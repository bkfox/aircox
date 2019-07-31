"""
Handle the audio streamer and controls it as we want it to be. It is
used to:
- generate config files and playlists;
- monitor Liquidsoap, logs and scheduled programs;
- cancels Diffusions that have an archive but could not have been played;
- run Liquidsoap
"""
from argparse import RawTextHelpFormatter
import time

import pytz
import tzlocal
from django.core.management.base import BaseCommand
from django.utils import timezone as tz

from aircox.models import Station, Episode, Diffusion, Track, Sound, Log
from aircox.controllers import Streamer, PlaylistSource

# force using UTC
tz.activate(pytz.UTC)


# FIXME liquidsoap does not manage timezones -- we have to convert
#       'on_air' metadata we get from it into utc one in order to work
#       correctly.
local_tz = tzlocal.get_localzone()


class Monitor:
    """
    Log and launch diffusions for the given station.

    Monitor should be able to be used after a crash a go back
    where it was playing, so we heavily use logs to be able to
    do that.

    We keep trace of played items on the generated stream:
    - sounds played on this stream;
    - scheduled diffusions
    - tracks for sounds of streamed programs
    """
    streamer = None
    """ Streamer controller """
    logs = None
    """ Queryset to station's logs (ordered by -pk) """
    cancel_timeout = 20
    """ Timeout in minutes before cancelling a diffusion. """
    sync_timeout = 5
    """ Timeout in minutes between two streamer's sync. """
    sync_next = None
    """ Datetime of the next sync """

    @property
    def station(self):
        return self.streamer.station

    @property
    def last_log(self):
        """ Last log of monitored station. """
        return self.logs.first()

    @property
    def last_diff_start(self):
        """ Log of last triggered item (sound or diffusion). """
        return self.logs.start().with_diff().first()

    def __init__(self, streamer, **kwargs):
        self.streamer = streamer
        self.__dict__.update(kwargs)
        self.logs = self.get_logs_queryset()

    def get_logs_queryset(self):
        """ Return queryset to assign as `self.logs` """
        return self.station.log_set.select_related('diffusion', 'sound') \
                           .order_by('-pk')

    def monitor(self):
        """ Run all monitoring functions once. """
        if not self.streamer.is_ready:
            return

        self.streamer.fetch()
        source = self.streamer.source
        if source and source.uri:
            log = self.trace_sound(source)
            if log:
                self.trace_tracks(log)
        else:
            print('no source or sound for stream; source = ', source)

        self.handle_diffusions()
        self.sync()

    def log(self, date=None, **kwargs):
        """ Create a log using **kwargs, and print info """
        kwargs.setdefault('station', self.station)
        log = Log(date=date or tz.now(), **kwargs)
        log.save()
        log.print()
        return log

    def trace_sound(self, source):
        """ Return on air sound log (create if not present). """
        sound_path, air_time = source.uri, source.air_time

        # check if there is yet a log for this sound on the source
        delta = tz.timedelta(seconds=5)
        air_times = (air_time - delta, air_time + delta)

        log = self.logs.on_air().filter(source=source.id,
                                        sound__path=sound_path,
                                        date__range=air_times).first()
        if log:
            return log

        # get sound
        diff = None
        sound = Sound.objects.filter(path=sound_path).first()
        if sound and sound.episode_id is not None:
            diff = Diffusion.objects.episode(id=sound.episode_id).on_air() \
                                    .now(air_time).first()

        # log sound on air
        return self.log(type=Log.Type.on_air, date=source.air_time,
                        source=source.id, sound=sound, diffusion=diff,
                        comment=sound_path)

    def trace_tracks(self, log):
        """
        Log tracks for the given sound log (for streamed programs only).
        """
        if log.diffusion:
            return

        tracks = Track.objects \
                      .filter(sound__id=log.sound_id, timestamp__isnull=False)\
                      .order_by('timestamp')
        if not tracks.exists():
            return

        # exclude already logged tracks
        tracks = tracks.exclude(log__station=self.station, log__pk__gt=log.pk)
        now = tz.now()
        for track in tracks:
            pos = log.date + tz.timedelta(seconds=track.timestamp)
            if pos > now:
                break
            # log track on air
            self.log(type=Log.Type.on_air, date=pos, source=log.source,
                     track=track, comment=track)

    def handle_diffusions(self):
        """
        Handle scheduled diffusion, trigger if needed, preload playlists
        and so on.
        """
        # TODO: restart
        # TODO: handle conflict + cancel
        diff = Diffusion.objects.station(self.station).on_air().now() \
                        .filter(episode__sound__type=Sound.Type.archive) \
                        .first()
        log = self.logs.start().filter(diffusion=diff) if diff else None
        if not diff or log:
            return

        playlist = Sound.objects.episode(id=diff.episode_id).paths()
        dealer = self.streamer.dealer
        dealer.queue(*playlist)
        self.log(type=Log.Type.start, source=dealer.id, diffusion=diff,
                 comment=str(diff))

    def sync(self):
        """ Update sources' playlists. """
        now = tz.now()
        if self.sync_next is not None and now < self.sync_next:
            return

        self.sync_next = now + tz.timedelta(minutes=self.sync_timeout)

        for source in self.streamer.sources:
            if isinstance(source, PlaylistSource):
                source.sync()


class Command (BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        group = parser.add_argument_group('actions')
        group.add_argument(
            '-c', '--config', action='store_true',
            help='generate configuration files for the stations'
        )
        group.add_argument(
            '-m', '--monitor', action='store_true',
            help='monitor the scheduled diffusions and log what happens'
        )
        group.add_argument(
            '-r', '--run', action='store_true',
            help='run the required applications for the stations'
        )

        group = parser.add_argument_group('options')
        group.add_argument(
            '-d', '--delay', type=int,
            default=1000,
            help='time to sleep in MILLISECONDS between two updates when we '
                 'monitor'
        )
        group.add_argument(
            '-s', '--station', type=str, action='append',
            help='name of the station to monitor instead of monitoring '
                 'all stations'
        )
        group.add_argument(
            '-t', '--timeout', type=int,
            default=Monitor.cancel_timeout,
            help='time to wait in MINUTES before canceling a diffusion that '
                 'should have ran but did not. '
        )
        # TODO: sync-timeout, cancel-timeout

    def handle(self, *args,
               config=None, run=None, monitor=None,
               station=[], delay=1000, timeout=600,
               **options):

        stations = Station.objects.filter(name__in=station) if station else \
                   Station.objects.all()
        streamers = [Streamer(station) for station in stations]

        for streamer in streamers:
            if config:
                streamer.make_config()
            if run:
                streamer.run_process()

        if monitor:
            monitors = [Monitor(streamer, cancel_timeout=timeout)
                        for streamer in streamers]

            delay = delay / 1000
            while True:
                for monitor in monitors:
                    monitor.monitor()
                time.sleep(delay)

        if run:
            for streamer in streamers:
                streamer.wait_process()

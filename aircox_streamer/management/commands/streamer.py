"""
Handle the audio streamer and controls it as we want it to be. It is
used to:
- generate config files and playlists;
- monitor Liquidsoap, logs and scheduled programs;
- cancels Diffusions that have an archive but could not have been played;
- run Liquidsoap
"""
# TODO:
# x controllers: remaining
# x diffusion conflicts
# x cancel
# x when liquidsoap fails to start/exists: exit
# - handle restart after failure
# - is stream restart after live ok?
from argparse import RawTextHelpFormatter
import time

import pytz
from django.db.models import Q
from django.core.management.base import BaseCommand
from django.utils import timezone as tz

from aircox.models import Station, Episode, Diffusion, Track, Sound, Log
from aircox.utils import date_range

from aircox_streamer.liquidsoap import Streamer, PlaylistSource


# force using UTC
tz.activate(pytz.UTC)


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
    delay = None
    """ Timedelta: minimal delay between two call of monitor. """
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

    def __init__(self, streamer, delay, cancel_timeout, **kwargs):
        self.streamer = streamer
        # adding time ensure all calculation have a margin
        self.delay = delay + tz.timedelta(seconds=5)
        self.cancel_timeout = cancel_timeout
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

        # Skip tracing - analyzis:
        # Reason: multiple database request every x seconds, reducing it.
        # We could skip this part when remaining time is higher than a minimal
        # value (which should be derived from Command's delay). Problems:
        # - How to trace tracks? (+ Source can change: caching log might sucks)
        # - if liquidsoap's source/request changes: remaining time goes higher,
        #   thus avoiding fetch
        #
        # Approach: something like having a mean time, such as:
        #
        # ```
        # source = stream.source
        # mean_time = source.air_time
        #           + min(next_track.timestamp, source.remaining)
        #           - (command.delay + 1)
        # trace_required = \/ source' != source
        #                  \/ source.uri' != source.uri
        #                  \/ now < mean_time
        # ```
        #
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
        air_uri, air_time = source.uri, source.air_time

        # check if there is yet a log for this sound on the source
        log = self.logs.on_air().filter(
            Q(sound__path=air_uri) |
            # sound can be null when arbitrary sound file is played
            Q(sound__isnull=True, track__isnull=True, comment=air_uri),
            source=source.id,
            date__range=date_range(air_time, self.delay),
        ).first()
        if log:
            return log

        # get sound
        diff = None
        sound = Sound.objects.filter(path=air_uri).first()
        if sound and sound.episode_id is not None:
            diff = Diffusion.objects.episode(id=sound.episode_id).on_air() \
                                    .now(air_time).first()

        # log sound on air
        return self.log(type=Log.TYPE_ON_AIR, date=source.air_time,
                        source=source.id, sound=sound, diffusion=diff,
                        comment=air_uri)

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
            self.log(type=Log.TYPE_ON_AIR, date=pos, source=log.source,
                     track=track, comment=track)

    def handle_diffusions(self):
        """
        Handle scheduled diffusion, trigger if needed, preload playlists
        and so on.
        """
        # TODO: program restart

        # Diffusion conflicts are handled by the way a diffusion is defined
        # as candidate for the next dealer's start.
        #
        # ```
        # logged_diff: /\ \A diff in diffs: \E log: /\ log.type = START
        #                                           /\ log.diff = diff
        #                                           /\ log.date = diff.start
        # queue_empty: /\ dealer.queue is empty
        #              /\ \/ ~dealer.on_air
        #                 \/ dealer.remaining < delay
        #
        # start_allowed: /\ diff not in logged_diff
        #                /\ queue_empty
        #
        # start_canceled: /\ diff not in logged diff
        #                 /\ ~queue_empty
        #                 /\ diff.start < now + cancel_timeout
        # ```
        #
        now = tz.now()
        diff = Diffusion.objects.station(self.station).on_air().now(now) \
                        .filter(episode__sound__type=Sound.TYPE_ARCHIVE) \
                        .first()
        # Can't use delay: diffusion may start later than its assigned start.
        log = None if not diff else self.logs.start().filter(diffusion=diff)
        if not diff or log:
            return

        dealer = self.streamer.dealer
        # start
        if not dealer.queue and dealer.rid is None or \
                dealer.remaining < self.delay.total_seconds():
            self.start_diff(dealer, diff)

        # cancel
        if diff.start < now - self.cancel_timeout:
            self.cancel_diff(dealer, diff)

    def start_diff(self, source, diff):
        playlist = Sound.objects.episode(id=diff.episode_id).paths()
        source.push(*playlist)
        self.log(type=Log.TYPE_START, source=source.id, diffusion=diff,
                 comment=str(diff))

    def cancel_diff(self, source, diff):
        diff.type = Diffusion.TYPE_CANCEL
        diff.save()
        self.log(type=Log.TYPE_CANCEL, source=source.id, diffusion=diff,
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
                 'monitor. This influence the delay before a diffusion is '
                 'launched.'
        )
        group.add_argument(
            '-s', '--station', type=str, action='append',
            help='name of the station to monitor instead of monitoring '
                 'all stations'
        )
        group.add_argument(
            '-t', '--timeout', type=float,
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
            delay = tz.timedelta(milliseconds=delay)
            timeout = tz.timedelta(minutes=timeout)
            monitors = [Monitor(streamer, delay, timeout)
                        for streamer in streamers]

            while not run or streamer.is_running:
                for monitor in monitors:
                    monitor.monitor()
                time.sleep(delay.total_seconds())

        if run:
            for streamer in streamers:
                streamer.wait_process()

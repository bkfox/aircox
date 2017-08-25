"""
Handle the audio streamer and controls it as we want it to be. It is
used to:
- generate config files and playlists;
- monitor Liquidsoap, logs and scheduled programs;
- cancels Diffusions that have an archive but could not have been played;
- run Liquidsoap
"""
import time
import re

from argparse import RawTextHelpFormatter

from django.conf import settings as main_settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz
from django.utils.functional import cached_property
from django.db import models

from aircox.models import Station, Diffusion, Track, Sound, Log #, DiffusionLog, SoundLog

# force using UTC
import pytz
tz.activate(pytz.UTC)


class Tracer:
    """
    Keep trace of played item and update logs in adequation to it
    """
    pass


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
    station = None
    streamer = None
    cancel_timeout = 60*10
    """
    Time in seconds before a diffusion that have archives is cancelled
    because it has not been played.
    """
    sync_timeout = 60*10
    """
    Time in minuts before all stream playlists are checked and updated
    """
    sync_next = None
    """
    Datetime of the next sync
    """


    def get_last_log(self, *args, **kwargs):
        return Log.objects.station(self.station, *args, **kwargs) \
                  .select_related('diffusion', 'sound') \
                  .order_by('date').last()

    @property
    def last_log(self):
        """
        Last log of monitored station
        """
        return self.get_last_log()

    @property
    def last_sound(self):
        """
        Last sound log of monitored station that occurred on_air
        """
        return self.get_last_log(type = Log.Type.on_air,
                                 sound__isnull = False)

    @property
    def last_diff_start(self):
        """
        Log of last triggered item (sound or diffusion)
        """
        return self.get_last_log(type = Log.Type.start,
                                 diffusion__isnull = False)


    def __init__(self, station, **kwargs):
        self.station = station
        self.__dict__.update(kwargs)

        now = tz.now()

    def monitor(self):
        """
        Run all monitoring functions.
        """
        if not self.streamer:
            self.streamer = self.station.streamer

        if not self.streamer.ready():
            return

        self.trace()
        self.sync_playlists()
        self.handle()

    def log(self, date = None, **kwargs):
        """
        Create a log using **kwargs, and print info
        """
        log = Log(station = self.station, date = date or tz.now(),
                  **kwargs)
        log.save()
        log.print()

        # update last log
        if log.type != Log.Type.other and \
                self.last_log and not self.last_log.end:
            self.last_log.end = log.date
        return log

    def trace(self):
        """
        Check the current_sound of the station and update logs if
        needed.
        """
        self.streamer.fetch()
        current_sound = self.streamer.current_sound
        current_source = self.streamer.current_source
        if not current_sound or not current_source:
            print('no source / no sound', current_sound, current_source)
            return

        log = self.get_last_log(models.Q(diffusion__isnull = False) |
                                models.Q(sound__isnull = False))

        if log:
            # check if sound on air changed compared to logged one
            try:
                # FIXME: TO-check liquidsoap ensure we have utc time
                on_air = current_source.metadata and \
                            current_source.metadata.get('on_air')
                on_air = tz.datetime.strptime(on_air, "%Y/%m/%d %H:%M:%S")
                on_air = tz.make_aware(on_air)

                is_diff = log.date != on_air
            except:
                on_air = None
                is_diff = log.source != current_source.id or \
                            (log.sound and log.sound.path != current_sound)
        else:
            # no log: sound is different
            is_diff = True

        if is_diff:
            sound = Sound.objects.filter(path = current_sound).first()

            # find an eventual diffusion associated to current sound
            # => check using last (started) diffusion's archives
            last_diff = self.last_diff_start
            diff = None
            if last_diff and not last_diff.is_expired():
                archives = last_diff.diffusion.get_archives()
                if archives.filter(pk = sound.pk).exists():
                    diff = last_diff.diffusion

            # log sound on air
            log = self.log(
                type = Log.Type.on_air,
                source = current_source.id,
                date = on_air or tz.now(),
                sound = sound,
                diffusion = diff,
                # if sound is removed, we keep sound path info
                comment = current_sound,
            )

        # tracks -- only for streams
        if not log.diffusion:
            self.trace_sound_tracks(log)


    def trace_sound_tracks(self, log):
        """
        Log tracks for the given sound log (for streamed programs).
        Called by self.trace
        """
        tracks = Track.objects.get_for(object = log.sound) \
                              .filter(in_seconds = True)
        if not tracks.exists():
            return

        tracks = tracks.exclude(log__station = self.station,
                                log__pk__gt = log.pk)
        now = tz.now()
        for track in tracks:
            pos = log.date + tz.timedelta(seconds = track.position)
            if pos > now:
                break
            # log track on air
            self.log(
                type = Log.Type.on_air, source = log.source,
                date = pos, track = track,
                comment = track,
            )

    def sync_playlists(self):
        """
        Synchronize updated playlists
        """
        now = tz.now()
        if self.sync_next and self.sync_next < now:
            return

        self.sync_next = now + tz.timedelta(seconds = self.sync_timeout)

        for source in self.station.sources:
            if source == self.station.dealer:
                continue
            playlist = source.program.sound_set.all() \
                             .values_list('path', flat = True)
            source.playlist = list(playlist)

    def trace_canceled(self):
        """
        Check diffusions that should have been played but did not start,
        and cancel them
        """
        if not self.cancel_timeout:
            return

        diffs = Diffusions.objects.at(self.station).filter(
            type = Diffusion.Type.normal,
            sound__type = Sound.Type.archive,
        )
        logs = station.raw_on_air(diffusion__isnull = False)

        date = tz.now() - datetime.timedelta(seconds = self.cancel_timeout)
        for diff in diffs:
            if logs.filter(diffusion = diff):
                continue
            if diff.start < now:
                diff.type = Diffusion.Type.canceled
                diff.save()
                # log canceled diffusion
                self.log(
                    type = Log.Type.other,
                    diffusion = diff,
                    comment = 'Diffusion canceled after {} seconds' \
                              .format(self.cancel_timeout)
                )

    def __current_diff(self):
        """
        Return a tuple with the currently running diffusion and the items
        that still have to be played. If there is not, return None
        """
        station = self.station
        now = tz.now()

        log = station.raw_on_air(diffusion__isnull = False) \
                     .select_related('diffusion') \
                     .order_by('date').last()
        if not log or not log.diffusion.is_date_in_range(now):
            # not running anymore
            return None, []

        # last sound source change: end of file reached or forced to stop
        sounds = station.raw_on_air(sound__isnull = False) \
                        .filter(date__gte = log.date) \
                        .order_by('date')

        if sounds.count() and sounds.last().source != log.source:
            return None, []

        # last diff is still playing: get remaining playlist
        sounds = sounds \
            .filter(source = log.source, pk__gt = log.pk) \
            .exclude(sound__type = Sound.Type.removed)

        remaining = log.diffusion.get_archives().exclude(pk__in = sounds) \
                       .values_list('path', flat = True)
        return log.diffusion, list(remaining)

    def __next_diff(self, diff):
        """
        Return the next diffusion to be played as tuple of (diff, playlist).
        If diff is given, it is the one to be played right after it.
        """
        station = self.station
        now = tz.now()

        kwargs = {'start__gte': diff.end } if diff else {}
        diff = Diffusion.objects \
            .at(station, now) \
            .filter(type = Diffusion.Type.normal, **kwargs) \
            .distinct().order_by('start')
        diff = diff.first()
        return (diff, diff and diff.playlist or [])

    def handle_pl_sync(self, source, playlist, diff = None, date = None):
        """
        Update playlist of a source if required, and handle logging when
        it is needed.

        - source: source on which it happens
        - playlist: list of sounds to use to update
        - diff: related diffusion
        """
        if source.playlist == playlist:
            return

        source.playlist = playlist
        if diff and not diff.is_live():
            # log diffusion archive load
            self.log(type = Log.Type.load,
                     source = source.id,
                     diffusion = diff,
                     date = date,
                     comment = '\n'.join(playlist))

    def handle_diff_start(self, source, diff, date):
        """
        Enable dealer in order to play a given diffusion if required,
        handle start of diffusion
        """
        if not diff or diff.start > date:
            return

        # TODO: user has not yet put the diffusion sound when diff started
        #       => live logged; what we want: if user put a sound after it
        #       has been logged as live, load and start this sound

        # live: just log it
        if diff.is_live():
            diff_ = Log.objects.station(self.station) \
                       .filter(diffusion = diff, type = Log.Type.on_air)
            if not diff_.count():
                # log live diffusion
                self.log(type = Log.Type.on_air, source = source.id,
                         diffusion = diff, date = date)
            return

        # enable dealer
        if not source.active:
            source.active = True
            last_start = self.last_diff_start
            if not last_start or last_start.diffusion_id != diff.pk:
                # log triggered diffusion
                self.log(type = Log.Type.start, source = source.id,
                         diffusion = diff, date = date)

    def handle(self):
        """
        Handle scheduled diffusion, trigger if needed, preload playlists
        and so on.
        """
        station = self.station
        dealer = station.dealer
        if not dealer:
            return
        now = tz.now()

        # current and next diffs
        current_diff, remaining_pl = self.__current_diff()
        next_diff, next_pl = self.__next_diff(current_diff)

        # playlist
        dealer.active = bool(remaining_pl)
        playlist = remaining_pl + next_pl

        self.handle_pl_sync(dealer, playlist, next_diff, now)
        self.handle_diff_start(dealer, next_diff, now)


class Command (BaseCommand):
    help= __doc__

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
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
            default=600,
            help='time to wait in SECONDS before canceling a diffusion that '
                 'has not been ran but should have been. If 0, does not '
                 'check'
        )

    def handle (self, *args,
                config = None, run = None, monitor = None,
                station = [], delay = 1000, timeout = 600,
                **options):

        stations = Station.objects.filter(name__in = station)[:] \
                    if station else Station.objects.all()[:]

        for station in stations:
            # station.prepare()
            if config and not run: # no need to write it twice
                station.streamer.push()
            if run:
                station.streamer.process_run()

        if monitor:
            monitors = [
                Monitor(station, cancel_timeout = timeout)
                    for station in stations
            ]
            delay = delay / 1000
            while True:
                for monitor in monitors:
                    monitor.monitor()
                time.sleep(delay)

        if run:
            for station in stations:
                station.controller.process_wait()


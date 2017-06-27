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

from aircox.models import Station, Diffusion, Track, Sound, Log


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

    def __init__(self, station, **kwargs):
        self.station = station
        self.__dict__.update(kwargs)

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

    def trace(self):
        """
        Check the current_sound of the station and update logs if
        needed.
        """
        self.streamer.fetch()
        current_sound = self.streamer.current_sound
        current_source = self.streamer.current_source
        if not current_sound or not current_source:
            return

        log = Log.objects.get_for(self.station, model = Sound) \
                         .order_by('date').last()

        # only streamed
        if log and (log.related and not log.related.diffusion):
            self.trace_sound_tracks(log)

        # TODO: expiration
        if log and (log.source == current_source.id and \
                log.related and
                log.related.path == current_sound):
            return

        sound = Sound.objects.filter(path = current_sound)
        self.log(
            type = Log.Type.play,
            source = current_source.id,
            date = tz.now(),
            related = sound[0] if sound else None,
            # keep sound path (if sound is removed, we keep that info)
            comment = current_sound,
        )

    def trace_sound_tracks(self, log):
        """
        Log tracks for the given sound (for streamed programs); Called by
        self.trace
        """
        logs = Log.objects.get_for(self.station, model = Track) \
                          .filter(pk__gt = log.pk)
        logs = [ log.related_id for log in logs ]

        tracks = Track.objects.get_for(object = log.related) \
                              .filter(in_seconds = True)
        if tracks and len(tracks) == len(logs):
            return

        tracks = tracks.exclude(pk__in = logs).order_by('position')
        now = tz.now()
        for track in tracks:
            pos = log.date + tz.timedelta(seconds = track.position)
            if pos < now:
                self.log(
                    type = Log.Type.play,
                    source = log.source,
                    date = pos,
                    related = track,
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
            source.playlist = playlist

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
        logs = station.played(models = Diffusion)

        date = tz.now() - datetime.timedelta(seconds = self.cancel_timeout)
        for diff in diffs:
            if logs.filter(related = diff):
                continue
            if diff.start < now:
                diff.type = Diffusion.Type.canceled
                diff.save()
                self.log(
                    type = Log.Type.other,
                    related = diff,
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

        log = station.played(models = Diffusion).order_by('date').last()
        if not log or not log.related.is_date_in_range(now):
            # not running anymore
            return None, []

        # sound has switched? assume it has been (forced to) stopped
        sounds = station.played(models = Sound) \
                        .filter(date__gte = log.date) \
                        .order_by('date')

        # last sound source change: end of file reached
        if sounds.count() and sounds.last().source != log.source:
            # diffusion is finished: end of sound file reached
            return None, []

        # last diff is still playing: get remaining playlist
        sounds = sounds \
            .filter(source = log.source, pk__gt = diff_log.pk) \
            .exclude(related__type = Sound.Type.removed)
            .values_list('related__path', flat = True)
        remaining = log.related.get_archives().exclude(path__in = sounds)

        return log.related, remaining

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
            .filter(type = Diffusion.Type.normal,
                    sound_type = Sound.Type.archive, **kwargs) \
            .distinct().order_by('start').first()
        return diff

    def handle_pl_sync(self, source, playlist, diff = None, date = None):
        """
        Update playlist of a source if required, and handle logging when
        it is needed.
        """
        dealer = self.station.dealer
        if dealer.playlist != playlist:
            dealer.playlist = playlist
            if diff and not diff.is_live():
                self.log(type = Log.Type.load, source = source.id,
                         related = diff, date = date)

    def handle_diff_start(self, source, diff, date):
        """
        Enable dealer in order to play a given diffusion if required,
        handle start of diffusion
        """
        if not diff or not diff.start <= now:
            return

        # live: just log it
        if diff.is_live():
            if not Log.get_for(object = diff).count():
                self.log(type = Log.Type.live, source = source.id,
                         related = diff, date = date)
            return

        # enable dealer
        if not dealer.active:
            dealer.active = True
            self.log(type = Log.Type.play, source = source.id,
                     related = diff, date = date)

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
        current_diff, current_pl = self.__current_diff()
        next_diff, next_pl = self.__next_diff(diff)

        # playlist
        dealer.active = bool(current_pl)
        playlist = current_pl + next_pl

        self.handle_pl_sync(dealer, playlist, next_diff, now)
        self.handle_diff_start(dealer, next_diff)


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


"""
Handle the audio streamer and controls it as we want it to be. It is
used to:
- generate config files and playlists;
- monitor Liquidsoap, logs and scheduled programs;
- cancels Diffusions that have an archive but could not have been played;
- run Liquidsoap
"""
import os
import time
import re

from argparse import RawTextHelpFormatter

from django.conf import settings as main_settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz

from aircox.models import Station, Diffusion, Track, Sound, Log


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

    def log(self, **kwargs):
        """
        Create a log using **kwargs, and print info
        """
        log = Log(station = self.station, **kwargs)
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

        log = Log.objects.get_for(model = Sound) \
                         .filter(station = self.station) \
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
            comment = None if sound else current_sound,
        )

    def trace_sound_tracks(self, log):
        """
        Log tracks for the given sound (for streamed programs); Called by
        self.trace
        """
        logs = Log.objects.get_for(model = Track) \
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
                    related = track
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
            playlist = [ sound.path for sound in
                            source.program.sound_set.all() ]
            source.playlist = playlist

    def trace_canceled(self):
        """
        Check diffusions that should have been played but did not start,
        and cancel them
        """
        if not self.cancel_timeout:
            return

        diffs = Diffusions.objects.get_at().filter(
            type = Diffusion.Type.normal,
            sound__type = Sound.Type.archive,
        )
        logs = station.get_played(models = Diffusion)

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
        now = tz.make_aware(tz.datetime.now())

        diff_log = station.get_played(models = Diffusion) \
                          .order_by('date').last()
        if not diff_log or \
                not diff_log.related.is_date_in_range(now):
            return None, []

        # sound has switched? assume it has been (forced to) stopped
        sounds = station.get_played(models = Sound) \
                        .filter(date__gte = diff_log.date) \
                        .order_by('date')

        if sounds.last() and sounds.last().source != diff_log.source:
            return diff_log, []

        # last diff is still playing: get the remaining playlist
        sounds = sounds.filter(
            source = diff_log.source, pk__gt = diff_log.pk
        )
        sounds = [
            sound.related.path for sound in sounds
            if sound.related.type != Sound.Type.removed
        ]

        return (
            diff_log.related,
            [ path for path in diff_log.related.playlist
                if path not in sounds ]
        )

    def __next_diff(self, diff):
        """
        Return the tuple with the next diff that should be played and
        the playlist

        Note: diff is a log
        """
        station = self.station
        now = tz.now()

        args = {'start__gt': diff.date } if diff else {}
        diff = Diffusion.objects.get_at(now).filter(
            type = Diffusion.Type.normal,
            sound__type = Sound.Type.archive,
            **args
        ).distinct().order_by('start').first()
        return (diff, diff and diff.playlist or [])

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
        diff, playlist = self.__current_diff()
        dealer.active = bool(playlist)

        next_diff, next_playlist = self.__next_diff(diff)
        playlist += next_playlist

        # playlist update
        if dealer.playlist != playlist:
            dealer.playlist = playlist
            if next_diff:
                self.log(
                    type = Log.Type.load,
                    source = dealer.id,
                    date = now,
                    related = next_diff
                )

        # dealer.on when next_diff start <= now
        if next_diff and not dealer.active and \
                next_diff.start <= now:
            dealer.active = True
            self.log(
                type = Log.Type.play,
                source = dealer.id,
                date = now,
                related = next_diff,
            )


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


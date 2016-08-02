import time

from django.utils import timezone as tz

import aircox.programs.models as programs
from aircox.controllers.models import Log

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
    controller = None
    cancel_timeout = 60*10
    """
    Time in seconds before a diffusion that have archives is cancelled
    because it has not been played.
    """

    def __init__(self, station, **kwargs):
        self.station = station
        self.__dict__.update(kwargs)

    def monitor(self):
        """
        Run all monitoring functions. Ensure that station has controllers
        """
        if not self.controller:
            self.station.prepare()
            for stream in self.station.stream_sources:
                stream.load_playlist()
        self.controller = self.station.controller

        if not self.controller.ready():
            return

        self.trace()
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
        self.controller.fetch()
        current_sound = self.controller.current_sound
        current_source = self.controller.current_source
        if not current_sound or not current_source:
            return

        log = Log.objects.get_for(model = programs.Sound) \
                    .filter(station = self.station).order_by('date').last()

        # only streamed
        if log and not log.related.diffusion:
            self.trace_sound_tracks(log)

        # TODO: expiration
        if log and (log.source == current_source.id_ and \
                    log.related.path == current_sound):
            return

        sound = programs.Sound.objects.filter(path = current_sound)
        self.log(
            type = Log.Type.play,
            source = current_source.id_,
            date = tz.now(),
            related = sound[0] if sound else None,
            comment = None if sound else current_sound,
        )

    def trace_sound_tracks(self, log):
        """
        Log tracks for the given sound (for streamed programs); Called by
        self.trace
        """
        logs = Log.objects.get_for(model = programs.Track) \
                  .filter(pk__gt = log.pk)
        logs = [ log.related_id for log in logs ]

        tracks = programs.Track.objects.get_for(object = log.related) \
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

    def trace_canceled(self):
        """
        Check diffusions that should have been played but did not start,
        and cancel them
        """
        if not self.cancel_timeout:
            return

        diffs = programs.objects.get_at().filter(
            type = programs.Diffusion.Type.normal,
            sound__type = programs.Sound.Type.archive,
        )
        logs = station.get_played(models = programs.Diffusion)

        date = tz.now() - datetime.timedelta(seconds = self.cancel_timeout)
        for diff in diffs:
            if logs.filter(related = diff):
                continue
            if diff.start < now:
                diff.type = programs.Diffusion.Type.canceled
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

        diff_log = station.get_played(models = programs.Diffusion) \
                          .order_by('date').last()
        if not diff_log or \
                not diff_log.related.is_date_in_range(now):
            return None, []

        # sound has switched? assume it has been (forced to) stopped
        sounds = station.get_played(models = programs.Sound) \
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
            if sound.related.type != programs.Sound.Type.removed
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
        diff = programs.Diffusion.objects.get_at(now).filter(
            type = programs.Diffusion.Type.normal,
            sound__type = programs.Sound.Type.archive,
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
        dealer.controller.active = bool(playlist)

        next_diff, next_playlist = self.__next_diff(diff)
        playlist += next_playlist

        # playlist update
        if dealer.controller.playlist != playlist:
            dealer.controller.playlist = playlist
            if next_diff:
                self.log(
                    type = Log.Type.load,
                    source = dealer.id_,
                    date = now,
                    related = next_diff
                )

        # dealer.on when next_diff start <= now
        if next_diff and not dealer.controller.active and \
                next_diff.start <= now:
            dealer.controller.active = True
            self.log(
                type = Log.Type.play,
                source = dealer.id_,
                date = now,
                related = next_diff,
            )



from django.utils import timezone as tz

import aircox.programs.models as programs
from aircox.controller.models import Log

class Monitor:
    """
    Log and launch diffusions for the given station.

    Monitor should be able to be used after a crash a go back
    where it was playing, so we heavily use logs to be able to
    do that.
    """
    station = None

    @staticmethod
    def log(**kwargs):
        """
        Create a log using **kwargs, and print info
        """
        log = programs.Log(station = self.station, **kwargs)
        log.save()
        log.print()

    def track(self):
        """
        Check the current_sound of the station and update logs if
        needed
        """
        station = self.station
        station.controller.fetch()

        current_sound = station.controller.current_sound
        current_source = station.controller.current_source
        if not current_sound:
            return

        log = Log.get_for(model = programs.Sound) \
                    .filter(station = station).order_by('date').last()
        # TODO: expiration
        if log and (log.source == current_source and \
                    log.related.path == current_sound):
            return

        sound = programs.Sound.object.filter(path = current_sound)
        self.log(
            type = Log.Type.play,
            source = current_source,
            date = tz.make_aware(tz.datetime.now()),

            related = sound[0] if sound else None,
            comment = None if sound else current_sound,
        )

    def __current_diff(self):
        """
        Return a tuple with the currently running diffusion and the items
        that still have to be played. If there is not, return None
        """
        station = self.station
        now = tz.make_aware(tz.datetime.now())

        sound_log = Log.get_for(model = programs.Sound) \
                        .filter(station = station).order_by('date').last()
        diff_log = Log.get_for(model = programs.Diffusion) \
                        .filter(station = station).order_by('date').last()

        if not sound_log or not diff_log or \
                sound_log.source != diff_log.source or \
                diff_log.related.is_date_in_my_range(now) :
            return None, []

        # last registered diff is still playing: update the playlist
        sounds = Log.get_for(model = programs.Sound) \
                    .filter(station = station, source = diff_log.source) \
                    .filter(pk__gt = diff.log.pk)
        sounds = [ sound.path for sound in sounds if not sound.removed ]

        return (
            diff_log.related,
            [ path for path in diff_log.related.playlist
                if path not in sounds ]
        )

    def __next_diff(self, diff):
        """
        Return the tuple with the next diff that should be played and
        the playlist
        """
        station = self.station
        now = tz.make_aware(tz.datetime.now())

        args = {'start__gt': diff.start } if diff else {}
        diff = programs.Diffusion.get(
            now, now = True,
            type = programs.Diffusion.Type.normal,
            sound__type = programs.Sound.Type.archive,
            sound__removed = False,
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
        now = tz.make_aware(tz.datetime.now())

        # current and next diffs
        diff, playlist = self.__current_diff()
        dealer.on = bool(playlist)

        next_diff, next_playlist = self.__next_diff()
        playlist += next_playlist

        # playlist update
        if dealer.playlist != playlist:
            dealer.playlist = playlist
            if next_diff:
                self.log(
                    type = Log.Type.load,
                    source = dealer.id,
                    date = now,
                    related_object = next_diff
                )

        # dealer.on when next_diff start <= now
        if next_diff and not dealer.on and next_diff.start <= now:
            dealer.on = True
            for source in station.get_sources():
                source.controller.skip()
            cl.log(
                type = Log.Type.play,
                source = dealer.id,
                date = now,
                related_object = next_diff,
            )


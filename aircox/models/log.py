from collections import deque
import logging
import os

from django.db import models
from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _


from aircox import settings
from .episode import Diffusion
from .sound import Sound, Track
from .station import Station


logger = logging.getLogger('aircox')


__all__ = ['Log', 'LogQuerySet']


class LogQuerySet(models.QuerySet):
    def station(self, station=None, id=None):
        return self.filter(station=station) if id is None else \
               self.filter(station_id=id)

    def today(self, date):
        return self.filter(date__date=date)

    def after(self, date):
        return self.filter(date__gte=date) \
            if isinstance(date, tz.datetime) else \
            self.filter(date__date__gte=date)

    def on_air(self):
        return self.filter(type=Log.TYPE_ON_AIR)

    def start(self):
        return self.filter(type=Log.TYPE_START)

    def with_diff(self, with_it=True):
        return self.filter(diffusion__isnull=not with_it)

    def with_sound(self, with_it=True):
        return self.filter(sound__isnull=not with_it)

    def with_track(self, with_it=True):
        return self.filter(track__isnull=not with_it)

    @staticmethod
    def _get_archive_path(station, date):
        # note: station name is not included in order to avoid problems
        #       of retrieving archive when it changes

        return os.path.join(
            settings.AIRCOX_LOGS_ARCHIVES_DIR,
            '{}_{}.log.gz'.format(date.strftime("%Y%m%d"), station.pk)
        )

    @staticmethod
    def _get_rel_objects(logs, type, attr):
        """
        From a list of dict representing logs, retrieve related objects
        of the given type.

        Example: _get_rel_objects([{..},..], Diffusion, 'diffusion')
        """
        attr_id = attr + '_id'

        return {
            rel.pk: rel

            for rel in type.objects.filter(
                pk__in=(
                    log[attr_id]

                    for log in logs if attr_id in log
                )
            )
        }

    def load_archive(self, station, date):
        """
        Return archived logs for a specific date as a list
        """
        import yaml
        import gzip

        path = self._get_archive_path(station, date)

        if not os.path.exists(path):
            return []

        with gzip.open(path, 'rb') as archive:
            data = archive.read()
            logs = yaml.load(data)

            # we need to preload diffusions, sounds and tracks
            rels = {
                'diffusion': self._get_rel_objects(logs, Diffusion, 'diffusion'),
                'sound': self._get_rel_objects(logs, Sound, 'sound'),
                'track': self._get_rel_objects(logs, Track, 'track'),
            }

            def rel_obj(log, attr):
                rel_id = log.get(attr + '_id')
                return rels[attr][rel_id] if rel_id else None

            return [
                Log(diffusion=rel_obj(log, 'diffusion'),
                    sound=rel_obj(log, 'sound'),
                    track=rel_obj(log, 'track'),
                    **log)

                for log in logs
            ]

    def make_archive(self, station, date, force=False, keep=False):
        """
        Archive logs of the given date. If the archive exists, it does
        not overwrite it except if "force" is given. In this case, the
        new elements will be appended to the existing archives.

        Return the number of archived logs, -1 if archive could not be
        created.
        """
        import yaml
        import gzip

        os.makedirs(settings.AIRCOX_LOGS_ARCHIVES_DIR, exist_ok=True)
        path = self._get_archive_path(station, date)

        if os.path.exists(path) and not force:
            return -1

        qs = self.station(station).today(date)

        if not qs.exists():
            return 0

        fields = Log._meta.get_fields()
        logs = [{i.attname: getattr(log, i.attname)
                 for i in fields} for log in qs]

        # Note: since we use Yaml, we can just append new logs when file
        # exists yet <3
        with gzip.open(path, 'ab') as archive:
            data = yaml.dump(logs).encode('utf8')
            archive.write(data)

        if not keep:
            qs.delete()

        return len(logs)


class Log(models.Model):
    """
    Log sounds and diffusions that are played on the station.

    This only remember what has been played on the outputs, not on each
    source; Source designate here which source is responsible of that.
    """

    TYPE_STOP = 0x00
    """ Source has been stopped, e.g. manually """
    # Rule: \/ diffusion != null \/ sound != null
    TYPE_START = 0x01
    """ Diffusion or sound has been request to be played. """
    TYPE_CANCEL = 0x02
    """ Diffusion has been canceled. """
    # Rule: \/ sound != null /\ track == null
    #       \/ sound == null /\ track != null
    #       \/ sound == null /\ track == null /\ comment = sound_path
    TYPE_ON_AIR = 0x03
    """ Sound or diffusion occured on air """
    TYPE_OTHER = 0x04
    """ Other log """
    TYPE_CHOICES = (
        (TYPE_STOP, _('stop')), (TYPE_START, _('start')),
        (TYPE_CANCEL, _('cancelled')), (TYPE_ON_AIR, _('on air')),
        (TYPE_OTHER, _('other'))
    )

    station = models.ForeignKey(
        Station, models.CASCADE,
        verbose_name=_('station'), help_text=_('related station'),
    )
    type = models.SmallIntegerField(_('type'), choices=TYPE_CHOICES)
    date = models.DateTimeField(_('date'), default=tz.now, db_index=True)
    source = models.CharField(
        # we use a CharField to avoid loosing logs information if the
        # source is removed
        max_length=64, blank=True, null=True,
        verbose_name=_('source'),
        help_text=_('identifier of the source related to this log'),
    )
    comment = models.CharField(
        max_length=512, blank=True, null=True,
        verbose_name=_('comment'),
    )
    sound = models.ForeignKey(
        Sound, models.SET_NULL,
        blank=True, null=True, db_index=True,
        verbose_name=_('Sound'),
    )
    track = models.ForeignKey(
        Track, models.SET_NULL,
        blank=True, null=True, db_index=True,
        verbose_name=_('Track'),
    )
    diffusion = models.ForeignKey(
        Diffusion, models.SET_NULL,
        blank=True, null=True, db_index=True,
        verbose_name=_('Diffusion'),
    )

    objects = LogQuerySet.as_manager()

    @property
    def related(self):
        return self.diffusion or self.sound or self.track

    @property
    def local_date(self):
        """
        Return a version of self.date that is localized to self.timezone;
        This is needed since datetime are stored as UTC date and we want
        to get it as local time.
        """
        return tz.localtime(self.date, tz.get_current_timezone())

    def __str__(self):
        return '#{} ({}, {}, {})'.format(
            self.pk, self.get_type_display(),
            self.source, self.local_date.strftime('%Y/%m/%d %H:%M%z'))

    @classmethod
    def __list_append(cls, object_list, items):
        object_list += [cls(obj) for obj in items]

    @classmethod
    def merge_diffusions(cls, logs, diffs, count=None):
        # TODO: limit count
        logs = list(logs.order_by('-date'))
        diffs = deque(diffs.on_air().before().order_by('-start'))
        object_list = []

        while True:
            if not len(diffs):
                object_list += logs
                break

            if not len(logs):
                object_list += diffs
                break

            diff = diffs.popleft()

            # - takes all logs after diff
            index = next((i for i, v in enumerate(logs)
                          if v.date <= diff.end), len(logs))
            if index is not None and index > 0:
                object_list += logs[:index]
                logs = logs[index:]

            # - last log while diff is running
            if logs[0].date > diff.start:
                object_list.append(logs[0])

            # - skips logs while diff is running
            index = next((i for i, v in enumerate(logs)
                         if v.date < diff.start), len(logs))
            if index is not None and index > 0:
                logs = logs[index:]

            # - add diff
            object_list.append(diff)

        return object_list


    def print(self):
        r = []
        if self.diffusion:
            r.append('diff: ' + str(self.diffusion_id))
        if self.sound:
            r.append('sound: ' + str(self.sound_id))
        if self.track:
            r.append('track: ' + str(self.track_id))
        logger.info('log %s: %s%s', str(self), self.comment or '',
                    ' (' + ', '.join(r) + ')' if r else '')


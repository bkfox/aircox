from enum import IntEnum
import logging
import os

from django.conf import settings as main_settings
from django.db import models
from django.db.models import Q
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from aircox import settings
from .program import Program
from .episode import Episode


logger = logging.getLogger('aircox')


__all__ = ['Sound', 'SoundQuerySet', 'Track']


class SoundQuerySet(models.QuerySet):
    def station(self, station=None, id=None):
        id = station.pk if id is None else id
        return self.filter(program__station__id=id)

    def episode(self, episode=None, id=None):
        id = episode.pk if id is None else id
        return self.filter(episode__id=id)

    def diffusion(self, diffusion=None, id=None):
        id = diffusion.pk if id is None else id
        return self.filter(episode__diffusion__id=id)

    def available(self):
        return self.exclude(type=Sound.TYPE_REMOVED)

    def public(self):
        """ Return sounds available as podcasts """
        return self.filter(is_public=True)

    def archive(self):
        """ Return sounds that are archives """
        return self.filter(type=Sound.TYPE_ARCHIVE)

    def paths(self, archive=True, order_by=True):
        """
        Return paths as a flat list (exclude sound without path).
        If `order_by` is True, order by path.
        """
        if archive:
            self = self.archive()
        if order_by:
            self = self.order_by('path')
        return self.filter(path__isnull=False).values_list('path', flat=True)

    def search(self, query):
        return self.filter(
            Q(name__icontains=query) | Q(path__icontains=query) |
            Q(program__title__icontains=query) |
            Q(episode__title__icontains=query)
        )


class Sound(models.Model):
    """
    A Sound is the representation of a sound file that can be either an excerpt
    or a complete archive of the related diffusion.
    """
    TYPE_OTHER = 0x00
    TYPE_ARCHIVE = 0x01
    TYPE_EXCERPT = 0x02
    TYPE_REMOVED = 0x03
    TYPE_CHOICES = (
        (TYPE_OTHER, _('other')), (TYPE_ARCHIVE, _('archive')),
        (TYPE_EXCERPT, _('excerpt')), (TYPE_REMOVED, _('removed'))
    )

    name = models.CharField(_('name'), max_length=64)
    program = models.ForeignKey(
        Program, models.CASCADE,
        verbose_name=_('program'),
        help_text=_('program related to it'),
    )
    episode = models.ForeignKey(
        Episode, models.SET_NULL, blank=True, null=True,
        verbose_name=_('episode'),
    )
    type = models.SmallIntegerField(_('type'), choices=TYPE_CHOICES)
    position = models.PositiveSmallIntegerField(
        _('order'), default=0, help_text=_('position in the playlist'),
    )
    # FIXME: url() does not use the same directory than here
    #        should we use FileField for more reliability?
    path = models.FilePathField(
        _('file'),
        path=settings.AIRCOX_PROGRAMS_DIR,
        match=r'(' + '|'.join(settings.AIRCOX_SOUND_FILE_EXT)
        .replace('.', r'\.') + ')$',
        recursive=True, max_length=255,
        blank=True, null=True, unique=True,
    )
    #embed = models.TextField(
    #    _('embed'),
    #    blank=True, null=True,
    #    help_text=_('HTML code to embed a sound from an external plateform'),
    #)
    duration = models.TimeField(
        _('duration'),
        blank=True, null=True,
        help_text=_('duration of the sound'),
    )
    mtime = models.DateTimeField(
        _('modification time'),
        blank=True, null=True,
        help_text=_('last modification date and time'),
    )
    is_good_quality = models.BooleanField(
        _('good quality'), help_text=_('sound meets quality requirements'),
        blank=True, null=True
    )
    is_public = models.BooleanField(
        _('public'), help_text=_('if it can be podcasted from the server'),
        default=False,
    )

    objects = SoundQuerySet.as_manager()

    class Meta:
        verbose_name = _('Sound')
        verbose_name_plural = _('Sounds')

    def __str__(self):
        return '/'.join(self.path.split('/')[-3:])

    def save(self, check=True, *args, **kwargs):
        if self.episode is not None and self.program is None:
            self.program = self.episode.program
        if check:
            self.check_on_file()
        self.__check_name()
        super().save(*args, **kwargs)

    def get_mtime(self):
        """
        Get the last modification date from file
        """
        mtime = os.stat(self.path).st_mtime
        mtime = tz.datetime.fromtimestamp(mtime)
        # db does not store microseconds
        mtime = mtime.replace(microsecond=0)

        return tz.make_aware(mtime, tz.get_current_timezone())

    def url(self):
        """ Return an url to the stream. """
        path = self.path.replace(main_settings.MEDIA_ROOT, '', 1)
        return main_settings.MEDIA_URL + '/' + path

    def file_exists(self):
        """ Return true if the file still exists. """

        return os.path.exists(self.path)

    def check_on_file(self):
        """
        Check sound file info again'st self, and update informations if
        needed (do not save). Return True if there was changes.
        """
        if not self.file_exists():
            if self.type == self.TYPE_REMOVED:
                return
            logger.info('sound %s: has been removed', self.path)
            self.type = self.TYPE_REMOVED

            return True

        # not anymore removed
        changed = False

        if self.type == self.TYPE_REMOVED and self.program:
            changed = True
            self.type = self.TYPE_ARCHIVE \
                if self.path.startswith(self.program.archives_path) else \
                self.TYPE_EXCERPT

        # check mtime -> reset quality if changed (assume file changed)
        mtime = self.get_mtime()

        if self.mtime != mtime:
            self.mtime = mtime
            self.is_good_quality = None
            logger.info('sound %s: m_time has changed. Reset quality info',
                        self.path)
            return True

        return changed

    def __check_name(self):
        if not self.name and self.path:
            # FIXME: later, remove date?
            self.name = os.path.basename(self.path)
            self.name = os.path.splitext(self.name)[0]
            self.name = self.name.replace('_', ' ')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__check_name()


class Track(models.Model):
    """
    Track of a playlist of an object. The position can either be expressed
    as the position in the playlist or as the moment in seconds it started.
    """
    episode = models.ForeignKey(
        Episode, models.CASCADE, blank=True, null=True,
        verbose_name=_('episode'),
    )
    sound = models.ForeignKey(
        Sound, models.CASCADE, blank=True, null=True,
        verbose_name=_('sound'),
    )
    position = models.PositiveSmallIntegerField(
        _('order'), default=0, help_text=_('position in the playlist'),
    )
    timestamp = models.PositiveSmallIntegerField(
        _('timestamp'),
        blank=True, null=True,
        help_text=_('position (in seconds)')
    )
    title = models.CharField(_('title'), max_length=128)
    artist = models.CharField(_('artist'), max_length=128)
    tags = TaggableManager(verbose_name=_('tags'), blank=True,)
    info = models.CharField(
        _('information'),
        max_length=128,
        blank=True, null=True,
        help_text=_('additional informations about this track, such as '
                    'the version, if is it a remix, features, etc.'),
    )

    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')
        ordering = ('position',)

    def __str__(self):
        return '{self.artist} -- {self.title} -- {self.position}'.format(
               self=self)

    def save(self, *args, **kwargs):
        if (self.sound is None and self.episode is None) or \
                (self.sound is not None and self.episode is not None):
            raise ValueError('sound XOR episode is required')
        super().save(*args, **kwargs)



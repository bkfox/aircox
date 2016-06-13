import os
import shutil
import logging
from enum import Enum, IntEnum

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.html import strip_tags
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings as main_settings

from taggit.managers import TaggableManager

import aircox.programs.utils as utils
import aircox.programs.settings as settings


logger = logging.getLogger('aircox.core')


def date_or_default(date, date_only = False):
    """
    Return date or default value (now) if not defined, and remove time info
    if date_only is True
    """
    date = date or tz.datetime.today()
    if not tz.is_aware(date):
        date = tz.make_aware(date)
    if date_only:
        return date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    return date


class Nameable(models.Model):
    name = models.CharField (
        _('name'),
        max_length = 128,
    )

    @property
    def slug(self):
        """
        Slug based on the name. We replace '-' by '_'
        """
        return slugify(self.name).replace('-', '_')

    def __str__(self):
        #if self.pk:
        #    return '#{} {}'.format(self.pk, self.name)
        return '{}'.format(self.name)

    class Meta:
        abstract = True


class Track(Nameable):
    """
    Track of a playlist of a diffusion. The position can either be expressed
    as the position in the playlist or as the moment in seconds it started.
    """
    # There are no nice solution for M2M relations ship (even without
    # through) in django-admin. So we unfortunately need to make one-
    # to-one relations and add a position argument
    diffusion = models.ForeignKey(
        'Diffusion',
    )
    artist = models.CharField(
        _('artist'),
        max_length = 128,
    )
    # position can be used to specify a position in seconds for non-
    # stop programs or a position in the playlist
    position = models.SmallIntegerField(
        default = 0,
        help_text=_('position in the playlist'),
    )
    tags = TaggableManager(
        verbose_name=_('tags'),
        blank=True,
    )

    def __str__(self):
        return ' '.join([self.artist, ':', self.name ])

    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')


class Sound(Nameable):
    """
    A Sound is the representation of a sound file that can be either an excerpt
    or a complete archive of the related diffusion.

    The podcasting and public access permissions of a Sound are managed through
    the related program info.
    """
    class Type(IntEnum):
        other = 0x00,
        archive = 0x01,
        excerpt = 0x02,

    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (int(y), _(x)) for x,y in Type.__members__.items() ],
        blank = True, null = True
    )
    path = models.FilePathField(
        _('file'),
        path = settings.AIRCOX_PROGRAMS_DIR,
        match = r'(' + '|'.join(settings.AIRCOX_SOUND_FILE_EXT) \
                                    .replace('.', r'\.') + ')$',
        recursive = True,
        blank = True, null = True,
        max_length = 256
    )
    embed = models.TextField(
        _('embed HTML code'),
        blank = True, null = True,
        help_text = _('HTML code used to embed a sound from external plateform'),
    )
    duration = models.TimeField(
        _('duration'),
        blank = True, null = True,
        help_text = _('duration of the sound'),
    )
    mtime = models.DateTimeField(
        _('modification time'),
        blank = True, null = True,
        help_text = _('last modification date and time'),
    )
    removed = models.BooleanField(
        _('removed'),
        default = False,
        help_text = _('this sound has been removed from filesystem'),
    )
    good_quality = models.BooleanField(
        _('good quality'),
        default = False,
        help_text = _('sound\'s quality is okay')
    )

    def get_mtime(self):
        """
        Get the last modification date from file
        """
        mtime = os.stat(self.path).st_mtime
        mtime = tz.datetime.fromtimestamp(mtime)
        # db does not store microseconds
        mtime = mtime.replace(microsecond = 0)
        return tz.make_aware(mtime, tz.get_current_timezone())

    def url(self):
        """
        Return an url to the stream
        """
        # path = self._meta.get_field('path').path
        path = self.path.replace(main_settings.MEDIA_ROOT, '', 1)
        #path = self.path.replace(path, '', 1)
        # print(path, self._meta.get_field('path').path)
        return path

    def file_exists(self):
        """
        Return true if the file still exists
        """
        return os.path.exists(self.path)

    def check_on_file(self):
        """
        Check sound file info again'st self, and update informations if
        needed (do not save). Return True if there was changes.
        """
        if not self.file_exists():
            if self.removed:
                return
            logger.info('sound %s: has been removed', self.path)
            self.removed = True
            return True

        old_removed = self.removed
        self.removed = False

        mtime = self.get_mtime()
        if self.mtime != mtime:
            self.mtime = mtime
            self.good_quality = False
            logger.info('sound %s: m_time has changed. Reset quality info',
                        self.path)
            return True
        return old_removed != self.removed

    def save(self, check = True, *args, **kwargs):
        if check:
            self.check_on_file()

        if not self.name and self.path:
            self.name = os.path.basename(self.path)
            self.name = os.path.splitext(self.name)[0]
            self.name = self.name.replace('_', ' ')
        super().save(*args, **kwargs)

    def __str__(self):
        return '/'.join(self.path.split('/')[-3:])

    class Meta:
        verbose_name = _('Sound')
        verbose_name_plural = _('Sounds')


class Stream(models.Model):
    """
    When there are no program scheduled, it is possible to play sounds
    in order to avoid blanks. A Stream is a Program that plays this role,
    and whose linked to a Stream.

    All sounds that are marked as good and that are under the related
    program's archive dir are elligible for the sound's selection.
    """
    program = models.ForeignKey(
        'Program',
        verbose_name = _('related program'),
    )
    delay = models.TimeField(
        _('delay'),
        blank = True, null = True,
        help_text = _('delay between two sound plays')
    )
    begin = models.TimeField(
        _('begin'),
        blank = True, null = True,
        help_text = _('used to define a time range this stream is'
                      'played')
    )
    end = models.TimeField(
        _('end'),
        blank = True, null = True,
        help_text = _('used to define a time range this stream is'
                      'played')
    )


class Schedule(models.Model):
    """
    A Schedule defines time slots of programs' diffusions. It can be an initial
    run or a rerun (in such case it is linked to the related schedule).
    """
    # Frequency for schedules. Basically, it is a mask of bits where each bit is
    # a week. Bits > rank 5 are used for special schedules.
    # Important: the first week is always the first week where the weekday of
    # the schedule is present.
    # For ponctual programs, there is no need for a schedule, only a diffusion
    Frequency = {
        'first':            (0b000001, _('first week of the month')),
        'second':           (0b000010, _('second week of the month')),
        'third':            (0b000100, _('third week of the month')),
        'fourth':           (0b001000, _('fourth week of the month')),
        'last':             (0b010000, _('last week of the month')),
        'first and third':  (0b000101, _('first and third weeks of the month')),
        'second and fourth': (0b001010, _('second and fourth weeks of the month')),
        'every':            (0b011111, _('every week')),
        'one on two':       (0b100000, _('one week on two')),
    }
    VerboseFrequency = { value[0]: value[1] for key, value in Frequency.items() }
    Frequency = { key: value[0] for key, value in Frequency.items() }

    program = models.ForeignKey(
        'Program',
        verbose_name = _('related program'),
    )
    date = models.DateTimeField(_('date'))
    duration = models.TimeField(
        _('duration'),
        help_text = _('regular duration'),
    )
    frequency = models.SmallIntegerField(
        _('frequency'),
        choices = VerboseFrequency.items(),
    )
    initial = models.ForeignKey(
        'self',
        verbose_name = _('initial'),
        blank = True, null = True,
        help_text = 'this schedule is a rerun of this one',
    )

    def match(self, date = None, check_time = True):
        """
        Return True if the given datetime matches the schedule
        """
        date = date_or_default(date)

        if self.date.weekday() == date.weekday() and self.match_week(date):
            return self.date.time() == date.time() if check_time else True
        return False

    def match_week(self, date = None):
        """
        Return True if the given week number matches the schedule, False
        otherwise.
        If the schedule is ponctual, return None.
        """
        # FIXME: does not work if first_day > date_day
        date = date_or_default(date)
        if self.frequency == Schedule.Frequency['one on two']:
            week = date.isocalendar()[1]
            return (week % 2) == (self.date.isocalendar()[1] % 2)

        first_of_month = date.replace(day = 1)
        week = date.isocalendar()[1] - first_of_month.isocalendar()[1]

        # weeks of month
        if week == 4:
            # fifth week: return if for every week
            return self.frequency == 0b1111
        return (self.frequency & (0b0001 << week) > 0)

    def normalize(self, date):
        """
        Set the time of a datetime to the schedule's one
        """
        return date.replace(hour = self.date.hour, minute = self.date.minute)

    def dates_of_month(self, date = None):
        """
        Return a list with all matching dates of date.month (=today)
        """
        date = date_or_default(date, True).replace(day=1)
        freq = self.frequency

        # move to the first day of the month that matches the schedule's weekday
        # check on SO#3284452 for the formula
        first_weekday = date.weekday()
        sched_weekday = self.date.weekday()
        date += tz.timedelta(days = (7 if first_weekday > sched_weekday else 0) \
                                    - first_weekday + sched_weekday)
        month = date.month

        # last of the month
        if freq == Schedule.Frequency['last']:
            date += tz.timedelta(days = 4 * 7)
            next_date = date + tz.timedelta(days = 7)
            if next_date.month == month:
                date = next_date
            return [self.normalize(date)]

        dates = []
        if freq == Schedule.Frequency['one on two']:
            # NOTE previous algorithm was based on the week number, but this
            # approach is wrong because number of weeks in a year can be
            # 52 or 53. This also clashes with the first week of the year.
            if not (date - self.date).days % 14:
                date += tz.timedelta(days = 7)

            while date.month == month:
                dates.append(date)
                date += tz.timedelta(days = 14)
        else:
            week = 0
            while week < 5 and date.month == month:
                if freq & (0b1 << week):
                    dates.append(date)
                date += tz.timedelta(days = 7)
        return [self.normalize(date) for date in dates]

    def diffusions_of_month(self, date, exclude_saved = False):
        """
        Return a list of Diffusion instances, from month of the given date, that
        can be not in the database.

        If exclude_saved, exclude all diffusions that are yet in the database.
        """
        dates = self.dates_of_month(date)
        saved = Diffusion.objects.filter(start__in = dates,
                                         program = self.program)
        diffusions = []

        duration = utils.to_timedelta(self.duration)

        # existing diffusions
        for item in saved:
            if item.start in dates:
                dates.remove(item.start)
            if not exclude_saved:
                diffusions.append(item)

        # others
        for date in dates:
            first_date = date
            if self.initial:
                first_date -= self.date - self.initial.date

            first_diffusion = Diffusion.objects.filter(start = first_date,
                                                       program = self.program)
            first_diffusion = first_diffusion[0] if first_diffusion.count() \
                              else None
            diffusions.append(Diffusion(
                                 program = self.program,
                                 type = Diffusion.Type.unconfirmed,
                                 initial = first_diffusion if self.initial else None,
                                 start = date,
                                 end = date + duration,
                             ))
        return diffusions

    def __str__(self):
        return ' | '.join([ '#' + str(self.id), self.program.name,
                            self.get_frequency_display(),
                            self.date.strftime('%a %H:%M') ])

    def save(self, *args, **kwargs):
        if self.initial:
            self.program = self.initial.program
            self.duration = self.initial.duration
            self.frequency = self.initial.frequency
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class Program(Nameable):
    """
    A Program can either be a Streamed or a Scheduled program.

    A Streamed program is used to generate non-stop random playlists when there
    is not scheduled diffusion. In such a case, a Stream is used to describe
    diffusion informations.

    A Scheduled program has a schedule and is the one with a normal use case.

    Renaming a Program rename the corresponding directory to matches the new
    name if it does not exists.
    """
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('if not set this program is no longer active')
    )
    public = models.BooleanField(
        _('public'),
        default = True,
        help_text = _('information are available to the public')
    )

    @property
    def path(self):
        """
        Return the path to the programs directory
        """
        return os.path.join(settings.AIRCOX_PROGRAMS_DIR,
                            self.slug + '_' + str(self.id) )

    def ensure_dir(self, subdir = None):
        """
        Make sur the program's dir exists (and optionally subdir). Return True
        if the dir (or subdir) exists.
        """
        path = os.path.join(self.path, subdir) if subdir else \
               self.path
        os.makedirs(path, exist_ok = True)
        return os.path.exists(path)

    def find_schedule(self, date):
        """
        Return the first schedule that matches a given date.
        """
        schedules = Schedule.objects.filter(program = self)
        for schedule in schedules:
            if schedule.match(date, check_time = False):
                return schedule

    def __init__(self, *kargs, **kwargs):
        super().__init__(*kargs, **kwargs)
        if self.name:
            self.__original_path = self.path

    def save(self, *kargs, **kwargs):
        super().save(*kargs, **kwargs)
        if hasattr(self, '__original_path') and \
                self.__original_path != self.path and \
                os.path.exists(self.__original_path) and \
                not os.path.exists(self.path):
            logger.info('program #%s\'s name changed to %s. Change dir name',
                        self.id, self.name)
            shutil.move(self.__original_path, self.path)

            sounds = Sounds.objects.filter(path__startswith = self.__original_path)
            for sound in sounds:
                sound.path.replace(self.__original_path, self.path)
                sound.save()

    @classmethod
    def get_from_path(cl, path):
        """
        Return a Program from the given path. We assume the path has been
        given in a previous time by this model (Program.path getter).
        """
        path = path.replace(settings.AIRCOX_PROGRAMS_DIR, '')
        while path[0] == '/': path = path[1:]
        while path[-1] == '/': path = path[:-2]
        if '/' in path:
            path = path[:path.index('/')]

        path = path.split('_')
        path = path[-1]
        qs = cl.objects.filter(id = int(path))
        return qs[0] if qs else None


class Diffusion(models.Model):
    """
    A Diffusion is an occurrence of a Program that is scheduled on the
    station's timetable. It can be a rerun of a previous diffusion. In such
    a case, use rerun's info instead of its own.

    A Diffusion without any rerun is named Episode (previously, a
    Diffusion was different from an Episode, but in the end, an
    episode only has a name, a linked program, and a list of sounds, so we
    finally merge theme).

    A Diffusion can have different types:
    - default: simple diffusion that is planified / did occurred
    - unconfirmed: a generated diffusion that has not been confirmed and thus
        is not yet planified
    - cancel: the diffusion has been canceled
    - stop: the diffusion has been manually stopped
    """
    class Type(IntEnum):
        normal = 0x00
        unconfirmed = 0x01
        canceled = 0x02

    # common
    program = models.ForeignKey (
        'Program',
        verbose_name = _('program'),
    )
    sounds = models.ManyToManyField(
        Sound,
        blank = True,
        verbose_name = _('sounds'),
    )
    # specific
    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (int(y), _(x)) for x,y in Type.__members__.items() ],
    )
    initial = models.ForeignKey (
        'self',
        verbose_name = _('initial'),
        blank = True, null = True,
        help_text = _('the diffusion is a rerun of this one')
    )
    start = models.DateTimeField( _('start of the diffusion') )
    end = models.DateTimeField( _('end of the diffusion') )

    @property
    def duration(self):
        return self.end - self.start

    @property
    def date(self):
        return self.start

    @property
    def playlist(self):
        """
        List of sounds as playlist
        """
        playlist = [ sound.path for sound in self.sounds.all() ]
        playlist.sort()
        return playlist

    def archives_duration(self):
        """
        Get total duration of the archives. May differ from the schedule
        duration.
        """
        sounds = self.initial.sounds if self.initial else self.sounds
        r = [ sound.duration
                for sound in sounds.filter(type = Sound.Type.archive)
                if sound.duration ]
        return utils.time_sum(r)

    def get_archives(self):
        """
        Return an ordered list of archives sounds for the given episode.
        """
        sounds = self.initial.sounds if self.initial else self.sounds
        r = [ sound for sound in sounds.all().order_by('path')
              if sound.type == Sound.Type.archive ]
        return r

    @classmethod
    def get(cl, date = None,
             now = False, next = False, prev = False,
             queryset = None,
             **filter_args):
        """
        Return a queryset of diffusions, depending on value of now/next/prev
        - now: that have date in their start-end range or start after
        - next: that start after date
        - prev: that end before date

        If queryset is not given, use self.objects.all

        Diffusions are ordered by +start for now and next; -start for prev
        """
        #FIXME: conflicts? ( + calling functions)
        date = date_or_default(date)
        if queryset is None:
            queryset = cl.objects

        if now:
            return queryset.filter(
                models.Q(start__lte = date,
                         end__gte = date) |
                models.Q(start__gte = date),
                **filter_args
            ).order_by('start')

        if next:
            return queryset.filter(
                start__gte = date,
                **filter_args
            ).order_by('start')

        if prev:
            return queryset.filter(
                end__lte = date,
                **filter_args
            ).order_by('-start')

    def is_date_in_my_range(self, date = None):
        """
        Return true if the given date is in the diffusion's start-end
        range.
        """
        return self.start < date_or_default(date) < self.end

    def get_conflicts(self):
        """
        Return a list of conflictual diffusions, based on the scheduled duration.
        """
        r = Diffusion.objects.filter(
            models.Q(start__lt = self.start,
                     end__gt = self.start) |
            models.Q(start__gt = self.start,
                     start__lt = self.end)
        )
        return r

    def save(self, *args, **kwargs):
        if self.initial:
            # force link to the top initial diffusion
            if self.initial.initial:
                self.initial = self.initial.initial
            self.program = self.initial.program
        super().save(*args, **kwargs)

    def __str__(self):
        return '{self.program.name} {date} #{self.pk}'.format(
            self=self, date=self.date.strftime('%Y-%m-%d %H:%M')
        )

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')

        permissions = (
            ('programming', _('edit the diffusion\'s planification')),
        )

class Log(models.Model):
    """
    Log a played sound start and stop, or a single message
    """
    source = models.CharField(
        _('source'),
        max_length = 64,
        help_text = 'source information',
        blank = True, null = True,
    )
    date = models.DateTimeField(
        'date',
        auto_now_add=True,
    )
    comment = models.CharField(
        max_length = 512,
        blank = True, null = True,
    )
    related_type = models.ForeignKey(
        ContentType,
        blank = True, null = True,
    )
    related_id = models.PositiveIntegerField(
        blank = True, null = True,
    )
    related_object = GenericForeignKey(
        'related_type', 'related_id',
    )

    @classmethod
    def get_for_related_model(cl, model):
        """
        Return a queryset that filter related_type to the given one.
        """
        return cl.objects.filter(related_type__pk =
                                    ContentType.objects.get_for_model(model).id)

    def print(self):
        logger.info('log #%s: %s%s',
            str(self),
            self.comment or '',
            ' -- {} #{}'.format(self.related_type, self.related_id)
                if self.related_object else ''
        )

    def __str__(self):
        return '#{} ({}, {})'.format(
                self.id, self.date.strftime('%Y-%m-%d %H:%M'), self.source
        )



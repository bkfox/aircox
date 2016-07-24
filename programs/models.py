import datetime
import os
import shutil
import logging
from enum import IntEnum

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


def as_date(date, as_datetime = True):
    """
    If as_datetime, return the date with time info set to 0; else, return
    a date with date informations of the given date/time.
    """
    import datetime
    if as_datetime:
        return date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    return datetime.date(date.year, date.month, date.day)

def date_or_default(date, no_time = False):
    """
    Return date or default value (now) if not defined, and remove time info
    if date_only is True
    """
    date = date or tz.now()
    if not tz.is_aware(date):
        date = tz.make_aware(date)
    if no_time:
        return as_date(date)
    return date


class Related(models.Model):
    """
    Add a field "related" of type GenericForeignKey, plus utilities.
    """
    related_type = models.ForeignKey(
        ContentType,
        blank = True, null = True,
    )
    related_id = models.PositiveIntegerField(
        blank = True, null = True,
    )
    related = GenericForeignKey(
        'related_type', 'related_id',
    )

    @classmethod
    def get_for(cl, object = None, model = None):
        """
        Return a queryset that filter on the given object or model(s)

        * object: if given, use its type and pk; match on models only.
        * model: one model or list of models
        """
        if not model and object:
            model = type(object)

        if type(model) in (list, tuple):
            model = [ ContentType.objects.get_for_model(m).id
                        for m in model ]
            qs = cl.objects.filter(related_type__pk__in = model)
        else:
            model = ContentType.objects.get_for_model(model)
            qs = cl.objects.filter(related_type__pk = model.id)

        if object:
            qs = qs.filter(related_id = object.pk)
        return qs

    class Meta:
        abstract = True


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


class Sound(Nameable):
    """
    A Sound is the representation of a sound file that can be either an excerpt
    or a complete archive of the related diffusion.
    """
    class Type(IntEnum):
        other = 0x00,
        archive = 0x01,
        excerpt = 0x02,

    diffusion = models.ForeignKey(
        'Diffusion',
        verbose_name = _('diffusion'),
        blank = True, null = True,
        help_text = _('this is set for scheduled programs')
    )
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
    public = models.BooleanField(
        _('public'),
        default = False,
        help_text = _('the sound is accessible to the public')
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
        return main_settings.MEDIA_URL + '/' + path

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

    def check_perms(self):
        """
        Check permissions and update them if this is activated
        """
        if not settings.AIRCOX_SOUND_AUTO_CHMOD or \
                self.removed or not os.path.exists(self.path):
            return

        flags = settings.AIRCOX_SOUND_CHMOD_FLAGS[self.public]
        try:
            os.chmod(self.path, flags)
        except PermissionError as err:
            logger.error(
                'cannot set permissions {} to file {}: {}'.format(
                    self.flags[self.public],
                    self.path, err
                )
            )

    def __check_name(self):
        if not self.name and self.path:
            # FIXME: later, remove date?
            self.name = os.path.basename(self.path)
            self.name = os.path.splitext(self.name)[0]
            self.name = self.name.replace('_', ' ')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__check_name()

    def save(self, check = True, *args, **kwargs):
        if check:
            self.check_on_file()
        self.__check_name()
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
    class Frequency(IntEnum):
        first = 0b000001
        second = 0b000010
        third = 0b000100
        fourth = 0b001000
        last = 0b010000
        first_and_third = 0b000101
        second_and_fourth = 0b001010
        every = 0b011111
        one_on_two = 0b100000

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
        choices = [
            (int(y), {
                'first': _('first week of the month'),
                'second': _('second week of the month'),
                'third': _('third week of the month'),
                'fourth': _('fourth week of the month'),
                'last': _('last week of the month'),
                'first_and_third': _('first and third weeks of the month'),
                'second_and_fourth': _('second and fourth weeks of the month'),
                'every': _('every week'),
                'one_on_two': _('one week on two'),
            }[x]) for x,y in Frequency.__members__.items()
        ],
    )
    initial = models.ForeignKey(
        'self',
        verbose_name = _('initial'),
        blank = True, null = True,
        help_text = 'this schedule is a rerun of this one',
    )

    @property
    def end(self):
        return self.date + utils.to_timedelta(self.duration)

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
        # since we care only about the week, go to the same day of the week
        date = date_or_default(date)
        date += tz.timedelta(days = self.date.weekday() - date.weekday() )

        if self.frequency == Schedule.Frequency.one_on_two:
            # cf notes in date_of_month
            diff = as_date(date, False) - as_date(self.date, False)
            return not (diff.days % 14)

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
        if freq == Schedule.Frequency.last:
            date += tz.timedelta(days = 4 * 7)
            next_date = date + tz.timedelta(days = 7)
            if next_date.month == month:
                date = next_date
            return [self.normalize(date)]

        dates = []
        if freq == Schedule.Frequency.one_on_two:
            # NOTE previous algorithm was based on the week number, but this
            # approach is wrong because number of weeks in a year can be
            # 52 or 53. This also clashes with the first week of the year.
            diff = as_date(date, False) - as_date(self.date, False)
            if diff.days % 14:
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
                week += 1;
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


class DiffusionManager(models.Manager):
    def get_at(self, date = None):
        """
        Return a queryset of diffusions that have the given date
        in their range.

        If date is a datetime.date object, check only against the
        date.
        """
        date = date or tz.now()
        if not issubclass(type(date), datetime.datetime):
            return self.filter(
                models.Q(start__contains = date) | \
                models.Q(end__contains = date)
            )

        return self.filter(
            models.Q(start__lte = date, end__gte = date) |
            # FIXME: should not be here?
            models.Q(start__gte = date),
        ).order_by('start')

    def get_after(self, date = None):
        """
        Return a queryset of diffusions that happen after the given
        date.
        """
        date = date_or_default(date)
        return self.filter(
            start__gte = date,
        ).order_by('start')

    def get_before(self, date):
        """
        Return a queryset of diffusions that finish before the given
        date.
        """
        date = date_or_default(date)
        return self.filter(
            end__lte = date,
        ).order_by('start')


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
    objects = DiffusionManager()

    class Type(IntEnum):
        normal = 0x00
        unconfirmed = 0x01
        canceled = 0x02

    # common
    program = models.ForeignKey (
        'Program',
        verbose_name = _('program'),
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
        List of archives' path; uses get_archives
        """
        return [ sound.path for sound in self.get_archives() ]

    def get_archives(self):
        """
        Return a list of available archives sounds for the given episode,
        ordered by path.
        """
        sounds = self.initial.sound_set if self.initial else self.sound_set
        return sounds.filter(type = Sound.Type.archive, removed = False). \
                      order_by('path')

    def is_date_in_range(self, date = None):
        """
        Return true if the given date is in the diffusion's start-end
        range.
        """
        date = date or tz.now()
        return self.start < date < self.end

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


class Track(Related):
    """
    Track of a playlist of an object. The position can either be expressed
    as the position in the playlist or as the moment in seconds it started.
    """
    # There are no nice solution for M2M relations ship (even without
    # through) in django-admin. So we unfortunately need to make one-
    # to-one relations and add a position argument
    title = models.CharField (
        _('title'),
        max_length = 128,
    )
    artist = models.CharField(
        _('artist'),
        max_length = 128,
    )
    tags = TaggableManager(
        verbose_name=_('tags'),
        blank=True,
    )
    info = models.CharField(
        _('information'),
        max_length = 128,
        blank = True, null = True,
        help_text=_('additional informations about this track, such as '
                    'the version, if is it a remix, features, etc.'),
    )
    position = models.SmallIntegerField(
        default = 0,
        help_text=_('position in the playlist'),
    )
    in_seconds = models.BooleanField(
        _('in seconds'),
        default = False,
        help_text=_('position in the playlist is expressed in seconds')
    )

    def __str__(self):
        return '{self.artist} -- {self.title}'.format(self=self)

    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')



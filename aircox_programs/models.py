import os

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.html import strip_tags
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from taggit.managers import TaggableManager

import aircox_programs.utils as utils
import aircox_programs.settings as settings


def date_or_default (date, date_only = False):
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


class Nameable (models.Model):
    name = models.CharField (
        _('name'),
        max_length = 128,
    )

    @property
    def slug (self):
        """
        Slug based on the name. We replace '-' by '_'
        """
        return slugify(self.name).replace('-', '_')

    def __str__ (self):
        #if self.pk:
        #    return '#{} {}'.format(self.pk, self.name)
        return '{}'.format(self.name)

    class Meta:
        abstract = True


class Track (Nameable):
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
        _('tags'),
        blank = True,
    )

    def __str__(self):
        return ' '.join([self.artist, ':', self.name ])

    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')


class Sound (Nameable):
    """
    A Sound is the representation of a sound file that can be either an excerpt
    or a complete archive of the related diffusion.

    The podcasting and public access permissions of a Sound are managed through
    the related program info.
    """
    Type = {
        'other': 0x00,
        'archive': 0x01,
        'excerpt': 0x02,
    }
    for key, value in Type.items():
        ugettext_lazy(key)

    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (y, x) for x,y in Type.items() ],
        blank = True, null = True
    )
    path = models.FilePathField(
        _('file'),
        path = settings.AIRCOX_PROGRAMS_DIR,
        match = r'(' + '|'.join(settings.AIRCOX_SOUND_FILE_EXT) \
                                    .replace('.', r'\.') + ')$',
        recursive = True,
        blank = True, null = True,
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
        help_text = _('sound\'s is accessible through the website')
    )

    def get_mtime (self):
        """
        Get the last modification date from file
        """
        mtime = os.stat(self.path).st_mtime
        mtime = tz.datetime.fromtimestamp(mtime)
        # db does not store microseconds
        mtime = mtime.replace(microsecond = 0)
        return tz.make_aware(mtime, tz.get_current_timezone())

    def file_exists (self):
        """
        Return true if the file still exists
        """
        return os.path.exists(self.path)

    def check_on_file (self):
        """
        Check sound file info again'st self, and update informations if
        needed (do not save). Return True if there was changes.
        """
        if not self.file_exists():
            if self.removed:
                return
            self.removed = True
            return True

        old_removed = self.removed
        self.removed = False

        mtime = self.get_mtime()
        if self.mtime != mtime:
            self.mtime = mtime
            self.good_quality = False
            return True
        return old_removed != self.removed

    def save (self, check = True, *args, **kwargs):
        if check:
            self.check_on_file()

        if not self.name and self.path:
            self.name = os.path.basename(self.path) \
                            .splitext() \
                            .replace('_', ' ')
        super().save(*args, **kwargs)

    def __str__ (self):
        return '/'.join(self.path.split('/')[-3:])

    class Meta:
        verbose_name = _('Sound')
        verbose_name_plural = _('Sounds')


class Stream (models.Model):
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
        help_text = _('plays this playlist at least every delay')
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


class Schedule (models.Model):
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
        'every':            (0b011111, _('once a week')),
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

    def match (self, date = None, check_time = True):
        """
        Return True if the given datetime matches the schedule
        """
        date = date_or_default(date)

        if self.date.weekday() == date.weekday() and self.match_week(date):
            return self.date.time() == date.time() if check_time else True
        return False

    def match_week (self, date = None):
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

    def normalize (self, date):
        """
        Set the time of a datetime to the schedule's one
        """
        return date.replace(hour = self.date.hour, minute = self.date.minute)

    def dates_of_month (self, date = None):
        """
        Return a list with all matching dates of date.month (=today)
        """
        date = date_or_default(date, True).replace(day=1)
        fwday = date.weekday()
        wday = self.date.weekday()

        # move date to the date weekday of the schedule
        # check on SO#3284452 for the formula
        date += tz.timedelta(days = (7 if fwday > wday else 0) - fwday + wday)
        fwday = date.weekday()

        # special frequency case
        weeks = self.frequency
        if self.frequency == Schedule.Frequency['last']:
            date += tz.timedelta(month = 1, days = -7)
            return self.normalize([date])
        if weeks == Schedule.Frequency['one on two']:
            # if both week are the same, then the date week of the month
            # matches. Note: wday % 2 + fwday % 2 => (wday + fwday) % 2
            fweek = date.isocalendar()[1]

            if date.month == 1 and fweek >= 50:
                # isocalendar can think we are on the last week of the
                # previous year
                fweek = 0
            week = self.date.isocalendar()[1]
            weeks = 0b010101 if not (fweek + week) % 2 else 0b001010

        dates = []
        for week in range(0,5):
            # there can be five weeks in a month
            if not weeks & (0b1 << week):
                continue
            wdate = date + tz.timedelta(days = week * 7)
            if wdate.month == date.month:
                dates.append(self.normalize(wdate))
        return dates

    def diffusions_of_month (self, date, exclude_saved = False):
        """
        Return a list of Diffusion instances, from month of the given date, that
        can be not in the database.

        If exclude_saved, exclude all diffusions that are yet in the database.
        """
        dates = self.dates_of_month(date)
        saved = Diffusion.objects.filter(date__in = dates,
                                         program = self.program)
        diffusions = []

        # existing diffusions
        for item in saved:
            if item.date in dates:
                dates.remove(item.date)
            if not exclude_saved:
                diffusions.append(item)

        # others
        for date in dates:
            first_date = date
            if self.initial:
                first_date -= self.date - self.initial.date

            first_diffusion = Diffusion.objects.filter(date = first_date,
                                                       program = self.program)
            first_diffusion = first_diffusion[0] if first_diffusion.count() \
                              else None
            diffusions.append(Diffusion(
                                 program = self.program,
                                 type = Diffusion.Type['unconfirmed'],
                                 initial = first_diffusion if self.initial else None,
                                 date = date,
                                 duration = self.duration,
                             ))
        return diffusions

    def __str__ (self):
        frequency = [ x for x,y in Schedule.Frequency.items()
                        if y == self.frequency ]
        return self.program.name + ': ' + frequency[0] + ' (' + str(self.date) + ')'

    class Meta:
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class Station (Nameable):
    """
    A Station regroup one or more programs (stream and normal), and is the top
    element used to generate streams outputs and configuration.
    """
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('this station is active')
    )
    public = models.BooleanField(
        _('public'),
        default = True,
        help_text = _('information are available to the public'),
    )
    fallback = models.FilePathField(
        _('fallback song'),
        match = r'(' + '|'.join(settings.AIRCOX_SOUND_FILE_EXT) \
                                    .replace('.', r'\.') + ')$',
        recursive = True,
        blank = True, null = True,
        help_text = _('use this song file if there is a problem and nothing is '
                      'played')
    )


class Program (Nameable):
    """
    A Program can either be a Streamed or a Scheduled program.

    A Streamed program is used to generate non-stop random playlists when there
    is not scheduled diffusion. In such a case, a Stream is used to describe
    diffusion informations.

    A Scheduled program has a schedule and is the one with a normal use case.
    """
    station = models.ForeignKey(
        Station,
        verbose_name = _('station')
    )
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
    def path (self):
        """
        Return the path to the programs directory
        """
        return os.path.join(settings.AIRCOX_PROGRAMS_DIR,
                            self.slug + '_' + str(self.id) )

    def ensure_dir (self, subdir = None):
        """
        Make sur the program's dir exists (and optionally subdir). Return True
        if the dir (or subdir) exists.
        """
        path = self.path
        if not os.path.exists(path):
            os.mkdir(path)

        if subdir:
            path = os.path.join(path, subdir)
            if not os.path.exists(path):
                os.mkdir(path)
        return os.path.exists(path)


    def find_schedule (self, date):
        """
        Return the first schedule that matches a given date.
        """
        schedules = Schedule.objects.filter(program = self)
        for schedule in schedules:
            if schedule.match(date, check_time = False):
                return schedule


class Diffusion (models.Model):
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
    Type = {
        'default':      0x00,   # diffusion is planified
        'unconfirmed':  0x01,   # scheduled by the generator but not confirmed for diffusion
        'cancel':       0x02,   # diffusion canceled
    }
    for key, value in Type.items():
        ugettext_lazy(key)

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
        choices = [ (y, x) for x,y in Type.items() ],
    )
    initial = models.ForeignKey (
        'self',
        verbose_name = _('initial'),
        blank = True, null = True,
        help_text = _('the diffusion is a rerun of this one')
    )
    date = models.DateTimeField( _('start of the diffusion') )
    duration = models.TimeField(
        _('duration'),
        blank = True, null = True,
        help_text = _('regular duration'),
    )

    def archives_duration (self):
        """
        Get total duration of the archives. May differ from the schedule
        duration.
        """
        sounds = self.initial.sounds if self.initial else self.sounds
        r = [ sound.duration
                for sound in sounds.filter(type = Sound.Type['archive'])
                if sound.duration ]
        return utils.time_sum(r) if r else self.duration

    def get_archives (self):
        """
        Return an ordered list of archives sounds for the given episode.
        """
        sounds = self.initial.sounds if self.initial else self.sounds
        r = [ sound for sound in sounds.all().order_by('path')
              if sound.type == Sound.Type['archive'] ]
        return r

    @classmethod
    def get_next (cl, station = None, date = None, **filter_args):
        """
        Return a queryset with the upcoming diffusions, ordered by
        +date
        """
        filter_args['date__gte'] = date_or_default(date)
        if station:
            filter_args['program__station'] = station
        return cl.objects.filter(**filter_args).order_by('date')

    @classmethod
    def get_prev (cl, station = None, date = None, **filter_args):
        """
        Return a queryset with the previous diffusion, ordered by
        -date
        """
        filter_args['date__lte'] = date_or_default(date)
        if station:
            filter_args['program__station'] = station
        return cl.objects.filter(**filter_args).order_by('-date')

    def save (self, *args, **kwargs):
        if self.initial:
            if self.initial.initial:
                self.initial = self.initial.initial
            self.program = self.initial.program
        super(Diffusion, self).save(*args, **kwargs)

    def __str__ (self):
        return self.program.name + ', ' + \
                self.date.strftime('%Y-%m-%d %H:%M') +\
                '' # FIXME str(self.type_display)

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')

        permissions = (
            ('programming', _('edit the diffusion\'s planification')),
        )


class Log (models.Model):
    """
    Log a played sound start and stop, or a single message
    """
    source = models.CharField(
        _('source'),
        max_length = 64,
        help_text = 'source information',
        blank = True, null = True,
    )
    sound = models.ForeignKey(
        'Sound',
        help_text = _('played sound'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        'date',
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

    def print (self):
        print(str(self), ':', self.comment or '')
        if self.diffusion:
            print(' - diffusion #' + str(self.diffusion.id))
        if self.sound:
            print(' - sound #' + str(self.sound.id), self.sound.path)

    def __str__ (self):
        return self.date.strftime('%Y-%m-%d %H:%M') + ', ' + self.source



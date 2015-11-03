import os

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.html import strip_tags

from taggit.managers import TaggableManager

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

    def get_slug_name (self):
        return slugify(self.name)

    def __str__ (self):
        #if self.pk:
        #    return '#{} {}'.format(self.pk, self.name)
        return '{}'.format(self.name)

    class Meta:
        abstract = True


class Track (Nameable):
    # There are no nice solution for M2M relations ship (even without
    # through) in django-admin. So we unfortunately need to make one-
    # to-one relations and add a position argument
    episode = models.ForeignKey(
        'Episode',
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
    or a complete archive of the related episode.

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
        match = r'(' + '|'.join(settings.AIRCOX_SOUND_FILE_EXT).replace('.', r'\.') + ')$',
        recursive = True,
        blank = True, null = True,
    )
    embed = models.TextField(
        _('embed HTML code'),
        blank = True, null = True,
        help_text = _('HTML code used to embed a sound from external plateform'),
    )
    duration = models.IntegerField(
        _('duration'),
        blank = True, null = True,
        help_text = _('duration in seconds'),
    )
    date = models.DateTimeField(
        _('date'),
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
        return tz.make_aware(mtime, tz.get_current_timezone())

    def file_exists (self):
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
        if self.date != mtime:
            self.date = mtime
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


class Schedule (models.Model):
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
        blank = True, null = True,
    )
    date = models.DateTimeField(_('date'))
    duration = models.TimeField(
        _('duration'),
    )
    frequency = models.SmallIntegerField(
        _('frequency'),
        choices = VerboseFrequency.items(),
    )
    rerun = models.ForeignKey(
        'self',
        verbose_name = _('rerun'),
        blank = True, null = True,
        help_text = "Schedule of a rerun of this one",
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
        wday = self.date.weekday()
        fwday = date.weekday()

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

        When a Diffusion is created, it tries to attach the corresponding
        episode using a match of episode.date (and takes care of rerun case);
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
            if self.rerun:
                first_date -= self.date - self.rerun.date

            diffusion = Diffusion.objects.filter(date = first_date,
                                                 program = self.program)
            episode = diffusion[0].episode if diffusion.count() else None

            diffusions.append(Diffusion(
                                 episode = episode,
                                 program = self.program,
                                 stream = self.program.stream,
                                 type = Diffusion.Type['unconfirmed'],
                                 date = date,
                             ))
        return diffusions

    def __str__ (self):
        frequency = [ x for x,y in Schedule.Frequency.items()
                        if y == self.frequency ]
        return self.program.name + ': ' + frequency[0] + ' (' + str(self.date) + ')'

    class Meta:
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class Diffusion (models.Model):
    Type = {
        'default':      0x00,   # simple diffusion (done/planed)
        'unconfirmed':  0x01,   # scheduled by the generator but not confirmed for diffusion
        'cancel':       0x02,   # cancellation happened; used to inform users
        # 'restart':      0x03,   # manual restart; used to remix/give up antenna
        'stop':         0x04,   # diffusion has been forced to stop
    }
    for key, value in Type.items():
        ugettext_lazy(key)

    episode = models.ForeignKey (
        'Episode',
        blank = True, null = True,
        verbose_name = _('episode'),
    )
    program = models.ForeignKey (
        'Program',
        verbose_name = _('program'),
    )
    # program.stream can change, but not the stream;
    stream = models.ForeignKey(
        'Stream',
        verbose_name = _('stream'),
        default = 0,
        help_text = 'stream id on which the diffusion happens',
    )
    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (y, x) for x,y in Type.items() ],
    )
    date = models.DateTimeField( _('start of the diffusion') )

    def save (self, *args, **kwargs):
        if self.episode: # FIXME self.episode or kwargs['episode']
            self.program = self.episode.program
        # check type against stream's type
        super(Diffusion, self).save(*args, **kwargs)

    def __str__ (self):
        return self.program.name + ' on ' + str(self.date) \
               + str(self.type)

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')


class Stream (Nameable):
    Type = {
        'random':   0x00,   # selection using random function
        'schedule': 0x01,   # selection using schedule
    }
    for key, value in Type.items():
        ugettext_lazy(key)

    public = models.BooleanField(
        _('public'),
        default = True,
        help_text = _('program list is public'),
    )
    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (y, x) for x,y in Type.items() ],
    )
    priority = models.SmallIntegerField(
        _('priority'),
        default = 0,
        help_text = _('priority of the stream')
    )
    time_start = models.TimeField(
        _('start'),
        blank = True, null = True,
        help_text = _('if random, used to define a time range this stream is'
                      'played')
    )
    time_end = models.TimeField(
        _('end'),
        blank = True, null = True,
        help_text = _('if random, used to define a time range this stream is'
                      'played')
    )

    # get info for:
    # - random lists
    # - scheduled lists


class Program (Nameable):
    stream = models.ForeignKey(
        Stream,
        verbose_name = _('streams'),
    )
    active = models.BooleanField(
        _('inactive'),
        default = True,
        help_text = _('if not set this program is no longer active')
    )

    @property
    def path (self):
        return os.path.join(settings.AIRCOX_PROGRAMS_DIR,
                            slugify(self.name + '_' + str(self.id)) )

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


class Episode (Nameable):
    program = models.ForeignKey(
        Program,
        verbose_name = _('program'),
        help_text = _('parent program'),
    )
    sounds = models.ManyToManyField(
        Sound,
        blank = True,
        verbose_name = _('sounds'),
    )

    class Meta:
        verbose_name = _('Episode')
        verbose_name_plural = _('Episodes')



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
        if self.pk:
            return '#{} {}'.format(self.pk, self.name)
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
    A Sound is the representation of a sound, that can be:
    - An episode podcast/complete record
    - An episode partial podcast
    - An episode is a part of the episode but not usable for direct podcast

    We can manage this using the "public" and "fragment" fields. If a Sound is
    public, then we can podcast it. If a Sound is a fragment, then it is not
    usable for diffusion.

    Each sound can be associated to a filesystem's file or an embedded
    code (for external podcasts).
    """
    path = models.FilePathField(
        _('file'),
        path = settings.AIRCOX_PROGRAMS_DIR,
        match = '*(' + '|'.join(settings.AIRCOX_SOUNDFILE_EXT) + ')$',
        recursive = True,
        blank = True, null = True,
    )
    embed = models.TextField(
        _('embed HTML code from external website'),
        blank = True, null = True,
        help_text = _('if set, consider the sound podcastable'),
    )
    duration = models.TimeField(
        _('duration'),
        blank = True, null = True,
    )
    public = models.BooleanField(
        _('public'),
        default = False,
        help_text = _("the element is public"),
    )
    fragment = models.BooleanField(
        _('incomplete sound'),
        default = False,
        help_text = _("the file is a cut"),
    )
    removed = models.BooleanField(
        default = False,
        help_text = _('this sound has been removed from filesystem'),
    )

    def get_mtime (self):
        """
        Get the last modification date from file
        """
        mtime = os.stat(self.path).st_mtime
        mtime = tz.datetime.fromtimestamp(mtime)
        return tz.make_aware(mtime, timezone.get_current_timezone())

    def save (self, *args, **kwargs):
        if not self.pk:
            self.date = self.get_mtime()

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
        date = date_or_default(date)
        if self.frequency == Schedule.Frequency['one on two']:
            week = date.isocalendar()[1]
            return (week % 2) == (self.date.isocalendar()[1] % 2)

        first_of_month = tz.datetime.date(date.year, date.month, 1)
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


class Stream (models.Model):
    Type = {
        'random':   0x00,   # selection using random function
        'schedule': 0x01,   # selection using schedule
    }
    for key, value in Type.items():
        ugettext_lazy(key)

    name = models.CharField(
        _('name'),
        max_length = 32,
        blank = True,
        null = True,
    )
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

    # get info for:
    # - random lists
    # - scheduled lists
    # link between Streams and Programs:
    #   - hours range (non-stop)
    #   - stream/pgm

    def __str__ (self):
        return '#{} {}'.format(self.priority, self.name)


class Program (Nameable):
    stream = models.ForeignKey(
        Stream,
        verbose_name = _('stream'),
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

    def find_schedule (self, date):
        """
        Return the first schedule that matches a given date
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



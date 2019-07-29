import calendar
from collections import OrderedDict
import datetime
from enum import IntEnum
import logging
import os
import shutil

import pytz
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Concat, Substr
from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from aircox import settings, utils
from .page import Page, PageQuerySet
from .station import Station


logger = logging.getLogger('aircox')


__all__ = ['Program', 'ProgramQuerySet', 'Stream', 'Schedule']


class ProgramQuerySet(PageQuerySet):
    def station(self, station):
        # FIXME: reverse-lookup
        return self.filter(station=station)


class Program(Page):
    """
    A Program can either be a Streamed or a Scheduled program.

    A Streamed program is used to generate non-stop random playlists when there
    is not scheduled diffusion. In such a case, a Stream is used to describe
    diffusion informations.

    A Scheduled program has a schedule and is the one with a normal use case.

    Renaming a Program rename the corresponding directory to matches the new
    name if it does not exists.
    """
    station = models.ForeignKey(
        Station,
        verbose_name=_('station'),
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('if not checked this program is no longer active')
    )
    sync = models.BooleanField(
        _('syncronise'),
        default=True,
        help_text=_('update later diffusions according to schedule changes')
    )

    objects = ProgramQuerySet.as_manager()

    @property
    def path(self):
        """ Return program's directory path """
        return os.path.join(settings.AIRCOX_PROGRAMS_DIR, self.slug)

    @property
    def archives_path(self):
        return os.path.join(self.path, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR)

    @property
    def excerpts_path(self):
        return os.path.join(
            self.path, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR
        )

    def __init__(self, *kargs, **kwargs):
        super().__init__(*kargs, **kwargs)

        if self.slug:
            self.__initial_path = self.path

    @classmethod
    def get_from_path(cl, path):
        """
        Return a Program from the given path. We assume the path has been
        given in a previous time by this model (Program.path getter).
        """
        path = path.replace(settings.AIRCOX_PROGRAMS_DIR, '')

        while path[0] == '/':
            path = path[1:]

        while path[-1] == '/':
            path = path[:-2]

        if '/' in path:
            path = path[:path.index('/')]

        path = path.split('_')
        path = path[-1]
        qs = cl.objects.filter(id=int(path))

        return qs[0] if qs else None

    def ensure_dir(self, subdir=None):
        """
        Make sur the program's dir exists (and optionally subdir). Return True
        if the dir (or subdir) exists.
        """
        path = os.path.join(self.path, subdir) if subdir else \
            self.path
        os.makedirs(path, exist_ok=True)

        return os.path.exists(path)

    def __str__(self):
        return self.title

    def save(self, *kargs, **kwargs):
        from .sound import Sound

        super().save(*kargs, **kwargs)

        path_ = getattr(self, '__initial_path', None)
        if path_ is not None and path_ != self.path and \
                os.path.exists(path_) and not os.path.exists(self.path):
            logger.info('program #%s\'s dir changed to %s - update it.',
                        self.id, self.title)

            shutil.move(path_, self.path)
            Sound.objects.filter(path__startswith=path_) \
                 .update(path=Concat('path', Substr(F('path'), len(path_))))


class BaseRerunQuerySet(models.QuerySet):
    def rerun(self):
        return self.filter(initial__isnull=False)

    def initial(self):
        return self.filter(initial__isnull=True)


class BaseRerun(models.Model):
    """
    Abstract model offering rerun facilities.
    `start` datetime field or property must be implemented by sub-classes
    """
    program = models.ForeignKey(
        Program, models.CASCADE,
        verbose_name=_('related program'),
    )
    initial = models.ForeignKey(
        'self', models.SET_NULL, related_name='rerun_set',
        verbose_name=_('initial schedule'),
        blank=True, null=True,
        help_text=_('mark as rerun of this %(model_name)'),
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.initial is not None:
            self.initial = self.initial.get_initial()
        if self.initial == self:
            self.initial = None

        if self.is_rerun:
            self.save_rerun()
        else:
            self.save_initial()
        super().save(*args, **kwargs)

    def save_rerun(self):
        pass

    def save_initial(self):
        pass

    @property
    def is_initial(self):
        return self.initial is None

    @property
    def is_rerun(self):
        return self.initial is not None

    def get_initial(self):
        """ Return the initial schedule (self or initial) """
        return self if self.initial is None else self.initial.get_initial()

    def clean(self):
        super().clean()
        if self.initial is not None and self.initial.start >= self.start:
            raise ValidationError({
                'initial': _('rerun must happen after initial')
            })


# BIG FIXME: self.date is still used as datetime
class Schedule(BaseRerun):
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
        ponctual = 0b000000
        first = 0b000001
        second = 0b000010
        third = 0b000100
        fourth = 0b001000
        last = 0b010000
        first_and_third = 0b000101
        second_and_fourth = 0b001010
        every = 0b011111
        one_on_two = 0b100000

    date = models.DateField(
        _('date'), help_text=_('date of the first diffusion'),
    )
    time = models.TimeField(
        _('time'), help_text=_('start time'),
    )
    timezone = models.CharField(
        _('timezone'),
        default=tz.get_current_timezone, max_length=100,
        choices=[(x, x) for x in pytz.all_timezones],
        help_text=_('timezone used for the date')
    )
    duration = models.TimeField(
        _('duration'),
        help_text=_('regular duration'),
    )
    frequency = models.SmallIntegerField(
        _('frequency'),
        choices=[(int(y), {
            'ponctual': _('ponctual'),
            'first': _('1st {day} of the month'),
            'second': _('2nd {day} of the month'),
            'third': _('3rd {day} of the month'),
            'fourth': _('4th {day} of the month'),
            'last': _('last {day} of the month'),
            'first_and_third': _('1st and 3rd {day}s of the month'),
            'second_and_fourth': _('2nd and 4th {day}s of the month'),
            'every': _('every {day}'),
            'one_on_two': _('one {day} on two'),
        }[x]) for x, y in Frequency.__members__.items()],
    )


    class Meta:
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')

    def __str__(self):
        return '{} - {}, {}'.format(
            self.program.title, self.get_frequency_verbose(),
            self.time.strftime('%H:%M')
        )

    def save_rerun(self, *args, **kwargs):
        self.program = self.initial.program
        self.duration = self.initial.duration
        self.frequency = self.initial.frequency

    @cached_property
    def tz(self):
        """ Pytz timezone of the schedule.  """
        import pytz
        return pytz.timezone(self.timezone)

    @cached_property
    def start(self):
        """ Datetime of the start (timezone unaware) """
        return tz.datetime.combine(self.date, self.time)

    @cached_property
    def end(self):
        """ Datetime of the end """
        return self.start + utils.to_timedelta(self.duration)

    def get_frequency_verbose(self):
        """ Return frequency formated for display """
        from django.template.defaultfilters import date
        return self.get_frequency_display().format(
            day=date(self.date, 'l')
        )

    # initial cached data
    __initial = None

    def changed(self, fields=['date', 'duration', 'frequency', 'timezone']):
        initial = self._Schedule__initial

        if not initial:
            return

        this = self.__dict__

        for field in fields:
            if initial.get(field) != this.get(field):
                return True

        return False

    def match(self, date=None, check_time=True):
        """
        Return True if the given date(time) matches the schedule.
        """
        date = utils.date_or_default(
            date, tz.datetime if check_time else datetime.date)

        if self.date.weekday() != date.weekday() or \
                not self.match_week(date):
            return False

        # we check against a normalized version (norm_date will have
        # schedule's date.
        return date == self.normalize(date) if check_time else True

    def match_week(self, date=None):
        """
        Return True if the given week number matches the schedule, False
        otherwise.
        If the schedule is ponctual, return None.
        """

        if self.frequency == Schedule.Frequency.ponctual:
            return False

        # since we care only about the week, go to the same day of the week
        date = utils.date_or_default(date, datetime.date)
        date += tz.timedelta(days=self.date.weekday() - date.weekday())

        # FIXME this case

        if self.frequency == Schedule.Frequency.one_on_two:
            # cf notes in date_of_month
            diff = date - utils.cast_date(self.date, datetime.date)

            return not (diff.days % 14)

        first_of_month = date.replace(day=1)
        week = date.isocalendar()[1] - first_of_month.isocalendar()[1]

        # weeks of month

        if week == 4:
            # fifth week: return if for every week

            return self.frequency == self.Frequency.every

        return (self.frequency & (0b0001 << week) > 0)

    def normalize(self, date):
        """
        Return a new datetime with schedule time. Timezone is handled
        using `schedule.timezone`.
        """
        date = tz.datetime.combine(date, self.time)
        return self.tz.normalize(self.tz.localize(date))

    def dates_of_month(self, date):
        """ Return normalized diffusion dates of provided date's month. """
        if self.frequency == Schedule.Frequency.ponctual:
            return []

        sched_wday, freq = self.date.weekday(), self.frequency
        date = date.replace(day=1)

        # last of the month
        if freq == Schedule.Frequency.last:
            date = date.replace(
                day=calendar.monthrange(date.year, date.month)[1])
            date_wday = date.weekday()

            # end of month before the wanted weekday: move one week back

            if date_wday < sched_wday:
                date -= tz.timedelta(days=7)
            date += tz.timedelta(days=sched_wday - date_wday)

            return [self.normalize(date)]

        # move to the first day of the month that matches the schedule's weekday
        # check on SO#3284452 for the formula
        date_wday, month = date.weekday(), date.month
        date += tz.timedelta(days=(7 if date_wday > sched_wday else 0) -
                                   date_wday + sched_wday)

        if freq == Schedule.Frequency.one_on_two:
            # - adjust date with modulo 14 (= 2 weeks in days)
            # - there are max 3 "weeks on two" per month
            if (date - self.date).days % 14:
                date += tz.timedelta(days=7)
            dates = (date + tz.timedelta(days=14*i) for i in range(0, 3))
        else:
            dates = (date + tz.timedelta(days=7*week) for week in range(0, 5)
                     if freq & (0b1 << week))

        return [self.normalize(date) for date in dates if date.month == month]


    def _exclude_existing_date(self, dates):
        from .episode import Diffusion
        saved = set(Diffusion.objects.filter(start__in=dates)
                                     .values_list('start', flat=True))
        return [date for date in dates if date not in saved]


    def diffusions_of_month(self, date):
        """
        Get episodes and diffusions for month of provided date, including
        reruns.
        :returns: tuple([Episode], [Diffusion])
        """
        from .episode import Diffusion, Episode
        if self.initial is not None or \
                self.frequency == Schedule.Frequency.ponctual:
            return []

        # dates for self and reruns as (date, initial)
        reruns = [(rerun, rerun.date - self.date)
                  for rerun in self.rerun_set.all()]

        dates = OrderedDict((date, None) for date in self.dates_of_month(date))
        dates.update([(rerun.normalize(date.date() + delta), date)
                      for date in dates.keys() for rerun, delta in reruns])

        # remove dates corresponding to existing diffusions
        saved = set(Diffusion.objects.filter(start__in=dates.keys(),
                                             program=self.program)
                             .values_list('start', flat=True))

        # make diffs
        duration = utils.to_timedelta(self.duration)
        diffusions = {}
        episodes = {}

        for date, initial in dates.items():
            if date in saved:
                continue

            if initial is None:
                episode = Episode.from_date(self.program, date)
                episodes[date] = episode
            else:
                episode = episodes[initial]
                initial = diffusions[initial]

            diffusions[date] = Diffusion(
                episode=episode, type=Diffusion.Type.on_air,
                initial=initial, start=date, end=date+duration
            )
        return episodes.values(), diffusions.values()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO/FIXME: use validators?
        if self.initial is not None and self.date > self.date:
            raise ValueError('initial must be later')

        # initial only if it has been yet saved
        if self.pk:
            self.__initial = self.__dict__.copy()


class Stream(models.Model):
    """
    When there are no program scheduled, it is possible to play sounds
    in order to avoid blanks. A Stream is a Program that plays this role,
    and whose linked to a Stream.

    All sounds that are marked as good and that are under the related
    program's archive dir are elligible for the sound's selection.
    """
    program = models.ForeignKey(
        Program, models.CASCADE,
        verbose_name=_('related program'),
    )
    delay = models.TimeField(
        _('delay'), blank=True, null=True,
        help_text=_('minimal delay between two sound plays')
    )
    begin = models.TimeField(
        _('begin'), blank=True, null=True,
        help_text=_('used to define a time range this stream is'
                    'played')
    )
    end = models.TimeField(
        _('end'),
        blank=True, null=True,
        help_text=_('used to define a time range this stream is'
                    'played')
    )



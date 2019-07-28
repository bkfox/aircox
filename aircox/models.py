import calendar
import datetime
import logging
import os
import shutil
from enum import IntEnum

import pytz
from django.conf import settings as main_settings
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Concat, Substr
from django.db.transaction import atomic
from django.utils import timezone as tz
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

import aircox.settings as settings
import aircox.utils as utils
from taggit.managers import TaggableManager

logger = logging.getLogger('aircox.core')


#
# Station related classes
#
class StationQuerySet(models.QuerySet):
    def default(self, station=None):
        """
        Return station model instance, using defaults or
        given one.
        """
        if station is None:
            return self.order_by('-default', 'pk').first()
        return self.filter(pk=station).first()


def default_station():
    """ Return default station (used by model fields) """
    return Station.objects.default()


class Station(models.Model):
    """
    Represents a radio station, to which multiple programs are attached
    and that is used as the top object for everything.

    A Station holds controllers for the audio stream generation too.
    Theses are set up when needed (at the first access to these elements)
    then cached.
    """
    name = models.CharField(_('name'), max_length=64)
    slug = models.SlugField(_('slug'), max_length=64, unique=True)
    path = models.CharField(
        _('path'),
        help_text=_('path to the working directory'),
        max_length=256,
        blank=True,
    )
    default = models.BooleanField(
        _('default station'),
        default=True,
        help_text=_('if checked, this station is used as the main one')
    )

    objects = StationQuerySet.as_manager()

    #
    # Controllers
    #
    __sources = None
    __dealer = None
    __streamer = None

    def __prepare_controls(self):
        import aircox.controllers as controllers
        if not self.__streamer:
            self.__streamer = controllers.Streamer(station=self)
            self.__dealer = controllers.Source(station=self)
            self.__sources = [self.__dealer] + [
                controllers.Source(station=self, program=program)

                for program in Program.objects.filter(stream__isnull=False)
            ]

    @property
    def inputs(self):
        """
        Return all active input ports of the station
        """
        return self.port_set.filter(
            direction=Port.Direction.input,
            active=True
        )

    @property
    def outputs(self):
        """ Return all active output ports of the station """
        return self.port_set.filter(
            direction=Port.Direction.output,
            active=True,
        )

    @property
    def sources(self):
        """ Audio sources, dealer included """
        self.__prepare_controls()
        return self.__sources

    @property
    def dealer(self):
        self.__prepare_controls()
        return self.__dealer

    @property
    def streamer(self):
        """
        Audio controller for the station
        """
        self.__prepare_controls()
        return self.__streamer

    def on_air(self, date=None, count=0):
        """
        Return a queryset of what happened on air, based on logs and
        diffusions informations. The queryset is sorted by -date.

        * date: only for what happened on this date;
        * count: number of items to retrieve if not zero;

        If date is not specified, count MUST be set to a non-zero value.

        It is different from Logs.on_air method since it filters
        out elements that should have not been on air, such as a stream
        that has been played when there was a live diffusion.
        """
        # TODO argument to get sound instead of tracks
        if not date and not count:
            raise ValueError('at least one argument must be set')

        # FIXME can be a potential source of bug
        if date:
            date = utils.cast_date(date, datetime.date)
        if date and date > datetime.date.today():
            return []

        now = tz.now()
        if date:
            logs = Log.objects.at(date)
            diffs = Diffusion.objects.station(self).at(date) \
                .filter(start__lte=now, type=Diffusion.Type.normal) \
                .order_by('-start')
        else:
            logs = Log.objects
            diffs = Diffusion.objects \
                             .filter(type=Diffusion.Type.normal,
                                     start__lte=now) \
                             .order_by('-start')[:count]

        q = Q(diffusion__isnull=False) | Q(track__isnull=False)
        logs = logs.station(self).on_air().filter(q).order_by('-date')

        # filter out tracks played when there was a diffusion
        n, q = 0, Q()
        for diff in diffs:
            if count and n >= count:
                break
            # FIXME: does not catch tracks started before diff end but
            #        that continued afterwards
            q = q | Q(date__gte=diff.start, date__lte=diff.end)
            n += 1
        logs = logs.exclude(q, diffusion__isnull=True)
        if count:
            logs = logs[:count]
        return logs

    def __str__(self):
        return self.name

    def save(self, make_sources=True, *args, **kwargs):
        if not self.path:
            self.path = os.path.join(
                settings.AIRCOX_CONTROLLERS_WORKING_DIR,
                self.slug
            )

        if self.default:
            qs = Station.objects.filter(default=True)

            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(default=False)

        super().save(*args, **kwargs)


class ProgramManager(models.Manager):
    def station(self, station, qs=None, **kwargs):
        qs = self if qs is None else qs

        return qs.filter(station=station, **kwargs)


class Program(models.Model):
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
    name = models.CharField(_('name'), max_length=64)
    slug = models.SlugField(_('slug'), max_length=64, unique=True)
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

    objects = ProgramManager()

    @property
    def path(self):
        """ Return program's directory path """
        return os.path.join(settings.AIRCOX_PROGRAMS_DIR, self.slug)

    def ensure_dir(self, subdir=None):
        """
        Make sur the program's dir exists (and optionally subdir). Return True
        if the dir (or subdir) exists.
        """
        path = os.path.join(self.path, subdir) if subdir else \
            self.path
        os.makedirs(path, exist_ok=True)

        return os.path.exists(path)

    @property
    def archives_path(self):
        return os.path.join(
            self.path, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR
        )

    @property
    def excerpts_path(self):
        return os.path.join(
            self.path, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR
        )

    def find_schedule(self, date):
        """
        Return the first schedule that matches a given date.
        """
        schedules = Schedule.objects.filter(program=self)

        for schedule in schedules:
            if schedule.match(date, check_time=False):
                return schedule

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

    def is_show(self):
        return self.schedule_set.count() != 0

    def __str__(self):
        return self.name

    def save(self, *kargs, **kwargs):
        super().save(*kargs, **kwargs)

        path_ = getattr(self, '__initial_path', None)
        if path_ is not None and path_ != self.path and \
                os.path.exists(path_) and not os.path.exists(self.path):
            logger.info('program #%s\'s dir changed to %s - update it.',
                        self.id, self.name)

            shutil.move(path_, self.path)
            Sound.objects.filter(path__startswith=path_) \
                 .update(path=Concat('path', Substr(F('path'), len(path_))))


class Stream(models.Model):
    """
    When there are no program scheduled, it is possible to play sounds
    in order to avoid blanks. A Stream is a Program that plays this role,
    and whose linked to a Stream.

    All sounds that are marked as good and that are under the related
    program's archive dir are elligible for the sound's selection.
    """
    program = models.ForeignKey(
        Program,
        verbose_name=_('related program'),
        on_delete=models.CASCADE,
    )
    delay = models.TimeField(
        _('delay'),
        blank=True, null=True,
        help_text=_('minimal delay between two sound plays')
    )
    begin = models.TimeField(
        _('begin'),
        blank=True, null=True,
        help_text=_('used to define a time range this stream is'
                    'played')
    )
    end = models.TimeField(
        _('end'),
        blank=True, null=True,
        help_text=_('used to define a time range this stream is'
                    'played')
    )


# BIG FIXME: self.date is still used as datetime
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

    program = models.ForeignKey(
        Program, models.CASCADE,
        verbose_name=_('related program'),
    )
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
            'every': _('{day}'),
            'one_on_two': _('one {day} on two'),
        }[x]) for x, y in Frequency.__members__.items()],
    )
    initial = models.ForeignKey(
        'self', models.SET_NULL,
        verbose_name=_('initial schedule'),
        blank=True, null=True,
        help_text=_('this schedule is a rerun of this one'),
    )

    @cached_property
    def tz(self):
        """
        Pytz timezone of the schedule.
        """
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
        """
        Return a list with all matching dates of date.month (=today)
        Ensure timezone awareness.

        :param datetime.date date: month and year
        """

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

    def diffusions_of_month(self, date=None, exclude_saved=False):
        """
        Return a list of Diffusion instances, from month of the given date, that
        can be not in the database.

        If exclude_saved, exclude all diffusions that are yet in the database.
        """

        if self.frequency == Schedule.Frequency.ponctual:
            return []

        dates = self.dates_of_month(date)
        diffusions = []

        # existing diffusions

        for item in Diffusion.objects.filter(
                program=self.program, start__in=dates):

            if item.start in dates:
                dates.remove(item.start)

            if not exclude_saved:
                diffusions.append(item)

        # new diffusions
        duration = utils.to_timedelta(self.duration)

        delta = None
        if self.initial:
            delta = self.start - self.initial.start

        # FIXME: daylight saving bug: delta misses an hour when diffusion and
        #        rerun are not on the same daylight-saving timezone
        #       -> solution: add rerun=True param, and gen reruns from initial for each
        diffusions += [
            Diffusion(
                program=self.program,
                type=Diffusion.Type.unconfirmed,
                initial=Diffusion.objects.program(self.program).filter(start=date-delta).first()
                if self.initial else None,
                start=date,
                end=date + duration,
            ) for date in dates
        ]

        return diffusions

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initial only if it has been yet saved

        if self.pk:
            self.__initial = self.__dict__.copy()

    def __str__(self):
        return ' | '.join(['#' + str(self.id), self.program.name,
                           self.get_frequency_display(),
                           self.time.strftime('%a %H:%M')])

    def save(self, *args, **kwargs):
        if self.initial:
            self.program = self.initial.program
            self.duration = self.initial.duration

            if not self.frequency:
                self.frequency = self.initial.frequency
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class DiffusionQuerySet(models.QuerySet):
    def station(self, station, **kwargs):
        return self.filter(program__station=station, **kwargs)

    def program(self, program):
        return self.filter(program=program)

    def on_air(self):
        return self.filter(type=Diffusion.Type.normal)

    def at(self, date=None):
        """
        Return diffusions occuring at the given date, ordered by +start

        If date is a datetime instance, get diffusions that occurs at
        the given moment. If date is not a datetime object, it uses
        it as a date, and get diffusions that occurs this day.

        When date is None, uses tz.now().
        """
        # note: we work with localtime
        date = utils.date_or_default(date)

        qs = self
        filters = None

        if isinstance(date, datetime.datetime):
            # use datetime: we want diffusion that occurs around this
            # range
            filters = {'start__lte': date, 'end__gte': date}
            qs = qs.filter(**filters)
        else:
            # use date: we want diffusions that occurs this day
            qs = qs.filter(Q(start__date=date) | Q(end__date=date))
        return qs.order_by('start').distinct()

    def after(self, date=None):
        """
        Return a queryset of diffusions that happen after the given
        date (default: today).
        """
        date = utils.date_or_default(date)
        if isinstance(date, tz.datetime):
            qs = self.filter(start__gte=date)
        else:
            qs = self.filter(start__date__gte=date)
        return qs.order_by('start')

    def before(self, date=None):
        """
        Return a queryset of diffusions that finish before the given
        date (default: today).
        """
        date = utils.date_or_default(date)
        if isinstance(date, tz.datetime):
            qs = self.filter(start__lt=date)
        else:
            qs = self.filter(start__date__lt=date)
        return qs.order_by('start')

    def range(self, start, end):
        # FIXME can return dates that are out of range...
        return self.after(start).before(end)


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
    objects = DiffusionQuerySet.as_manager()

    class Type(IntEnum):
        normal = 0x00
        unconfirmed = 0x01
        canceled = 0x02

    # common
    program = models.ForeignKey(
        Program,
        verbose_name=_('program'),
        on_delete=models.CASCADE,
    )
    # specific
    type = models.SmallIntegerField(
        verbose_name=_('type'),
        choices=[(int(y), _(x)) for x, y in Type.__members__.items()],
    )
    initial = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='reruns',
        verbose_name=_('initial diffusion'),
        help_text=_('the diffusion is a rerun of this one')
    )
    # port = models.ForeignKey(
    #    'self',
    #    verbose_name = _('port'),
    #    blank = True, null = True,
    #    on_delete=models.SET_NULL,
    #    help_text = _('use this input port'),
    # )
    conflicts = models.ManyToManyField(
        'self',
        verbose_name=_('conflicts'),
        blank=True,
        help_text=_('conflicts'),
    )

    start = models.DateTimeField(_('start of the diffusion'))
    end = models.DateTimeField(_('end of the diffusion'))

    @property
    def duration(self):
        return self.end - self.start

    @property
    def date(self):
        """ Return diffusion start as a date. """

        return utils.cast_date(self.start)

    @cached_property
    def local_start(self):
        """
        Return a version of self.date that is localized to self.timezone;
        This is needed since datetime are stored as UTC date and we want
        to get it as local time.
        """

        return tz.localtime(self.start, tz.get_current_timezone())

    @property
    def local_end(self):
        """
        Return a version of self.date that is localized to self.timezone;
        This is needed since datetime are stored as UTC date and we want
        to get it as local time.
        """

        return tz.localtime(self.end, tz.get_current_timezone())

    @property
    def original(self):
        """ Return the original diffusion (self or initial) """

        return self.initial if self.initial else self

    def is_live(self):
        """
        True if Diffusion is live (False if there are sounds files)
        """

        return self.type == self.Type.normal and \
            not self.get_sounds(archive=True).count()

    def get_playlist(self, **types):
        """
        Returns sounds as a playlist (list of *local* archive file path).
        The given arguments are passed to ``get_sounds``.
        """

        return list(self.get_sounds(**types)
                        .filter(path__isnull=False,
                                type=Sound.Type.archive)
                        .values_list('path', flat=True))

    def get_sounds(self, **types):
        """
        Return a queryset of sounds related to this diffusion,
        ordered by type then path.

        **types: filter on the given sound types name, as `archive=True`
        """
        sounds = (self.initial or self).sound_set.order_by('type', 'path')
        _in = [getattr(Sound.Type, name)
               for name, value in types.items() if value]

        return sounds.filter(type__in=_in)

    def is_date_in_range(self, date=None):
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

        return Diffusion.objects.filter(
            Q(start__lt=self.start, end__gt=self.start) |
            Q(start__gt=self.start, start__lt=self.end)
        ).exclude(pk=self.pk).distinct()

    def check_conflicts(self):
        conflicts = self.get_conflicts()
        self.conflicts.set(conflicts)

    __initial = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial = {
            'start': self.start,
            'end': self.end,
        }

    def save(self, no_check=False, *args, **kwargs):
        if no_check:
            return super().save(*args, **kwargs)

        if self.initial:
            # enforce link to the original diffusion
            self.initial = self.initial.original
            self.program = self.initial.program

        super().save(*args, **kwargs)

        if self.__initial:
            if self.start != self.__initial['start'] or \
                    self.end != self.__initial['end']:
                self.check_conflicts()

    def __str__(self):
        str_ = '{self.program.name} {date}'.format(
            self=self, date=self.local_start.strftime('%Y/%m/%d %H:%M%z'),
        )
        if self.initial:
            str_ += ' ({})'.format(_('rerun'))
        return str_

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')
        permissions = (
            ('programming', _('edit the diffusion\'s planification')),
        )


class SoundQuerySet(models.QuerySet):
    def podcasts(self):
        """ Return sound available as podcasts """
        return self.filter(Q(embed__isnull=False) | Q(is_public=True))

    def diffusion(self, diffusion):
        return self.filter(diffusion=diffusion)


class Sound(models.Model):
    """
    A Sound is the representation of a sound file that can be either an excerpt
    or a complete archive of the related diffusion.
    """
    class Type(IntEnum):
        other = 0x00,
        archive = 0x01,
        excerpt = 0x02,
        removed = 0x03,

    name = models.CharField(_('name'), max_length=64)
    program = models.ForeignKey(
        Program,
        verbose_name=_('program'),
        blank=True, null=True,
        on_delete=models.SET_NULL,
        help_text=_('program related to it'),
    )
    diffusion = models.ForeignKey(
        Diffusion, models.SET_NULL,
        verbose_name=_('diffusion'),
        blank=True, null=True,
        limit_choices_to={'initial__isnull': True},
        help_text=_('initial diffusion related it')
    )
    type = models.SmallIntegerField(
        verbose_name=_('type'),
        choices=[(int(y), _(x)) for x, y in Type.__members__.items()],
        blank=True, null=True
    )
    # FIXME: url() does not use the same directory than here
    #        should we use FileField for more reliability?
    path = models.FilePathField(
        _('file'),
        path=settings.AIRCOX_PROGRAMS_DIR,
        match=r'(' + '|'.join(settings.AIRCOX_SOUND_FILE_EXT)
        .replace('.', r'\.') + ')$',
        recursive=True,
        blank=True, null=True,
        unique=True,
        max_length=255
    )
    embed = models.TextField(
        _('embed HTML code'),
        blank=True, null=True,
        help_text=_('HTML code used to embed a sound from external plateform'),
    )
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
        _('good quality'),
        help_text=_('sound meets quality requirements for diffusion'),
        blank=True, null=True
    )
    is_public = models.BooleanField(
        _('public'),
        default=False,
        help_text=_('the sound is accessible to the public')
    )

    objects = SoundQuerySet.as_manager()

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

    def file_metadata(self):
        """
        Get metadata from sound file and return a Track object if succeed,
        else None.
        """
        if not self.file_exists():
            return None

        import mutagen
        try:
            meta = mutagen.File(self.path)
        except:
            meta = {}

        if meta is None:
            meta = {}

        def get_meta(key, cast=str):
            value = meta.get(key)
            return cast(value[0]) if value else None

        info = '{} ({})'.format(get_meta('album'), get_meta('year')) \
            if meta and ('album' and 'year' in meta) else \
               get_meta('album') \
            if 'album' else \
               ('year' in meta) and get_meta('year') or ''

        return Track(sound=self,
                     position=get_meta('tracknumber', int) or 0,
                     title=get_meta('title') or self.name,
                     artist=get_meta('artist') or _('unknown'),
                     info=info)

    def check_on_file(self):
        """
        Check sound file info again'st self, and update informations if
        needed (do not save). Return True if there was changes.
        """

        if not self.file_exists():
            if self.type == self.Type.removed:
                return
            logger.info('sound %s: has been removed', self.path)
            self.type = self.Type.removed

            return True

        # not anymore removed
        changed = False

        if self.type == self.Type.removed and self.program:
            changed = True
            self.type = self.Type.archive \
                if self.path.startswith(self.program.archives_path) else \
                self.Type.excerpt

        # check mtime -> reset quality if changed (assume file changed)
        mtime = self.get_mtime()

        if self.mtime != mtime:
            self.mtime = mtime
            self.is_good_quality = None
            logger.info('sound %s: m_time has changed. Reset quality info',
                        self.path)

            return True

        return changed

    def check_perms(self):
        """
        Check file permissions and update it if the sound is public
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

    def save(self, check=True, *args, **kwargs):
        if check:
            self.check_on_file()
        self.__check_name()
        super().save(*args, **kwargs)

    def __str__(self):
        return '/'.join(self.path.split('/')[-3:])

    class Meta:
        verbose_name = _('Sound')
        verbose_name_plural = _('Sounds')


class Track(models.Model):
    """
    Track of a playlist of an object. The position can either be expressed
    as the position in the playlist or as the moment in seconds it started.
    """
    diffusion = models.ForeignKey(
        Diffusion, models.CASCADE, blank=True, null=True,
        verbose_name=_('diffusion'),
    )
    sound = models.ForeignKey(
        Sound, models.CASCADE, blank=True, null=True,
        verbose_name=_('sound'),
    )
    position = models.PositiveSmallIntegerField(
        _('order'),
        default=0,
        help_text=_('position in the playlist'),
    )
    timestamp = models.PositiveSmallIntegerField(
        _('timestamp'),
        blank=True, null=True,
        help_text=_('position in seconds')
    )
    title = models.CharField(
        _('title'),
        max_length=128,
    )
    artist = models.CharField(
        _('artist'),
        max_length=128,
    )
    tags = TaggableManager(
        verbose_name=_('tags'),
        blank=True,
    )
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
        if (self.sound is None and self.diffusion is None) or \
                (self.sound is not None and self.diffusion is not None):
            raise ValueError('sound XOR diffusion is required')
        super().save(*args, **kwargs)

#
# Controls and audio input/output
#
class Port (models.Model):
    """
    Represent an audio input/output for the audio stream
    generation.

    You might want to take a look to LiquidSoap's documentation
    for the options available for each kind of input/output.

    Some port types may be not available depending on the
    direction of the port.
    """
    class Direction(IntEnum):
        input = 0x00
        output = 0x01

    class Type(IntEnum):
        jack = 0x00
        alsa = 0x01
        pulseaudio = 0x02
        icecast = 0x03
        http = 0x04
        https = 0x05
        file = 0x06

    station = models.ForeignKey(
        Station,
        verbose_name=_('station'),
        on_delete=models.CASCADE,
    )
    direction = models.SmallIntegerField(
        _('direction'),
        choices=[(int(y), _(x)) for x, y in Direction.__members__.items()],
    )
    type = models.SmallIntegerField(
        _('type'),
        # we don't translate the names since it is project names.
        choices=[(int(y), x) for x, y in Type.__members__.items()],
    )
    active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('this port is active')
    )
    settings = models.TextField(
        _('port settings'),
        help_text=_('list of comma separated params available; '
                    'this is put in the output config file as raw code; '
                    'plugin related'),
        blank=True, null=True
    )

    def is_valid_type(self):
        """
        Return True if the type is available for the given direction.
        """

        if self.direction == self.Direction.input:
            return self.type not in (
                self.Type.icecast, self.Type.file
            )

        return self.type not in (
            self.Type.http, self.Type.https
        )

    def save(self, *args, **kwargs):
        if not self.is_valid_type():
            raise ValueError(
                "port type is not allowed with the given port direction"
            )

        return super().save(*args, **kwargs)

    def __str__(self):
        return "{direction}: {type} #{id}".format(
            direction=self.get_direction_display(),
            type=self.get_type_display(),
            id=self.pk or ''
        )


class LogQuerySet(models.QuerySet):
    def station(self, station):
        return self.filter(station=station)

    def at(self, date=None):
        date = utils.date_or_default(date)
        return self.filter(date__date=date)

    def on_air(self):
        return self.filter(type=Log.Type.on_air)

    def start(self):
        return self.filter(type=Log.Type.start)

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
                attr_id = attr + '_id'
                rel_id = log.get(attr + '_id')

                return rels[attr][rel_id] if rel_id else None

            # make logs

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

        qs = self.station(station).at(date)

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
    class Type(IntEnum):
        stop = 0x00
        """
        Source has been stopped, e.g. manually
        """
        start = 0x01
        """
        The diffusion or sound has been triggered by the streamer or
        manually.
        """
        load = 0x02
        """
        A playlist has updated, and loading started. A related Diffusion
        does not means that the playlist is only for it (e.g. after a
        crash, it can reload previous remaining sound files + thoses of
        the next diffusion)
        """
        on_air = 0x03
        """
        The sound or diffusion has been detected occurring on air. Can
        also designate live diffusion, although Liquidsoap did not play
        them since they don't have an attached sound archive.
        """
        other = 0x04
        """
        Other log
        """

    type = models.SmallIntegerField(
        choices=[(int(y), _(x.replace('_', ' ')))
                 for x, y in Type.__members__.items()],
        blank=True, null=True,
        verbose_name=_('type'),
    )
    station = models.ForeignKey(
        Station, on_delete=models.CASCADE,
        verbose_name=_('station'),
        help_text=_('related station'),
    )
    source = models.CharField(
        # we use a CharField to avoid loosing logs information if the
        # source is removed
        max_length=64, blank=True, null=True,
        verbose_name=_('source'),
        help_text=_('identifier of the source related to this log'),
    )
    date = models.DateTimeField(
        default=tz.now, db_index=True,
        verbose_name=_('date'),
    )
    comment = models.CharField(
        max_length=512, blank=True, null=True,
        verbose_name=_('comment'),
    )

    diffusion = models.ForeignKey(
        Diffusion, on_delete=models.SET_NULL,
        blank=True, null=True, db_index=True,
        verbose_name=_('Diffusion'),
    )
    sound = models.ForeignKey(
        Sound, on_delete=models.SET_NULL,
        blank=True, null=True, db_index=True,
        verbose_name=_('Sound'),
    )
    track = models.ForeignKey(
        Track, on_delete=models.SET_NULL,
        blank=True, null=True, db_index=True,
        verbose_name=_('Track'),
    )

    collision = models.ForeignKey(
        Diffusion, on_delete=models.SET_NULL,
        blank=True, null=True,
        verbose_name=_('Collision'),
        related_name='+',
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

    def __str__(self):
        return '#{} ({}, {}, {})'.format(
            self.pk, self.get_type_display(),
            self.source,
            self.local_date.strftime('%Y/%m/%d %H:%M%z'),
        )

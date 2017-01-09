import datetime
import calendar
import os
import shutil
import logging
from enum import IntEnum

from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.html import strip_tags
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings as main_settings

from taggit.managers import TaggableManager

import aircox.utils as utils
import aircox.settings as settings


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


#
# Abstracts
#
class RelatedManager(models.Manager):
    def get_for(self, object = None, model = None):
        """
        Return a queryset that filter on the given object or model(s)

        * object: if given, use its type and pk; match on models only.
        * model: one model or an iterable of models
        """
        if not model and object:
            model = type(object)

        if hasattr(model, '__iter__'):
            model = [ ContentType.objects.get_for_model(m).id
                        for m in model ]
            qs = self.filter(related_type__pk__in = model)
        else:
            model = ContentType.objects.get_for_model(model)
            qs = self.filter(related_type__pk = model.id)
        if object:
            qs = qs.filter(related_id = object.pk)
        return qs


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

    objects = RelatedManager()

    @classmethod
    def ReverseField(cl):
        """
        Return a GenericRelation object that points to this class
        """
        return GenericRelation(cl, 'related_id', 'related_type')

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


#
# Small common models
#
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


#
# Station related classes
#
class Station(Nameable):
    """
    Represents a radio station, to which multiple programs are attached
    and that is used as the top object for everything.

    A Station holds controllers for the audio stream generation too.
    Theses are set up when needed (at the first access to these elements)
    then cached.
    """
    path = models.CharField(
        _('path'),
        help_text = _('path to the working directory'),
        max_length = 256,
        blank = True,
    )

    #
    # Controllers
    #
    __sources = None
    __dealer = None
    __streamer = None

    def __prepare(self):
        import aircox.controllers as controllers
        if not self.__streamer:
            self.__streamer = controllers.Streamer(station = self)
            self.__dealer = controllers.Source(station = self)
            self.__sources = [ self.__dealer ] + [
                controllers.Source(station = self, program = program)
                for program in Program.objects.filter(stream__isnull = False)
            ]

    @property
    def inputs(self):
        """
        Return all active input ports of the station
        """
        return self.port_set.filter(
            direction = Port.Direction.input,
            active = True
        )

    @property
    def outputs(self):
        """
        Return all active output ports of the station
        """
        return self.port_set.filter(
            direction = Port.Direction.output,
            active = True,
        )

    @property
    def sources(self):
        """
        Audio sources, dealer included
        """
        self.__prepare()
        return self.__sources

    @property
    def dealer(self):
        self.__prepare()
        return self.__dealer

    @property
    def streamer(self):
        """
        Audio controller for the station
        """
        self.__prepare()
        return self.__streamer

    def get_played(self, models, archives = True):
        """
        Return a queryset with log of played elements on this station,
        of the given models, ordered by date ascending.

        * models: a model or a list of models
        * archives: if false, exclude log of diffusion's archives from
            the queryset;
        """
        qs = Log.objects.get_for(model = models) \
                .filter(station = self, type = Log.Type.play)
        if not archives and self.dealer:
            qs = qs.exclude(
                source = self.dealer.id,
                related_type = ContentType.objects.get_for_model(Sound)
            )
        return qs.order_by('date')

    @staticmethod
    def __mix_logs_and_diff(diffs, logs, count = 0):
        """
        Mix together logs and diffusion items of the same day,
        ordered by their date.

        Diffs and Logs are assumed to be ordered by -date, and so is
        the resulting list
        """
        # we fill a list with diff and retrieve logs that happened between
        # each to put them too there.
        # we do the algorithm in the reverse way in order to be able to limit
        # process calculations using count if needed.
        diff_ = None
        now = tz.now()
        items = []

        logs = logs.order_by('-date')
        for diff in diffs.order_by('-start'):
            if diff_:
                logs_ = logs.filter(date__gt = diff.end, date__lt = diff_.start)
            else:
                logs_ = logs.filter(date__gt = diff.end)

            if diff.end < now:
                # a log can be started before the end of the diffusion and still
                # is running. We can't say if it has been properly finished
                # before the end of the diffusion, but we assume that in most
                # cases this is true.
                # We just check if there is some other log after this partial
                # one.
                partial = logs.filter(
                    date__gt = diff.start, date__lt = diff.end
                )
                if partial:
                    next_log = logs.filter(pk__gt = partial.pk).first()
                    if not next_log or next_log.date > diff.end:
                        partial.date = diff.end
                        logs_ = list(logs_[:count]) + [partial]

            # append to list
            diff_ = diff
            items.extend(logs_)
            items.append(diff)
            if count and len(items) >= count:
                break

        if diff_:
            if count and len(items) >= count:
                return items[:count]
            logs_ = logs.filter(date__lt = diff_.start)
        else:
            logs_ = logs.all()

        items.extend(logs_)
        return items[:count] if count else items

    def on_air(self, date = None, count = 0):
        """
        Return a list of what happened on air, based on logs and
        diffusions informations. The list is sorted by -date.

        * date: only for what happened on this date;
        * count: number of items to retrieve if not zero;

        If date is not specified, count MUST be set to a non-zero value.
        Be careful with what you which for: the result is a plain list.

        The list contains:
        * track logs: for the streamed programs;
        * diffusion: for the scheduled diffusions;
        """
        # FIXME: as an iterator?
        # TODO argument to get sound instead of tracks
        if not date and not count:
            raise ValueError('at least one argument must be set')

        if date and date > datetime.date.today():
            return []

        logs = Log.objects.get_for(model = Track) \
                  .filter(station = self)
        if date:
            logs = logs.filter(date__contains = date)
            diffs = Diffusion.objects.get_at(date)
        else:
            diffs = Diffusion.objects

        diffs = diffs.filter(program__station = self) \
                     .filter(type = Diffusion.Type.normal) \
                     .filter(start__lte = tz.now())
        return self.__mix_logs_and_diff(diffs, logs, count)

    def save(self, make_sources = True, *args, **kwargs):
        if not self.path:
            self.path = os.path.join(
                settings.AIRCOX_CONTROLLERS_WORKING_DIR,
                self.slug
            )

        super().save(*args, **kwargs)


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
    station = models.ForeignKey(
        Station,
        verbose_name = _('station'),
    )
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('if not checked this program is no longer active')
    )
    sync = models.BooleanField(
        _('syncronise'),
        default = True,
        help_text = _('update later diffusions according to schedule changes')
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

    def is_show(self):
        return self.schedule_set.count() != 0


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
        Program,
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
                'ponctual': _('ponctual'),
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

    # initial cached data
    __initial = None

    def changed(self, fields = ['date','duration','frequency']):
        initial = self._Schedule__initial
        if not initial:
            return

        before, now = self.__initial, self.__dict__
        before, now = {
            f: getattr(before, f) for f in fields
            if hasattr(before, f)
        }, {
            f: getattr(now, f) for f in fields
            if hasattr(now, f)
        }
        return before == now

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
        if self.frequency == Schedule.Frequency.ponctual:
            return False

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
        if self.frequency == Schedule.Frequency.ponctual:
            return []

        date = date_or_default(date, True).replace(day=1)
        freq = self.frequency

        # last of the month
        if freq == Schedule.Frequency.last:
            date = date.replace(day=calendar.monthrange(date.year, date.month)[1])

            # end of month before the wanted weekday: move one week back
            if date.weekday() < self.date.weekday():
                date -= datetime.timedelta(days = 7)

            delta = self.date.weekday() - date.weekday()
            date += datetime.timedelta(days = delta)
            return [self.normalize(date)]

        # move to the first day of the month that matches the schedule's weekday
        # check on SO#3284452 for the formula
        first_weekday = date.weekday()
        sched_weekday = self.date.weekday()
        date += tz.timedelta(days = (7 if first_weekday > sched_weekday else 0) \
                                    - first_weekday + sched_weekday)
        month = date.month

        dates = []
        if freq == Schedule.Frequency.one_on_two:
            # check date base on a diff of dates base on a 14 days delta
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
        if self.frequency == Schedule.Frequency.ponctual:
            return []

        dates = self.dates_of_month(date)
        diffusions = []

        # existing diffusions
        for item in Diffusion.objects.filter(
                program = self.program, start__in = dates):
            if item.start in dates:
                dates.remove(item.start)
            if not exclude_saved:
                diffusions.append(item)

        # new diffusions
        duration = utils.to_timedelta(self.duration)
        if self.initial:
            delta = self.date - self.initial.date
        diffusions += [
            Diffusion(
                program = self.program,
                type = Diffusion.Type.unconfirmed,
                initial = \
                    Diffusion.objects.filter(start = date - delta).first() \
                        if self.initial else None,
                start = date,
                end = date + duration,
            ) for date in dates
        ]
        return diffusions

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial = self.__dict__.copy()

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


class DiffusionManager(models.Manager):
    def get_at(self, date = None, next = False):
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

        if not next:
            return self.filter(start__lte = date, end__gte = date) \
                       .order_by('start')

        return self.filter(
            models.Q(start__lte = date, end__gte = date) |
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
        Program,
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
    # port = models.ForeignKey(
    #    'self',
    #    verbose_name = _('port'),
    #    blank = True, null = True,
    #    help_text = _('use this input port'),
    # )

    start = models.DateTimeField( _('start of the diffusion') )
    end = models.DateTimeField( _('end of the diffusion') )

    tracks = Track.ReverseField()

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
        return sounds.filter(type = Sound.Type.archive).order_by('path')

    def get_excerpts(self):
        """
        Return a list of available archives sounds for the given episode,
        ordered by path.
        """
        sounds = self.initial.sound_set if self.initial else self.sound_set
        return sounds.filter(type = Sound.Type.excerpt).order_by('path')

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


class Sound(Nameable):
    """
    A Sound is the representation of a sound file that can be either an excerpt
    or a complete archive of the related diffusion.
    """
    class Type(IntEnum):
        other = 0x00,
        archive = 0x01,
        excerpt = 0x02,
        removed = 0x03,

    program = models.ForeignKey(
        Program,
        verbose_name = _('program'),
        blank = True, null = True,
        help_text = _('program related to it'),
    )
    diffusion = models.ForeignKey(
        'Diffusion',
        verbose_name = _('diffusion'),
        blank = True, null = True,
        help_text = _('initial diffusion related it')
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
    good_quality = models.NullBooleanField(
        _('good quality'),
        help_text = _('sound\'s quality is okay'),
        blank = True, null = True
    )
    public = models.BooleanField(
        _('public'),
        default = False,
        help_text = _('the sound is accessible to the public')
    )

    tracks = Track.ReverseField()

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

        track = Track(
            related = self,
            title = get_meta('title') or self.name,
            artist = get_meta('artist') or _('unknown'),
            info = info,
            position = get_meta('tracknumber', int) or 0,
        )
        return track

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
            self.good_quality = None
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
        verbose_name = _('station'),
    )
    direction = models.SmallIntegerField(
        _('direction'),
        choices = [ (int(y), _(x)) for x,y in Direction.__members__.items() ],
    )
    type = models.SmallIntegerField(
        _('type'),
        # we don't translate the names since it is project names.
        choices = [ (int(y), x) for x,y in Type.__members__.items() ],
    )
    active = models.BooleanField(
        _('active'),
        default = True,
        help_text = _('this port is active')
    )
    settings = models.TextField(
        _('port settings'),
        help_text = _('list of comma separated params available; '
                      'this is put in the output config file as raw code; '
                      'plugin related'),
        blank = True, null = True
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
            direction = self.get_direction_display(),
            type = self.get_type_display(),
            id = self.pk or ''
        )


class Log(Related):
    """
    Log sounds and diffusions that are played on the station.

    This only remember what has been played on the outputs, not on each
    source; Source designate here which source is responsible of that.
    """
    class Type(IntEnum):
        stop = 0x00
        """
        Source has been stopped (only when there is no more sound)
        """
        play = 0x01
        """
        Source has been started/changed and is running related_object
        If no related_object is available, comment is used to designate
        the sound.
        """
        load = 0x02
        """
        Source starts to be preload related_object
        """
        other = 0x03
        """
        Other log
        """

    type = models.SmallIntegerField(
        verbose_name = _('type'),
        choices = [ (int(y), _(x)) for x,y in Type.__members__.items() ],
        blank = True, null = True,
    )
    station = models.ForeignKey(
        Station,
        verbose_name = _('station'),
        help_text = _('station on which the event occured'),
    )
    source = models.CharField(
        # we use a CharField to avoid loosing logs information if the
        # source is removed
        _('source'),
        max_length=64,
        help_text = _('source id that make it happen on the station'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        default=tz.now,
    )
    comment = models.CharField(
        _('comment'),
        max_length = 512,
        blank = True, null = True,
    )

    @property
    def end(self):
        """
        Calculated end using self.related informations
        """
        if self.related_type == Diffusion:
            return self.related.end
        if self.related_type == Sound:
            return self.date + to_timedelta(self.duration)
        return self.date

    def is_expired(self, date = None):
        """
        Return True if the log is expired. Note that it only check
        against the date, so it is still possible that the expiration
        occured because of a Stop or other source.
        """
        date = date_or_default(date)
        return self.end < date

    def print(self):
        logger.info('log #%s: %s%s',
            str(self),
            self.comment or '',
            ' -- {} #{}'.format(self.related_type, self.related_id)
                if self.related else ''
        )

    def __str__(self):
        return '#{} ({}, {})'.format(
                self.pk, self.date.strftime('%Y/%m/%d %H:%M'), self.source
        )




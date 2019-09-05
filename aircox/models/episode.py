import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property


from aircox import settings, utils
from .program import Program, InProgramQuerySet, \
        BaseRerun, BaseRerunQuerySet
from .page import Page, PageQuerySet


__all__ = ['Episode', 'Diffusion', 'DiffusionQuerySet']


class EpisodeQuerySet(PageQuerySet, InProgramQuerySet):
    pass


class Episode(Page):
    program = models.ForeignKey(
        Program, models.CASCADE,
        verbose_name=_('program'),
    )

    objects = EpisodeQuerySet.as_manager()
    detail_url_name = 'episode-detail'

    class Meta:
        verbose_name = _('Episode')
        verbose_name_plural = _('Episodes')

    def get_absolute_url(self):
        if not self.is_published:
            return self.program.get_absolute_url()
        return super().get_absolute_url()

    def save(self, *args, **kwargs):
        if self.cover is None:
            self.cover = self.program.cover
        super().save(*args, **kwargs)

    @classmethod
    def get_init_kwargs_from(cls, page, date, title=None, **kwargs):
        """ Get default Episode's title  """
        title = settings.AIRCOX_EPISODE_TITLE.format(
            program=page,
            date=date.strftime(settings.AIRCOX_EPISODE_TITLE_DATE_FORMAT),
        ) if title is None else title
        return super().get_init_kwargs_from(page, title=title, program=page,
                                            **kwargs)


class DiffusionQuerySet(BaseRerunQuerySet):
    def episode(self, episode=None, id=None):
        """ Diffusions for this episode """
        return self.filter(episode=episode) if id is None else \
               self.filter(episode__id=id)

    def on_air(self):
        """ On air diffusions """
        return self.filter(type=Diffusion.TYPE_ON_AIR)

    def now(self, now=None, order=True):
        """ Diffusions occuring now """
        now = now or tz.now()
        qs = self.filter(start__lte=now, end__gte=now).distinct()
        return qs.order_by('start') if order else qs

    def today(self, today=None, order=True):
        """ Diffusions occuring today. """
        today = today or datetime.date.today()
        qs = self.filter(Q(start__date=today) | Q(end__date=today))
        return qs.order_by('start') if order else qs

    def at(self, date, order=True):
        """ Return diffusions at specified date or datetime """
        return self.now(date, order) if isinstance(date, tz.datetime) else \
            self.today(date, order)

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


class Diffusion(BaseRerun):
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

    TYPE_ON_AIR = 0x00
    TYPE_UNCONFIRMED = 0x01
    TYPE_CANCEL = 0x02
    TYPE_CHOICES = (
        (TYPE_ON_AIR, _('on air')),
        (TYPE_UNCONFIRMED, _('not confirmed')),
        (TYPE_CANCEL, _('cancelled')),
    )

    episode = models.ForeignKey(
        Episode, models.CASCADE, verbose_name=_('episode'),
    )
    type = models.SmallIntegerField(
        verbose_name=_('type'), default=TYPE_ON_AIR, choices=TYPE_CHOICES,
    )
    start = models.DateTimeField(_('start'))
    end = models.DateTimeField(_('end'))
    # port = models.ForeignKey(
    #    'self',
    #    verbose_name = _('port'),
    #    blank = True, null = True,
    #    on_delete=models.SET_NULL,
    #    help_text = _('use this input port'),
    # )

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')
        permissions = (
            ('programming', _('edit the diffusion\'s planification')),
        )

    def __str__(self):
        str_ = '{episode} - {date}'.format(
            self=self, episode=self.episode and self.episode.title,
            date=self.local_start.strftime('%Y/%m/%d %H:%M%z'),
        )
        if self.initial:
            str_ += ' ({})'.format(_('rerun'))
        return str_

    #def save(self, no_check=False, *args, **kwargs):
        #if self.start != self._initial['start'] or \
        #        self.end != self._initial['end']:
        #    self.check_conflicts()

    def save_rerun(self):
        print('rerun save', self)
        self.episode = self.initial.episode
        self.program = self.episode.program

    def save_initial(self):
        print('initial save', self)
        self.program = self.episode.program
        if self.episode != self._initial['episode']:
            self.rerun_set.update(episode=self.episode, program=self.program)

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

    # TODO: property?
    def is_live(self):
        """ True if Diffusion is live (False if there are sounds files). """
        return self.type == self.TYPE_ON_AIR and \
            not self.episode.sound_set.archive().count()

    def get_playlist(self, **types):
        """
        Returns sounds as a playlist (list of *local* archive file path).
        The given arguments are passed to ``get_sounds``.
        """
        from .sound import Sound
        return list(self.get_sounds(**types)
                        .filter(path__isnull=False, type=Sound.TYPE_ARCHIVE)
                        .values_list('path', flat=True))

    def get_sounds(self, **types):
        """
        Return a queryset of sounds related to this diffusion,
        ordered by type then path.

        **types: filter on the given sound types name, as `archive=True`
        """
        from .sound import Sound
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
        """ Return conflicting diffusions queryset """

        # conflicts=Diffusion.objects.filter(Q(start__lt=OuterRef('start'), end__gt=OuterRef('end')) | Q(start__gt=OuterRef('start'), start__lt=OuterRef('end')))
        # diffs= Diffusion.objects.annotate(conflict_with=Exists(conflicts)).filter(conflict_with=True)
        return Diffusion.objects.filter(
            Q(start__lt=self.start, end__gt=self.start) |
            Q(start__gt=self.start, start__lt=self.end)
        ).exclude(pk=self.pk).distinct()

    def check_conflicts(self):
        conflicts = self.get_conflicts()
        self.conflicts.set(conflicts)

    _initial = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial = {
            'start': self.start,
            'end': self.end,
            'episode': getattr(self, 'episode', None),
        }



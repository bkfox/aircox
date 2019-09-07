from collections import OrderedDict
import datetime

from django.views.generic import ListView
from django.utils.translation import ugettext as _

from ..models import Diffusion, Episode, Program, Sound
from .base import BaseView
from .program import ProgramPageDetailView
from .page import PageListView
from .mixins import GetDateMixin, ParentMixin


__all__ = ['EpisodeDetailView', 'EpisodeListView', 'DiffusionListView']


class EpisodeDetailView(ProgramPageDetailView):
    model = Episode

    def get_podcasts(self, diffusion):
        return Sound.objects.diffusion(diffusion).podcasts()

    def get_context_data(self, **kwargs):
        self.program = kwargs.setdefault('program', self.object.program)

        kwargs.setdefault('parent', self.program)
        if not 'tracks' in kwargs:
            kwargs['tracks'] = self.object.track_set.order_by('position')
        if not 'podcasts' in kwargs:
            kwargs['podcasts'] = self.object.sound_set.podcasts()
        return super().get_context_data(**kwargs)


class EpisodeListView(ParentMixin, PageListView):
    model = Episode
    item_template_name = 'aircox/episode_item.html'
    show_headline = True

    parent_model = Program
    fk_parent = 'program'


class DiffusionListView(GetDateMixin, BaseView, ListView):
    """ View for timetables """
    model = Diffusion

    date = None
    start = None
    end = None

    def get_date(self):
        date = super().get_date()
        return date if date is not None else datetime.date.today()

    def get_queryset(self):
        return super().get_queryset().today(self.date).order_by('start')

    def get_context_data(self, **kwargs):
        today = datetime.date.today()
        start = self.date - datetime.timedelta(days=self.date.weekday())
        dates = [
            (today, None),
            (today - datetime.timedelta(days=1), None),
            (today + datetime.timedelta(days=1), None),
            (today - datetime.timedelta(days=7), _('next week')),
            (today + datetime.timedelta(days=7), _('last week')),
            (None, None)
        ] + [
            (date, date.strftime('%A %d'))
            for date in (start + datetime.timedelta(days=i)
                         for i in range(0, 7)) if date != today
        ]
        return super().get_context_data(date=self.date, dates=dates, **kwargs)


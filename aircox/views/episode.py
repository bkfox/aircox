from collections import OrderedDict
import datetime

from django.views.generic import ListView

from ..models import Diffusion, Episode, Program, StaticPage, Sound
from .base import BaseView
from .program import ProgramPageDetailView
from .page import PageListView
from .mixins import AttachedToMixin, GetDateMixin, ParentMixin


__all__ = ['EpisodeDetailView', 'EpisodeListView', 'DiffusionListView', 'SoundListView']


class EpisodeDetailView(ProgramPageDetailView):
    model = Episode

    def get_context_data(self, **kwargs):
        if not 'tracks' in kwargs:
            kwargs['tracks'] = self.object.track_set.order_by('position')
        return super().get_context_data(**kwargs)


class EpisodeListView(PageListView):
    model = Episode
    item_template_name = 'aircox/widgets/episode_item.html'
    has_headline = True
    parent_model = Program
    attach_to_value = StaticPage.ATTACH_TO_EPISODES


class DiffusionListView(GetDateMixin, AttachedToMixin, BaseView, ListView):
    """ View for timetables """
    model = Diffusion
    has_filters = True
    redirect_date_url = 'diffusion-list'
    attach_to_value = StaticPage.ATTACH_TO_DIFFUSIONS

    def get_date(self):
        date = super().get_date()
        return date if date is not None else datetime.date.today()

    def get_queryset(self):
        return super().get_queryset().date(self.date).order_by('start')

    def get_context_data(self, **kwargs):
        start = self.date - datetime.timedelta(days=self.date.weekday())
        dates = [start + datetime.timedelta(days=i) for i in range(0, 7)]
        return super().get_context_data(date=self.date, dates=dates, **kwargs)


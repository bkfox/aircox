from collections import OrderedDict
import datetime

from django.views.generic import ListView
from django.utils.translation import gettext as _

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
        if not 'tracks' in kwargs:
            kwargs['tracks'] = self.object.track_set.order_by('position')
        if not 'podcasts' in kwargs:
            kwargs['podcasts'] = self.object.sound_set.podcasts()
        return super().get_context_data(**kwargs)


class EpisodeListView(ParentMixin, PageListView):
    model = Episode
    item_template_name = 'aircox/widgets/episode_item.html'
    has_headline = True
    parent_model = Program


class DiffusionListView(GetDateMixin, BaseView, ListView):
    """ View for timetables """
    model = Diffusion
    has_filters = True
    redirect_date_url = 'diffusion-list'

    def get_date(self):
        date = super().get_date()
        return date if date is not None else datetime.date.today()

    def get_queryset(self):
        return super().get_queryset().today(self.date).order_by('start')

    def get_context_data(self, **kwargs):
        start = self.date - datetime.timedelta(days=self.date.weekday())
        dates = [start + datetime.timedelta(days=i) for i in range(0, 7)]
        return super().get_context_data(date=self.date, dates=dates, **kwargs)


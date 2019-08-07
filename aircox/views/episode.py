from collections import OrderedDict
import datetime

from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from ..models import Diffusion, Episode, Page, Program, Sound
from .base import BaseView
from .page import PageListView
from .program import ProgramPageDetailView


__all__ = ['EpisodeDetailView', 'DiffusionListView', 'TimetableView']


class EpisodeDetailView(ProgramPageDetailView):
    model = Episode

    def get_podcasts(self, diffusion):
        return Sound.objects.diffusion(diffusion).podcasts()

    def get_context_data(self, **kwargs):
        kwargs.setdefault('program', self.object.program)
        kwargs.setdefault('parent', kwargs['program'])
        if not 'tracks' in kwargs:
            kwargs['tracks'] = self.object.track_set.order_by('position')
        if not 'podcasts' in kwargs:
            kwargs['podcasts'] = self.object.sound_set.podcasts()
        return super().get_context_data(**kwargs)


# TODO: pagination: in template, only a limited number of pages displayed
class EpisodeListView(PageListView):
    model = Episode
    item_template_name = 'aircox/episode_item.html'
    show_headline = True
    template_name = 'aircox/diffusion_list.html'
    program = None

    def get(self, request, *args, **kwargs):
        program_slug = kwargs.get('program_slug')
        if program_slug:
            self.program = get_object_or_404(Program, slug=program_slug)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.program:
            qs = qs.filter(program=self.program)
        return qs

    def get_context_data(self, **kwargs):
        program = kwargs.setdefault('program', self.program)
        if program is not None:
            kwargs.setdefault('cover', program.cover)
            kwargs.setdefault('parent', program)
        return super().get_context_data(**kwargs)


class TimetableView(BaseView, ListView):
    """ View for timetables """
    template_name_suffix = '_timetable'
    model = Diffusion
    # ordering = ('start',)

    date = None
    start = None
    end = None

    def get_queryset(self):
        self.date = self.kwargs.get('date') or datetime.date.today()
        self.start = self.date - datetime.timedelta(days=self.date.weekday())
        self.end = self.start + datetime.timedelta(days=7)
        return super().get_queryset().range(self.start, self.end) \
                                     .order_by('start')

    def get_context_data(self, **kwargs):
        # regoup by dates
        by_date = OrderedDict()
        date = self.start
        while date < self.end:
            by_date[date] = []
            date += datetime.timedelta(days=1)

        for diffusion in self.object_list:
            if diffusion.date not in by_date:
                continue
            by_date[diffusion.date].append(diffusion)

        return super().get_context_data(
            by_date=by_date,
            date=self.date,
            start=self.start,
            end=self.end - datetime.timedelta(days=1),
            prev_date=self.start - datetime.timedelta(days=1),
            next_date=self.end + datetime.timedelta(days=1),
            **kwargs
        )



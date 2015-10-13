from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import ListView
from django.views.generic import DetailView
from django.core import serializers
from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox_programs.models as programs
from aircox_cms.views import Sections

from website.models import *


class PlayListSection (Sections.List):
    title = _('Playlist')

    def get_object_list (self):
        tracks = programs.Track.objects \
                     .filter(episode = self.object) \
                     .order_by('position')
        return [ Sections.List.Item(None, track.title, track.artist)
                    for track in tracks ]

class ScheduleSection (Sections.List):
    title = _('Schedule')

    def get_object_list (self):
        scheds = programs.Schedule.objects \
                    .filter(program = self.object.pk)

        return [
            Sections.List.Item(None, sched.get_frequency_display(),
                             _('rerun') if sched.rerun else None)
            for sched in scheds
        ]

class EpisodesSection (Sections.Posts):
    title = _('Episodes')

    def get_object_list (self):
        return Episode.objects.filter(related__program = self.object.related.pk)

class PreviousDiffusions (Sections.Posts):
    title = _('Previous Diffusions')
    fields = ['title', 'time']

    def get_object_list (self):
        diffusions = programs.Diffusion.objects\
                         .filter(date__lt = tz.datetime.now())
        episodes = []

        for diffusion in diffusions:
            if not diffusion.episode:
                continue

            post = Episode.objects.filter(related = diffusion.episode.pk)
            if not post:
                continue
            post = post[0]
            post.date = diffusion.date
            episodes.append(post)
            if len(episodes) == self.paginate_by:
                break

        return episodes



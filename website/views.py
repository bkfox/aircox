from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import ListView
from django.views.generic import DetailView
from django.core import serializers
from django.utils.translation import ugettext as _, ugettext_lazy

import programs.models as programs
from cms.views import ListSection


class PlaylistSection (ListSection):
    title = _('Playlist')

    def get_object_list (self):
        tracks = programs.Track.objects \
                     .filter(episode = self.object) \
                     .order_by('position')
        return [ ListSection.Item(None, track.title, track.artist)
                    for track in tracks ]


class ScheduleSection (ListSection):
    title = _('Schedule')

    def get_object_list (self):
        scheds = programs.Schedule.objects \
                    .filter(program = self.object.pk)

        return [
            ListSection.Item(None, sched.get_frequency_display(),
                             _('rerun') if sched.rerun else None)
            for sched in scheds
        ]




import copy

from django import forms
from django.contrib import admin
from django.db import models

from suit.admin import SortableTabularInline, SortableModelAdmin
from autocomplete_light.contrib.taggit_field import TaggitWidget, TaggitField

from aircox_programs.forms import *
from aircox_programs.models import *


#
# Inlines
#
# TODO: inherits from the corresponding admin view
class SoundInline (admin.TabularInline):
    model = Sound


class ScheduleInline (admin.TabularInline):
    model = Schedule
    extra = 1


class DiffusionInline (admin.TabularInline):
    model = Diffusion
    fields = ('episode', 'type', 'date', 'stream')
    readonly_fields = ('date', 'stream')
    extra = 1


class TrackInline (SortableTabularInline):
    fields = ['artist', 'name', 'tags', 'position']
    form = TrackForm
    model = Track
    sortable = 'position'
    extra = 10


class NameableAdmin (admin.ModelAdmin):
    fields = [ 'name' ]

    list_display = ['id', 'name']
    list_filter = []
    search_fields = ['name',]


@admin.register(Sound)
class SoundAdmin (NameableAdmin):
    fields = None
    list_display = ['id', 'name', 'duration', 'type', 'date', 'good_quality', 'removed', 'public']
    fieldsets = [
        (None, { 'fields': NameableAdmin.fields + ['path', 'type'] } ),
        (None, { 'fields': ['embed', 'duration', 'date'] }),
        (None, { 'fields': ['removed', 'good_quality', 'public' ] } )
    ]


@admin.register(Stream)
class StreamAdmin (SortableModelAdmin):
    list_display = ('id', 'name', 'type')
    sortable = "priority"


@admin.register(Program)
class ProgramAdmin (NameableAdmin):
    fields = NameableAdmin.fields + ['stream']
    inlines = [ ScheduleInline ]


@admin.register(Episode)
class EpisodeAdmin (NameableAdmin):
    list_filter = ['program'] + NameableAdmin.list_filter
    fields = NameableAdmin.fields + ['sounds', 'program']

    inlines = (TrackInline, DiffusionInline)


@admin.register(Diffusion)
class DiffusionAdmin (admin.ModelAdmin):
    def archives (self, obj):
        sounds = obj.episode and \
                    (os.path.basename(sound.path) for sound in obj.episode.sounds.all()
                        if sound.type == Sound.Type['archive'] )
        return ', '.join(sounds) if sounds else ''

    list_display = ('id', 'type', 'date', 'archives', 'episode', 'program', 'stream')
    list_filter = ('type', 'date', 'program', 'stream')
    list_editable = ('type', 'date')

    def get_queryset(self, request):
        qs = super(DiffusionAdmin, self).get_queryset(request)
        if 'type__exact' in request.GET and \
                str(Diffusion.Type['unconfirmed']) in request.GET['type__exact']:
            return qs
        return qs.exclude(type = Diffusion.Type['unconfirmed'])


admin.site.register(Track)
admin.site.register(Schedule)


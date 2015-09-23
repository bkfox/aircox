import copy

from django import forms
from django.contrib import admin
from django.db import models

from suit.admin import SortableTabularInline, SortableModelAdmin
from autocomplete_light.contrib.taggit_field import TaggitWidget, TaggitField

from programs.forms import *
from programs.models import *


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


class DescriptionAdmin (admin.ModelAdmin):
    fields = [ 'name', 'tags', 'description' ]

    def tags (obj):
        return ', '.join(obj.tags.names())

    list_display = ['id', 'name', tags]
    list_filter = []
    search_fields = ['name',]


@admin.register(Sound)
class SoundAdmin (DescriptionAdmin):
    fields = None
    fieldsets = [
        (None, { 'fields': DescriptionAdmin.fields + ['path' ] } ),
        (None, { 'fields': ['duration', 'date', 'fragment' ] } )
    ]


@admin.register(Stream)
class StreamAdmin (SortableModelAdmin):
    list_display = ('id', 'name', 'type', 'priority')
    sortable = "priority"


@admin.register(Program)
class ProgramAdmin (DescriptionAdmin):
    fields = DescriptionAdmin.fields + ['stream']
    inlines = [ ScheduleInline ]


@admin.register(Episode)
class EpisodeAdmin (DescriptionAdmin):
    list_filter = ['program'] + DescriptionAdmin.list_filter
    fields = DescriptionAdmin.fields + ['sounds']

    inlines = (TrackInline, DiffusionInline)


@admin.register(Diffusion)
class DiffusionAdmin (admin.ModelAdmin):
    list_display = ('id', 'type', 'date', 'episode', 'program', 'stream')
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


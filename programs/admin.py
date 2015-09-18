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
    fields = ['artist', 'title', 'tags', 'position']
    form = TrackForm
    model = Track
    sortable = 'position'
    extra = 10


class MetadataAdmin (admin.ModelAdmin):
    fieldsets = [
        ( None, {
            'fields': [ 'title', 'tags' ]
        }),
        ( None, {
            'fields': [ 'date', 'public' ],
        }),
    ]

    def save_model (self, request, obj, form, change):
        # FIXME: if request.data.author?
        if not obj.author:
            obj.author = request.user
        obj.save()


class PublicationAdmin (MetadataAdmin):
    fieldsets = copy.deepcopy(MetadataAdmin.fieldsets)

    list_display = ('id', 'title', 'date', 'public', 'parent')
    list_filter = ['date', 'public', 'parent', 'author']
    list_editable = ('public',)
    search_fields = ['title', 'content']

    fieldsets[0][1]['fields'].insert(1, 'subtitle')
    fieldsets[0][1]['fields'] += [ 'img', 'content' ]
    fieldsets[1][1]['fields'] += [ 'parent' ] #, 'meta' ],


@admin.register(Sound)
class SoundAdmin (MetadataAdmin):
    fieldsets = [
        (None, { 'fields': ['title', 'tags', 'path' ] } ),
        (None, { 'fields': ['duration', 'date', 'fragment' ] } )
    ]


@admin.register(Stream)
class StreamAdmin (SortableModelAdmin):
    list_display = ('id', 'title', 'type', 'public', 'priority')
    list_editable = ('public',)
    sortable = "priority"


@admin.register(Program)
class ProgramAdmin (PublicationAdmin):
    fieldsets = copy.deepcopy(PublicationAdmin.fieldsets)
    inlines = [ ScheduleInline ]

    fieldsets[1][1]['fields'] += ['email', 'url']


@admin.register(Episode)
class EpisodeAdmin (PublicationAdmin):
    fieldsets = copy.deepcopy(PublicationAdmin.fieldsets)
    list_filter = ['parent'] + PublicationAdmin.list_filter

    fieldsets[0][1]['fields'] += ['sounds']

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


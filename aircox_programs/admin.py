import copy

from django import forms
from django.contrib import admin
from django.db import models

from suit.admin import SortableTabularInline, SortableModelAdmin

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

class StreamInline (admin.TabularInline):
    fields = ['delay', 'begin', 'end']
    model = Stream
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
    list_display = ['id', 'name', 'duration', 'type', 'mtime', 'good_quality', 'removed', 'public']
    fieldsets = [
        (None, { 'fields': NameableAdmin.fields + ['path', 'type'] } ),
        (None, { 'fields': ['embed', 'duration', 'mtime'] }),
        (None, { 'fields': ['removed', 'good_quality', 'public' ] } )
    ]
    readonly_fields = ('path', 'duration',)


@admin.register(Stream)
class StreamAdmin (admin.ModelAdmin):
    list_display = ('id', 'program', 'delay', 'begin', 'end')


@admin.register(Station)
class StationAdmin (NameableAdmin):
    fields = NameableAdmin.fields + [ 'active', 'public', 'fallback' ]

@admin.register(Program)
class ProgramAdmin (NameableAdmin):
    fields = NameableAdmin.fields + [ 'station', 'active' ]
    # TODO list_display
    inlines = [ ScheduleInline, StreamInline ]

    # SO#8074161
    #def get_form (self, request, obj=None, **kwargs):
        #if obj:
        #    if Schedule.objects.filter(program = obj).count():
        #        self.inlines.remove(StreamInline)
        #    elif Stream.objects.filter(program = obj).count():
        #        self.inlines.remove(ScheduleInline)
        #return super().get_form(request, obj, **kwargs)

@admin.register(Diffusion)
class DiffusionAdmin (admin.ModelAdmin):
    def archives (self, obj):
        sounds = [ str(s) for s in obj.get_archives()]
        return ', '.join(sounds) if sounds else ''

    list_display = ('id', 'type', 'date', 'archives', 'program', 'initial')
    list_filter = ('type', 'date', 'program')
    list_editable = ('type', 'date')

    fields = ['type', 'date', 'initial', 'sounds', 'program']
    readonly_fields = ('duration',)

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            if obj.date < tz.make_aware(tz.datetime.now()):
                self.readonly_fields = list(self.fields)
                self.readonly_fields.remove('type')
            elif obj.initial:
                self.readonly_fields = ['program', 'sounds']
            else:
                self.readonly_fields = []
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(DiffusionAdmin, self).get_queryset(request)
        if '_changelist_filters' in request.GET or \
            'type__exact' in request.GET and \
                str(Diffusion.Type['unconfirmed']) in request.GET['type__exact']:
            return qs
        return qs.exclude(type = Diffusion.Type['unconfirmed'])


admin.site.register(Log)
admin.site.register(Track)
admin.site.register(Schedule)


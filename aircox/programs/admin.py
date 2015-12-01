import copy

from django import forms
from django.contrib import admin
from django.db import models

from aircox.programs.models import *


#
# Inlines
#
class SoundInline (admin.TabularInline):
    model = Sound


class ScheduleInline (admin.TabularInline):
    model = Schedule
    extra = 1

class StreamInline (admin.TabularInline):
    fields = ['delay', 'begin', 'end']
    model = Stream
    extra = 1


# from suit.admin import SortableTabularInline, SortableModelAdmin
#class TrackInline (SortableTabularInline):
#    fields = ['artist', 'name', 'tags', 'position']
#    form = TrackForm
#    model = Track
#    sortable = 'position'
#    extra = 10


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

    def conflicts (self, obj):
        if obj.type == Diffusion.Type['unconfirmed']:
            return ', '.join([ str(d) for d in obj.get_conflicts()])
        return ''

    list_display = ('id', 'type', 'date', 'program', 'initial', 'archives', 'conflicts')
    list_filter = ('type', 'date', 'program')
    list_editable = ('type', 'date')

    fields = ['type', 'date', 'initial', 'program', 'sounds']

    def get_form(self, request, obj=None, **kwargs):
        if request.user.has_perm('aircox_program.programming'):
            self.readonly_fields = []
        else:
            self.readonly_fields = ['program', 'date', 'duration']

        if obj.initial:
            self.readonly_fields += ['program', 'sounds']
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(DiffusionAdmin, self).get_queryset(request)
        if '_changelist_filters' in request.GET or \
            'type__exact' in request.GET and \
                str(Diffusion.Type['unconfirmed']) in request.GET['type__exact']:
            return qs
        return qs.exclude(type = Diffusion.Type['unconfirmed'])


@admin.register(Log)
class LogAdmin (admin.ModelAdmin):
    list_display = ['id', 'date', 'source', 'comment', 'related_object']
    list_filter = ['date', 'related_type']

admin.site.register(Track)
admin.site.register(Schedule)


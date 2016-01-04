import copy

from django import forms
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

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
    def schedule (self, obj):
        return Schedule.objects.filter(program = obj).count() > 0
    schedule.boolean = True
    schedule.short_description = _("Schedule")

    list_display = ('id', 'name', 'active', 'schedule')
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

    list_display = ('id', 'type', 'start', 'end', 'program', 'initial', 'archives', 'conflicts')
    list_filter = ('type', 'start', 'program')
    list_editable = ('type', 'start', 'end')

    fields = ['type', 'start', 'end', 'initial', 'program', 'sounds']

    def get_form(self, request, obj=None, **kwargs):
        if request.user.has_perm('aircox_program.programming'):
            self.readonly_fields = []
        else:
            self.readonly_fields = ['program', 'start', 'end']

        if obj and obj.initial:
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


@admin.register(Schedule)
class ScheduleAdmin (admin.ModelAdmin):
    def program_name (self, obj):
        return obj.program.name
    program_name.short_description = _('Program')

    def day (self, obj):
        return obj.date.strftime('%A')
    day.short_description = _('Day')

    def rerun (self, obj):
        return obj.initial != None
    rerun.short_description = _('Rerun')
    rerun.boolean = True

    list_display = ['id', 'program_name', 'frequency', 'date', 'day', 'rerun']
    list_editable = ['frequency', 'date']

admin.site.register(Track)


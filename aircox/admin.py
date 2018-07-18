import copy

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.models import *

#
# Inlines
#
class SoundInline(admin.TabularInline):
    model = Sound


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1

class StreamInline(admin.TabularInline):
    fields = ['delay', 'begin', 'end']
    model = Stream
    extra = 1

class SoundInline(admin.TabularInline):
    fields = ['type', 'path', 'duration','public']
    # readonly_fields = fields
    model = Sound
    extra = 0


class DiffusionInline(admin.StackedInline):
    model = Diffusion
    extra = 0
    fields = ['type', 'start', 'end']

class NameableAdmin(admin.ModelAdmin):
    fields = [ 'name' ]

    list_display = ['id', 'name']
    list_filter = []
    search_fields = ['name',]


class TrackInline(GenericTabularInline):
    ct_field = 'related_type'
    ct_fk_field = 'related_id'
    model = Track
    extra = 0
    fields = ('artist', 'title', 'info', 'position', 'in_seconds', 'tags')

    list_display = ['artist','title','tags','related']
    list_filter = ['artist','title','tags']


@admin.register(Sound)
class SoundAdmin(NameableAdmin):
    fields = None
    list_display = ['id', 'name', 'program', 'type', 'duration', 'mtime',
                    'public', 'good_quality', 'path']
    list_filter = ('program', 'type', 'good_quality', 'public')
    fieldsets = [
        (None, { 'fields': NameableAdmin.fields +
                           ['path', 'type', 'program', 'diffusion'] } ),
        (None, { 'fields': ['embed', 'duration', 'public', 'mtime'] }),
        (None, { 'fields': ['good_quality' ] } )
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [TrackInline]


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'delay', 'begin', 'end')


@admin.register(Program)
class ProgramAdmin(NameableAdmin):
    def schedule(self, obj):
        return Schedule.objects.filter(program = obj).count() > 0
    schedule.boolean = True
    schedule.short_description = _("Schedule")

    list_display = ('id', 'name', 'active', 'schedule', 'sync', 'station')
    fields = NameableAdmin.fields + [ 'active', 'station','sync' ]
    inlines = [ ScheduleInline, StreamInline ]

    # SO#8074161
    #def get_form(self, request, obj=None, **kwargs):
        #if obj:
        #    if Schedule.objects.filter(program = obj).count():
        #        self.inlines.remove(StreamInline)
        #    elif Stream.objects.filter(program = obj).count():
        #        self.inlines.remove(ScheduleInline)
        #return super().get_form(request, obj, **kwargs)


@admin.register(Diffusion)
class DiffusionAdmin(admin.ModelAdmin):
    def archives(self, obj):
        sounds = [ str(s) for s in obj.get_sounds(archive=True)]
        return ', '.join(sounds) if sounds else ''

    def conflicts_(self, obj):
        if obj.conflicts.count():
            return obj.conflicts.count()
        return ''

    def start_date(self, obj):
        return obj.local_date.strftime('%Y/%m/%d %H:%M')
    start_date.short_description = _('start')

    def end_date(self, obj):
        return obj.local_end.strftime('%H:%M')
    end_date.short_description = _('end')

    def first(self, obj):
        return obj.initial.start if obj.initial else ''

    list_display = ('id', 'program', 'start_date', 'end_date', 'type', 'first', 'archives', 'conflicts_')
    list_filter = ('type', 'start', 'program')
    list_editable = ('type',)
    ordering = ('-start', 'id')

    fields = ['type', 'start', 'end', 'initial', 'program', 'conflicts']
    readonly_fields = ('conflicts',)
    inlines = [ DiffusionInline, SoundInline ]


    def get_form(self, request, obj=None, **kwargs):
        if request.user.has_perm('aircox_program.programming'):
            self.readonly_fields = []
        else:
            self.readonly_fields = ['program', 'start', 'end']
        return super().get_form(request, obj, **kwargs)

    def get_object(self, *args, **kwargs):
        """
        We want rerun to redirect to the given object.
        """
        obj = super().get_object(*args, **kwargs)
        if obj and obj.initial:
            obj = obj.initial
        return obj

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET and len(request.GET):
            return qs
        return qs.exclude(type = Diffusion.Type.unconfirmed)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    def program_name(self, obj):
        return obj.program.name
    program_name.short_description = _('Program')

    def day(self, obj):
        return '' # obj.date.strftime('%A')
    day.short_description = _('Day')

    def rerun(self, obj):
        return obj.initial != None
    rerun.short_description = _('Rerun')
    rerun.boolean = True


    list_filter = ['frequency', 'program']
    list_display = ['id', 'program_name', 'frequency', 'day', 'date',
                    'time', 'duration', 'timezone', 'rerun']
    list_editable = ['time', 'timezone', 'duration']


    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['program', 'date', 'frequency']
        else:
            return []


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'artist', 'position', 'in_seconds', 'related']



# TODO: sort & redo
class PortInline(admin.StackedInline):
    model = Port
    extra = 0

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    inlines = [ PortInline ]

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'station', 'source', 'type', 'comment', 'diffusion', 'sound', 'track']
    list_filter = ['date', 'source', 'diffusion', 'sound', 'track']

admin.site.register(Port)





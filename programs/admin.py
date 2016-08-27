import copy

from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.programs.models import *


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
    fields = ('artist', 'title', 'info', 'position')
    readonly_fields = ('position',)


@admin.register(Sound)
class SoundAdmin(NameableAdmin):
    fields = None
    list_display = ['id', 'name', 'duration', 'type', 'mtime',
                    'public', 'good_quality', 'path']
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

    list_display = ('id', 'name', 'active', 'schedule')
    fields = NameableAdmin.fields + [ 'active' ]
    # TODO list_display
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
        sounds = [ str(s) for s in obj.get_archives()]
        return ', '.join(sounds) if sounds else ''

    def conflicts(self, obj):
        if obj.type == Diffusion.Type.unconfirmed:
            return ', '.join([ str(d) for d in obj.get_conflicts()])
        return ''

    def end_time(self, obj):
        return obj.end.strftime('%H:%M')
    end_time.short_description = _('end')

    def first(self, obj):
        return obj.initial.start if obj.initial else ''

    list_display = ('id', 'program', 'start', 'end_time', 'type', 'first', 'archives', 'conflicts')
    list_filter = ('type', 'start', 'program')
    list_editable = ('type',)
    ordering = ('-start', 'id')

    fields = ['type', 'start', 'end', 'initial', 'program']
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
        return obj.date.strftime('%A')
    day.short_description = _('Day')

    def rerun(self, obj):
        return obj.initial != None
    rerun.short_description = _('Rerun')
    rerun.boolean = True

    list_filter = ['frequency', 'program']
    list_display = ['id', 'program_name', 'frequency', 'date', 'day', 'rerun']
    list_editable = ['frequency', 'date']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'artist', 'position', 'in_seconds', 'related']



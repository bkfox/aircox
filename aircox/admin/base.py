from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.safestring import mark_safe

from adminsortable2.admin import SortableInlineAdminMixin

from aircox.models import *


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1

class StreamInline(admin.TabularInline):
    fields = ['delay', 'begin', 'end']
    model = Stream
    extra = 1


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'delay', 'begin', 'end')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    def schedule(self, obj):
        return Schedule.objects.filter(program=obj).count() > 0

    schedule.boolean = True
    schedule.short_description = _("Schedule")

    list_display = ('name', 'id', 'active', 'schedule', 'sync', 'station')
    fields = ['name', 'slug', 'active', 'station', 'sync']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    inlines = [ScheduleInline, StreamInline]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    def program_name(self, obj):
        return obj.program.name
    program_name.short_description = _('Program')

    def day(self, obj):
        return '' # obj.date.strftime('%A')
    day.short_description = _('Day')

    def rerun(self, obj):
        return obj.initial is not None
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

# TODO: sort & redo
class PortInline(admin.StackedInline):
    model = Port
    extra = 0


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PortInline]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'station', 'source', 'type', 'diffusion', 'sound', 'track']
    list_filter = ['date', 'source', 'station']

admin.site.register(Port)





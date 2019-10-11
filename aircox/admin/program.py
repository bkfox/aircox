from copy import deepcopy

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ..models import Program, Schedule, Stream
from .page import PageAdmin


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


class StreamInline(admin.TabularInline):
    fields = ['delay', 'begin', 'end']
    model = Stream
    extra = 1


@admin.register(Program)
class ProgramAdmin(PageAdmin):
    def schedule(self, obj):
        return Schedule.objects.filter(program=obj).count() > 0

    schedule.boolean = True
    schedule.short_description = _("Schedule")

    list_display = PageAdmin.list_display + ('schedule', 'station', 'active')
    list_filter = PageAdmin.list_filter + ('station', 'active')
    fieldsets = deepcopy(PageAdmin.fieldsets) + [
        (_('Program Settings'), {
            'fields': ['active', 'station', 'sync'],
            'classes': ('collapse',),
        })
    ]

    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']

    inlines = [ScheduleInline, StreamInline]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    def program_title(self, obj):
        return obj.program.title
    program_title.short_description = _('Program')

    def freq(self, obj):
        return obj.get_frequency_verbose()
    freq.short_description = _('Day')

    list_filter = ['frequency', 'program']
    list_display = ['program_title', 'freq', 'time', 'timezone', 'duration',
                    'initial']
    list_editable = ['time', 'duration', 'initial']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['program', 'date', 'frequency']
        else:
            return []


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('id', 'program', 'delay', 'begin', 'end')




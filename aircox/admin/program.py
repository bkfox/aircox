from copy import copy

from django.contrib import admin
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from ..models import Program, Schedule, Stream
from .page import PageAdmin


# In order to simplify schedule_post_save algorithm, an existing schedule can't
# update the following fields: "frequency", "date"
class ScheduleInlineForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial:
            self.fields['date'].disabled = True
            self.fields['frequency'].disabled = True


class ScheduleInline(admin.TabularInline):
    model = Schedule
    form = ScheduleInlineForm
    readonly_fields = ('timezone',)
    extra = 1


class StreamInline(admin.TabularInline):
    model = Stream
    fields = ['delay', 'begin', 'end']
    extra = 1


@admin.register(Program)
class ProgramAdmin(PageAdmin):
    def schedule(self, obj):
        return Schedule.objects.filter(program=obj).count() > 0

    schedule.boolean = True
    schedule.short_description = _("Schedule")

    list_display = PageAdmin.list_display + ('schedule', 'station', 'active')
    list_filter = PageAdmin.list_filter + ('station', 'active')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)

    inlines = [ScheduleInline, StreamInline]

    def get_fieldsets(self, request, obj=None):
        fields = super().get_fieldsets(request, obj)
        if request.user.has_perm('aircox.program.scheduling'):
            fields = fields + [
                (_('Program Settings'), {
                    'fields': ['active', 'station', 'sync'],
                })
            ]
        return fields


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



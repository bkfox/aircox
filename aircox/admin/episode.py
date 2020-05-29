from django import forms
from django.contrib import admin
from django.utils.translation import gettext as _

from ..models import Episode, Diffusion

from .page import PageAdmin
from .sound import SoundInline, TracksInline


class DiffusionBaseAdmin:
    fields = ['type', 'start', 'end']

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.has_perm('aircox_program.scheduling'):
            fields += ('program', 'start', 'end')
        return [field for field in fields if field in self.fields]


@admin.register(Diffusion)
class DiffusionAdmin(DiffusionBaseAdmin, admin.ModelAdmin):
    def start_date(self, obj):
        return obj.local_start.strftime('%Y/%m/%d %H:%M')
    start_date.short_description = _('start')

    def end_date(self, obj):
        return obj.local_end.strftime('%H:%M')
    end_date.short_description = _('end')

    list_display = ('episode', 'start_date', 'end_date', 'type', 'initial')
    list_filter = ('type', 'start', 'program')
    list_editable = ('type',)
    ordering = ('-start', 'id')

    fields = ['type', 'start', 'end', 'initial', 'program']


class DiffusionInline(DiffusionBaseAdmin, admin.TabularInline):
    model = Diffusion
    fk_name = 'episode'
    extra = 0

    def has_add_permission(self, request, obj):
        return request.user.has_perm('aircox_program.scheduling')


class EpisodeAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = True


@admin.register(Episode)
class EpisodeAdmin(PageAdmin):
    form = EpisodeAdminForm
    list_display = PageAdmin.list_display
    list_filter = PageAdmin.list_filter + ('diffusion__start',)
    search_fields = PageAdmin.search_fields + ('parent__title',)
    # readonly_fields = ('parent',)

    inlines = [TracksInline, SoundInline, DiffusionInline]



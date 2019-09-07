import copy

from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.models import Episode, Diffusion, Sound, Track

from .page import PageAdmin
from .sound import SoundInline, TracksInline


class DiffusionBaseAdmin:
    fields = ['type', 'start', 'end']

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not request.user.has_perm('aircox_program.scheduling'):
            fields += ['program', 'start', 'end']
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

    def has_add_permission(self, request):
        return request.user.has_perm('aircox_program.scheduling')


@admin.register(Episode)
class EpisodeAdmin(PageAdmin):
    list_display = PageAdmin.list_display + ('program',)
    list_filter = PageAdmin.list_filter + ('program',)
    search_fields = PageAdmin.search_fields + ['program__title']
    readonly_fields = ('program',)

    fieldsets = copy.deepcopy(PageAdmin.fieldsets)
    fieldsets[1][1]['fields'].insert(0, 'program')
    inlines = [TracksInline, SoundInline, DiffusionInline]



from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.models import Diffusion, Sound, Track

from .playlist import TracksInline


class SoundInline(admin.TabularInline):
    model = Sound
    fk_name = 'diffusion'
    fields = ['type', 'path', 'duration','public']
    readonly_fields = ['type']
    extra = 0


class RediffusionInline(admin.StackedInline):
    model = Diffusion
    fk_name = 'initial'
    extra = 0
    fields = ['type', 'start', 'end']


@admin.register(Diffusion)
class DiffusionAdmin(admin.ModelAdmin):
    def archives(self, obj):
        sounds = [str(s) for s in obj.get_sounds(archive=True)]
        return ', '.join(sounds) if sounds else ''

    def conflicts_count(self, obj):
        if obj.conflicts.count():
            return obj.conflicts.count()
        return ''
    conflicts_count.short_description = _('Conflicts')

    def start_date(self, obj):
        return obj.local_date.strftime('%Y/%m/%d %H:%M')
    start_date.short_description = _('start')

    def end_date(self, obj):
        return obj.local_end.strftime('%H:%M')
    end_date.short_description = _('end')

    def first(self, obj):
        return obj.initial.start if obj.initial else ''

    list_display = ('id', 'program', 'start_date', 'end_date', 'type', 'first', 'archives', 'conflicts_count')
    list_filter = ('type', 'start', 'program')
    list_editable = ('type',)
    ordering = ('-start', 'id')

    fields = ['type', 'start', 'end', 'initial', 'program', 'conflicts']
    readonly_fields = ('conflicts',)
    inlines = [TracksInline, RediffusionInline, SoundInline]

    def get_playlist(self, request, obj=None):
        return obj and getattr(obj, 'playlist', None)

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
        return qs.exclude(type=Diffusion.Type.unconfirmed)



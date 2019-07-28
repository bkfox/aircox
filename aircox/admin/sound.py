from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.models import Sound
from .playlist import TracksInline


@admin.register(Sound)
class SoundAdmin(admin.ModelAdmin):
    fields = None
    list_display = ['id', 'name', 'program', 'type', 'duration', 'mtime',
                    'is_public', 'is_good_quality', 'path']
    list_filter = ('program', 'type', 'is_good_quality', 'is_public')
    fieldsets = [
        (None, {'fields': ['name', 'path', 'type', 'program', 'diffusion']}),
        (None, {'fields': ['embed', 'duration', 'is_public', 'mtime']}),
        (None, {'fields': ['is_good_quality']})
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [TracksInline]



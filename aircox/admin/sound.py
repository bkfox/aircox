from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.models import Sound
from .base import NameableAdmin
from .playlist import TracksInline


@admin.register(Sound)
class SoundAdmin(NameableAdmin):
    fields = None
    list_display = ['id', 'name', 'program', 'type', 'duration', 'mtime',
                    'public', 'good_quality', 'path']
    list_filter = ('program', 'type', 'good_quality', 'public')
    fieldsets = [
        (None, {'fields': NameableAdmin.fields +
                          ['path', 'type', 'program', 'diffusion']}),
        (None, {'fields': ['embed', 'duration', 'public', 'mtime']}),
        (None, {'fields': ['good_quality']})
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [TracksInline]



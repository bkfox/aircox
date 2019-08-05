from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

from aircox.models import Sound
from .playlist import TracksInline


class SoundInline(admin.TabularInline):
    model = Sound
    fields = ['type', 'path', 'duration', 'is_public']
    readonly_fields = ['type']
    extra = 0


@admin.register(Sound)
class SoundAdmin(admin.ModelAdmin):
    def filename(self, obj):
        return '/'.join(obj.path.split('/')[-2:])
    filename.short_description=_('file')

    fields = None
    list_display = ['id', 'name', 'program', 'type', 'duration',
                    'is_public', 'is_good_quality', 'episode', 'filename']
    list_filter = ('program', 'type', 'is_good_quality', 'is_public')
    fieldsets = [
        (None, {'fields': ['name', 'path', 'type', 'program', 'episode']}),
        (None, {'fields': ['embed', 'duration', 'is_public', 'mtime']}),
        (None, {'fields': ['is_good_quality']})
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [TracksInline]




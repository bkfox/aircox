from django.contrib import admin
from django.utils.translation import gettext as _, gettext_lazy

from adminsortable2.admin import SortableInlineAdminMixin

from ..models import Sound, Track


class TracksInline(SortableInlineAdminMixin, admin.TabularInline):
    template = 'admin/aircox/playlist_inline.html'
    model = Track
    extra = 0
    fields = ('position', 'artist', 'title', 'info', 'timestamp', 'tags')

    list_display = ['artist', 'title', 'tags', 'related']
    list_filter = ['artist', 'title', 'tags']


class SoundInline(admin.TabularInline):
    model = Sound
    fields = ['type', 'path', 'embed', 'duration', 'is_public']
    readonly_fields = ['type', 'path', 'duration']
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).available()


@admin.register(Sound)
class SoundAdmin(admin.ModelAdmin):
    def filename(self, obj):
        return '/'.join(obj.path.split('/')[-2:])
    filename.short_description=_('file')

    fields = None
    list_display = ['id', 'name', 'program', 'type', 'duration',
                    'is_public', 'is_good_quality', 'episode', 'filename']
    list_filter = ('program', 'type', 'is_good_quality', 'is_public')

    search_fields = ['name', 'program']
    fieldsets = [
        (None, {'fields': ['name', 'path', 'type', 'program', 'episode']}),
        (None, {'fields': ['embed', 'duration', 'is_public', 'mtime']}),
        (None, {'fields': ['is_good_quality']})
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [TracksInline]


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    list_display = ['pk', 'artist', 'title', 'tag_list', 'episode', 'sound', 'timestamp']
    list_editable = ['artist', 'title']
    list_filter = ['artist', 'title', 'tags']

    search_fields = ['artist', 'title']
    fieldsets = [
        (_('Playlist'), {'fields': ['episode', 'sound', 'position', 'timestamp']}),
        (_('Info'), {'fields': ['artist', 'title', 'info', 'tags']}),
    ]

    # TODO on edit: readonly_fields = ['episode', 'sound']



from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from adminsortable2.admin import SortableInlineAdminMixin

from ..models import Sound, Track


class TrackInline(SortableInlineAdminMixin, admin.TabularInline):
    template = 'admin/aircox/playlist_inline.html'
    model = Track
    extra = 0
    fields = ('position', 'artist', 'title', 'info', 'tags')

    list_display = ['artist', 'title', 'tags', 'related']
    list_filter = ['artist', 'title', 'tags']

class SoundTrackInline(TrackInline):
    fields = TrackInline.fields + ('timestamp',)


class SoundInline(admin.TabularInline):
    model = Sound
    fields = ['type', 'name', 'audio', 'duration', 'is_good_quality', 'is_public']
    readonly_fields = ['type', 'audio', 'duration', 'is_good_quality']
    extra = 0
    max_num = 0

    def audio(self, obj):
        return mark_safe('<audio src="{}" controls></audio>'.format(obj.url()))

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
    list_filter = ('type', 'is_good_quality', 'is_public')

    search_fields = ['name', 'program__title']
    fieldsets = [
        (None, {'fields': ['name', 'path', 'type', 'program', 'episode']}),
        (None, {'fields': ['duration', 'is_public', 'is_good_quality', 'mtime']}),
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [SoundTrackInline]


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



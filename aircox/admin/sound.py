from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

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
    audio.short_descripton = _('Audio')

    def get_queryset(self, request):
        return super().get_queryset(request).available()


@admin.register(Sound)
class SoundAdmin(admin.ModelAdmin):
    fields = None
    list_display = ['id', 'name', 'related',
                    'type', 'duration', 'is_public', 'is_good_quality',
                    'audio']
    list_filter = ('type', 'is_good_quality', 'is_public')
    list_editable = ['name', 'type', 'is_public']

    search_fields = ['name', 'program__title']
    fieldsets = [
        (None, {'fields': ['name', 'path', 'type', 'program', 'episode']}),
        (None, {'fields': ['duration', 'is_public', 'is_good_quality', 'mtime']}),
    ]
    readonly_fields = ('path', 'duration',)
    inlines = [SoundTrackInline]

    def related(self, obj):
        # TODO: link to episode or program edit
        return obj.episode.title if obj.episode else\
               obj.program.title if obj.program else ''
    related.short_description = _('Program / Episode')

    def audio(self, obj):
        return mark_safe('<audio src="{}" controls></audio>'.format(obj.url()))
    audio.short_descripton = _('Audio')


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



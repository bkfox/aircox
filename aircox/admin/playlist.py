from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy

from adminsortable2.admin import SortableInlineAdminMixin

from aircox.models import Track


class TracksInline(SortableInlineAdminMixin, admin.TabularInline):
    template = 'admin/aircox/playlist_inline.html'
    model = Track
    extra = 0
    fields = ('position', 'artist', 'title', 'info', 'timestamp', 'tags')

    list_display = ['artist', 'title', 'tags', 'related']
    list_filter = ['artist', 'title', 'tags']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    list_display = ['pk', 'artist', 'title', 'tag_list', 'diffusion', 'sound', 'timestamp']
    list_editable = ['artist', 'title']
    list_filter = ['sound', 'diffusion', 'artist', 'title', 'tags']
    fieldsets = [
        (_('Playlist'), {'fields': ['diffusion', 'sound', 'position', 'timestamp']}),
        (_('Info'), {'fields': ['artist', 'title', 'info', 'tags']}),
    ]

    # TODO on edit: readonly_fields = ['diffusion', 'sound']

#@admin.register(Playlist)
#class PlaylistAdmin(admin.ModelAdmin):
#    fields = ['diffusion', 'sound']
#    inlines = [TracksInline]
#    # TODO: dynamic read only fields



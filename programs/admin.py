import copy

from django.contrib     import admin
from django.db          import models

from suit.admin import SortableTabularInline

from programs.forms     import *
from programs.models    import *


#
# Inlines
#
# TODO: inherits from the corresponding admin view
class ScheduleInline (admin.TabularInline):
    model = Schedule
    extra = 1


class DiffusionInline (admin.TabularInline):
    model = Diffusion
    fields = ('episode', 'type', 'begin', 'end', 'stream')
    readonly_fields = ('begin', 'end', 'stream')
    extra = 1



class TrackInline (SortableTabularInline):
    fields = ['artist', 'title', 'tags', 'position']
    form = TrackForm
    model = Track
    sortable = 'position'
    extra = 10


#
# Parents
#
class MetadataAdmin (admin.ModelAdmin):
    fieldsets = [
        ( None, {
            'fields': [ 'title', 'tags' ]
        }),
        ( None, {
            'fields': [ 'date', 'public', 'enumerable' ],
        }),
    ]


    def save_model (self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        obj.save()


from autocomplete_light.contrib.taggit_field import TaggitWidget, TaggitField
class PublicationAdmin (MetadataAdmin):
    fieldsets = copy.deepcopy(MetadataAdmin.fieldsets)

    list_display = ('id', 'title', 'date', 'public', 'parent')
    list_filter = ['date', 'public', 'parent', 'author']
    search_fields = ['title', 'content']


    fieldsets[0][1]['fields'].insert(1, 'subtitle')
    fieldsets[0][1]['fields'] += [ 'img', 'content' ]
    fieldsets[1][1]['fields'] += [ 'parent' ] #, 'meta' ],



#
# ModelAdmin list
#
class SoundAdmin (MetadataAdmin):
    fieldsets = [
        (None, { 'fields': ['title', 'tags', 'path' ] } ),
        (None, { 'fields': ['duration', 'date', 'fragment' ] } )
    ]


class ArticleAdmin (PublicationAdmin):
    fieldsets           = copy.deepcopy(PublicationAdmin.fieldsets)

    fieldsets[1][1]['fields'] += ['static_page']


class ProgramAdmin (PublicationAdmin):
    fieldsets           = copy.deepcopy(PublicationAdmin.fieldsets)
    inlines             = [ ScheduleInline ]

    fieldsets[1][1]['fields'] += ['email', 'url']


class EpisodeAdmin (PublicationAdmin):
    fieldsets = copy.deepcopy(PublicationAdmin.fieldsets)
    list_filter         = ['parent'] + PublicationAdmin.list_filter

    fieldsets[0][1]['fields'] += ['sounds']

    inlines = (TrackInline, DiffusionInline)


class DiffusionAdmin (admin.ModelAdmin):
    list_display = ('type', 'begin', 'end', 'episode', 'program', 'stream')
    list_filter = ('type', 'begin', 'program', 'stream')




admin.site.register(Track)
admin.site.register(Sound, SoundAdmin)
admin.site.register(Schedule)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Program, ProgramAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Diffusion, DiffusionAdmin)


import copy

from django.contrib     import admin
from django.forms       import Textarea
from django.db          import models

import autocomplete_light as al

from programs.models    import *


#
# Inlines
#
# TODO: inherits from the corresponding admin view
class SoundInline (admin.TabularInline):
    model = Sound
    raw_id_fields=('parent',)
    fields = ('title', 'private', 'tags', 'file', 'duration', 'fragment')
    extra = 1


class ScheduleInline (admin.TabularInline):
    model = Schedule
    extra = 1


class DiffusionInline (admin.TabularInline):
    model = Diffusion
    raw_id_fields=('parent',)
    fields = ('parent', 'type', 'date')
    extra = 1


#
# Parents
#
class MetadataAdmin (admin.ModelAdmin):
    fieldsets = [
        ( None, {
            'fields': [ 'title', 'tags' ]
        }),
        ( None, {
            'fields': [ 'date' ],
        }),
    ]


    def save_model (self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        obj.save()



class PublicationAdmin (MetadataAdmin):
    form = al.modelform_factory(
               Episode
             , fields = '__all__'
             # , autocomplete_fields = ['tracks']
             )


    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'style':'width:calc(100% - 12px);'})},
    }

    fieldsets = copy.deepcopy(MetadataAdmin.fieldsets)

    list_display = ('id', 'title', 'date', 'private')
    list_filter = ['date', 'private']
    search_fields = ['title', 'content']


    fieldsets[0][1]['fields'].insert(1, 'subtitle')
    fieldsets[0][1]['fields'] += [ 'img', 'content' ]
    fieldsets[1][1]['fields'] += [ 'parent', 'private', 'can_comment' ] #, 'meta' ],


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
    #inlines             = [ SoundInline ]
    list_filter         = ['parent'] + PublicationAdmin.list_filter

    # FIXME later: when we have thousands of tracks
    fieldsets[0][1]['fields'] += ['tracks']
    fieldsets[0][1]['fields'] += ['sounds']



admin.site.register(Track)
admin.site.register(Sound, SoundAdmin)
admin.site.register(Schedule)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Program, ProgramAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Diffusion)


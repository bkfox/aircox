import copy

from django.contrib     import admin
import programs.models  as models


#
# Inlines
#
# TODO: inherits from the corresponding admin view
class SoundFileInline (admin.TabularInline):
    model = models.SoundFile
    extra = 1


class EpisodeInline (admin.StackedInline):
    model = models.Episode
    extra = 0


class ScheduleInline (admin.TabularInline):
    model = models.Schedule
    extra = 0




class EventInline (admin.StackedInline):
    model = models.Event
    extra = 0

#
# Parents
#
class MetadataAdmin (admin.ModelAdmin):
    fieldsets = [
        ( None, {
            'fields': [ 'title', 'tags' ]
        }),
        ( 'metadata', {
            'fields': [ 'date' ],
            'classes': ['collapse']
        }),
    ]


    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        obj.save()



class PublicationAdmin (MetadataAdmin):
    fieldsets = copy.deepcopy(MetadataAdmin.fieldsets)

    list_display = ('id', 'title', 'date', 'status')
    list_filter = ['date', 'status']
    search_fields = ['title', 'content']


    def __init__ (self, *args, **kwargs):
        self.fieldsets[0][1]['fields'].insert(1, 'subtitle')
        self.fieldsets[0][1]['fields'] += [ 'img', 'content' ]
        self.fieldsets[1][1]['fields'] += [ 'parent', 'status', 'enable_comments', 'meta' ],
        return super(PublicationAdmin, self).__init__(*args, **kwargs)


#
# ModelAdmin list
#
#class TrackAdmin (MetadataAdmin):
#    fieldsets = [
#        (None, { 'fields': [ 'title', 'artist', 'version', 'tags'] } )
#    ]

class SoundFileAdmin (MetadataAdmin):
    fieldsets = [
        (None, { 'fields': ['title', 'tags', 'file', 'embed' ] } ),
        ('metadata', { 'fields': ['duration', 'date', 'podcastable', 'fragment' ] } )
    ]

    #inlines = [ EpisodeInline ]



class ArticleAdmin (PublicationAdmin):
    fieldsets           = copy.deepcopy(PublicationAdmin.fieldsets)

    fieldsets[1][1]['fields'] += ['static_page']



class ProgramAdmin (PublicationAdmin):
    fieldsets           = copy.deepcopy(PublicationAdmin.fieldsets)
    prepopulated_fields = { 'tag': ('title',) }
    inlines             = [ EpisodeInline, ScheduleInline ]

    fieldsets[1][1]['fields'] += ['email', 'url', 'tag']



class EpisodeAdmin (PublicationAdmin):
    fieldsets           = copy.deepcopy(PublicationAdmin.fieldsets)
    inlines             = [ EventInline, SoundFileInline ]
    list_filter         = ['parent'] + PublicationAdmin.list_filter

    fieldsets[0][1]['fields'] += ['tracks']



admin.site.register(models.Track)
admin.site.register(models.SoundFile, SoundFileAdmin)
admin.site.register(models.Schedule)
admin.site.register(models.Article, ArticleAdmin)
admin.site.register(models.Program, ProgramAdmin)
admin.site.register(models.Episode, EpisodeAdmin)
admin.site.register(models.Event)


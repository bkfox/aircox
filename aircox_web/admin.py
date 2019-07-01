import copy

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from content_editor.admin import ContentEditor, ContentEditorInline
from feincms3 import plugins
from feincms3.admin import TreeAdmin

from aircox import models as aircox
from . import models
from aircox.admin.playlist import TracksInline
from aircox.admin.mixins import UnrelatedInlineMixin


@admin.register(models.Site)
class SiteAdmin(ContentEditor):
    inlines = [
        ContentEditorInline.create(models.SiteRichText),
        ContentEditorInline.create(models.SiteImage),
        ContentEditorInline.create(models.SiteLink),
    ]


class PageDiffusionPlaylist(UnrelatedInlineMixin, TracksInline):
    parent_model = aircox.Diffusion
    fields = list(TracksInline.fields)
    fields.remove('timestamp')

    def get_parent(self, view_obj):
        return view_obj and view_obj.diffusion

    def save_parent(self, parent, view_obj):
        parent.save()
        view_obj.diffusion = parent
        view_obj.save()


@admin.register(models.Page)
class PageAdmin(ContentEditor):
    list_display = ["title", "parent", "status"]
    prepopulated_fields = {"slug": ("title",)}
    # readonly_fields = ('diffusion',)

    fieldsets = (
        (_('Main'), {
            'fields': ['title', 'slug', 'as_program', 'headline'],
            'classes': ('tabbed', 'uncollapse')
        }),
        (_('Settings'), {
            'fields': ['featured', 'allow_comments',
                       'status', 'static_path', 'path'],
            'classes': ('tabbed',)
        }),
        #(_('Infos'), {
        #    'fields': ['diffusion'],
        #    'classes': ('tabbed',)
        #}),
    )

    inlines = [
        ContentEditorInline.create(models.PageRichText),
        ContentEditorInline.create(models.PageImage),
    ]


@admin.register(models.DiffusionPage)
class DiffusionPageAdmin(PageAdmin):
    fieldsets = copy.deepcopy(PageAdmin.fieldsets)
    fieldsets[1][1]['fields'].insert(0, 'diffusion')

    inlines = PageAdmin.inlines + [
        PageDiffusionPlaylist
    ]

    # TODO: permissions
    #def get_inline_instances(self, request, obj=None):
    #    inlines = super().get_inline_instances(request, obj)
    #    if obj and obj.diffusion:
    #        inlines.insert(0, PageDiffusionPlaylist(self.model, self.admin_site))
    #    return inlines


@admin.register(models.ProgramPage)
class DiffusionPageAdmin(PageAdmin):
    fieldsets = copy.deepcopy(PageAdmin.fieldsets)
    fieldsets[1][1]['fields'].insert(0, 'program')

    inlines = PageAdmin.inlines + [
        PageDiffusionPlaylist
    ]




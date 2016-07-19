from django.contrib import admin
from suit.admin import SortableTabularInline, SortableModelAdmin
from suit.admin import SortableGenericTabularInline

import aircox.programs.models as programs
import aircox.cms.admin as cms
import aircox.website.models as models
import aircox.website.forms as forms


class TrackInline(SortableGenericTabularInline):
    ct_field = 'related_type'
    ct_fk_field = 'related_id'
    form = forms.TrackForm
    model = programs.Track
    sortable = 'position'
    extra = 4
    fields = ['artist', 'title', 'tags', 'info', 'position']

admin.site.register(models.Article, cms.PostAdmin)
admin.site.register(models.Program, cms.RelatedPostAdmin)
admin.site.register(models.Diffusion, cms.RelatedPostAdmin)

cms.inject_inline(programs.Diffusion, TrackInline, True)
cms.inject_related_inline(models.Program, True)
cms.inject_related_inline(models.Diffusion, True)


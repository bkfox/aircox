from django.contrib import admin
from suit.admin import SortableTabularInline, SortableModelAdmin

import aircox.programs.models as programs
import aircox.cms.admin as cms
import aircox.website.models as models
import aircox.website.forms as forms


class TrackInline (SortableTabularInline):
    fields = ['artist', 'name', 'tags', 'position']
    form = forms.TrackForm
    model = programs.Track
    sortable = 'position'
    extra = 10


class DiffusionPostAdmin(cms.RelatedPostAdmin):
    inlines = [TrackInline]


admin.site.register(models.Program, cms.RelatedPostAdmin)
admin.site.register(models.Diffusion, DiffusionPostAdmin)



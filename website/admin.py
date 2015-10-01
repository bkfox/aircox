import copy

from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.contenttypes.admin import GenericStackedInline

import programs.models as programs
from website.models import *


def add_inline (base_model, post_model, prepend = False):
    class InlineModel (admin.StackedInline):
        model = post_model
        extra = 1
        max_num = 1
        verbose_name = _('Post')

    registry = admin.site._registry
    if not base_model in registry:
        raise TypeError(str(base_model) + " not in admin registry")

    inlines = list(registry[base_model].inlines) or []
    if prepend:
        inlines.insert(0, InlineModel)
    else:
        inlines.append(InlineModel)

    registry[base_model].inlines = inlines


add_inline(programs.Program, Program)
add_inline(programs.Episode, Episode)


#class ArticleAdmin (DescriptionAdmin):
#    fieldsets = copy.deepcopy(DescriptionAdmin.fieldsets)
#
#    fieldsets[1][1]['fields'] += ['static_page']




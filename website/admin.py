import copy

from django.contrib import admin

from programs.admin import PublicationAdmin
from website.models import *

@admin.register(Article)
class ArticleAdmin (PublicationAdmin):
    fieldsets = copy.deepcopy(PublicationAdmin.fieldsets)

    fieldsets[1][1]['fields'] += ['static_page']




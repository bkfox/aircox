import copy

from django.contrib import admin

from ..models import Article
from .page import PageAdmin


__all__ = ['ArticleAdmin']


@admin.register(Article)
class ArticleAdmin(PageAdmin):
    list_display = PageAdmin.list_display + ('program',)
    list_filter = ('program',)
    # TODO: readonly field

    fieldsets = copy.deepcopy(PageAdmin.fieldsets)
    fieldsets[1][1]['fields'].insert(0, 'program')


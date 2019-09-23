import copy

from django.contrib import admin

from ..models import Article
from .page import PageAdmin


__all__ = ['ArticleAdmin']


@admin.register(Article)
class ArticleAdmin(PageAdmin):
    list_filter = PageAdmin.list_filter
    search_fields = PageAdmin.search_fields + ['parent__title']
    # TODO: readonly field



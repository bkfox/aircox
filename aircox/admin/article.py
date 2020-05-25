import copy

from django.contrib import admin

from ..models import Article
from .page import PageAdmin


__all__ = ['ArticleAdmin']


@admin.register(Article)
class ArticleAdmin(PageAdmin):
    search_fields = PageAdmin.search_fields + ('parent__title',)
    # TODO: readonly field



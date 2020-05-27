from django.db import models
from django.utils.translation import gettext_lazy as _

from .page import Page, PageQuerySet
from .program import Program, ProgramChildQuerySet


class Article(Page):
    detail_url_name = 'article-detail'

    objects = ProgramChildQuerySet.as_manager()

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')


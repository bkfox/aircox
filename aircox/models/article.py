from django.db import models
from django.utils.translation import ugettext_lazy as _

from .page import Page, PageQuerySet
from .program import Program, InProgramQuerySet


class ArticleQuerySet(InProgramQuerySet, PageQuerySet):
    pass


class Article(Page):
    detail_url_name = 'article-detail'

    program = models.ForeignKey(
        Program, models.SET_NULL,
        verbose_name=_('program'), blank=True, null=True,
        help_text=_("publish as this program's article"),
    )
    is_static = models.BooleanField(
        _('is static'), default=False,
        help_text=_('Should this article be considered as a page '
                    'instead of a blog article'),
    )

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')


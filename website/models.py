from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from programs.models import Publication


class Article (Publication):
    parent = models.ForeignKey(
        'self',
        verbose_name = _('parent'),
        blank = True, null = True,
        help_text = _('parent article'),
    )
    static_page = models.BooleanField(
        _('static page'),
        default = False,
    )
    focus = models.BooleanField(
        _('article is focus'),
        default = False,
    )
    referring_tag = models.CharField(
        _('referring tag'),
        max_length = 32,
        blank = True, null = True,
        help_text = _('tag used by other to refers to this article'),
    )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')





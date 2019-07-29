from enum import IntEnum

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from ckeditor.fields import RichTextField
from filer.fields.image import FilerImageField
from model_utils.managers import InheritanceQuerySet


__all__ = ['Page', 'PageQuerySet']


class PageQuerySet(InheritanceQuerySet):
    def published(self):
        return self.filter(status=Page.STATUS.published)


class Page(models.Model):
    """ Base class for publishable content """
    class STATUS(IntEnum):
        draft = 0x00
        published = 0x10
        trash = 0x20

    title = models.CharField(max_length=128)
    slug = models.SlugField(_('slug'), blank=True, unique=True)
    status = models.PositiveSmallIntegerField(
        _('status'),
        default=STATUS.draft,
        choices=[(int(y), _(x)) for x, y in STATUS.__members__.items()],
    )
    cover = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Cover'),
    )
    content = RichTextField(
        _('content'), blank=True, null=True,
    )
    featured = models.BooleanField(
        _('featured'), default=False,
    )
    allow_comments = models.BooleanField(
        _('allow comments'), default=True,
    )

    objects = PageQuerySet.as_manager()

    class Meta:
        abstract=True

    def __str__(self):
        return '{}: {}'.format(self._meta.verbose_name,
                               self.title or self.pk)

    def save(self, *args, **kwargs):
        # TODO: ensure unique slug
        if not self.slug:
            self.slug = slugify(self.title)
        print(self.title, '--', self.slug)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(self.detail_url_name, kwargs={'slug': self.slug}) \
            if self.is_published else ''

    @property
    def is_published(self):
        return self.status == self.STATUS.published



from enum import IntEnum

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from ckeditor.fields import RichTextField
from filer.fields.image import FilerImageField
from model_utils.managers import InheritanceQuerySet

from .station import Station


__all__ = ['PageQuerySet', 'Page', 'NavItem']


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

    detail_url_name = None

    class Meta:
        abstract = True

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
            if self.is_published else '#'

    @property
    def is_draft(self):
        return self.status == self.STATUS.draft

    @property
    def is_published(self):
        return self.status == self.STATUS.published

    @property
    def is_trash(self):
        return self.status == self.STATUS.trash


class NavItem(models.Model):
    """ Navigation menu items """
    station = models.ForeignKey(
        Station, models.CASCADE, verbose_name=_('station'))
    menu = models.SlugField(_('menu'), max_length=24)
    order = models.PositiveSmallIntegerField(_('order'))
    text = models.CharField(_('title'), max_length=64)
    url = models.CharField(_('url'), max_length=256, blank=True, null=True)
    #target_type = models.ForeignKey(
    #    ContentType, models.CASCADE, blank=True, null=True)
    #target_id = models.PositiveSmallIntegerField(blank=True, null=True)
    #target = GenericForeignKey('target_type', 'target_id')

    class Meta:
        verbose_name = _('Menu item')
        ordering = ('order', 'pk')

    is_active = False

    def get_is_active(self, url):
        """ Return True if navigation item is active for this url. """
        return self.url and url.startswith(self.url)

    def render(self, request, css_class='', active_class=''):
        if active_class and request.path.startswith(self.url):
            css_class += ' ' + active_class

        if not self.url:
            return self.text
        elif not css_class:
            return format_html('<a href="{}">{}</a>', self.url, self.text)
        else:
            return format_html('<a href="{}" class="{}">{}</a>', self.url,
                               css_class, self.text)


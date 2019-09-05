from enum import IntEnum
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.text import slugify
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from ckeditor.fields import RichTextField
from filer.fields.image import FilerImageField
from model_utils.managers import InheritanceQuerySet

from .station import Station


__all__ = ['Category', 'PageQuerySet', 'Page', 'NavItem']


headline_re = re.compile(r'(<p>)?'
                         r'(?P<headline>[^\n]{1,140}(\n|[^\.]*?\.))'
                         r'(</p>)?')


class Category(models.Model):
    title = models.CharField(_('title'), max_length=64)
    slug = models.SlugField(_('slug'), max_length=64, db_index=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.title


class PageQuerySet(InheritanceQuerySet):
    def draft(self):
        return self.filter(status=Page.STATUS_DRAFT)

    def published(self):
        return self.filter(status=Page.STATUS_PUBLISHED)

    def trash(self):
        return self.filter(status=Page.STATUS_TRASH)


class Page(models.Model):
    """ Base class for publishable content """
    STATUS_DRAFT = 0x00
    STATUS_PUBLISHED = 0x10
    STATUS_TRASH = 0x20
    STATUS_CHOICES = (
        (STATUS_DRAFT, _('draft')),
        (STATUS_PUBLISHED, _('published')),
        (STATUS_TRASH, _('trash')),
    )

    title = models.CharField(max_length=128)
    slug = models.SlugField(_('slug'), blank=True, unique=True)
    status = models.PositiveSmallIntegerField(
        _('status'), default=STATUS_DRAFT, choices=STATUS_CHOICES,
    )
    category = models.ForeignKey(
        Category, models.SET_NULL,
        verbose_name=_('category'), blank=True, null=True, db_index=True
    )
    cover = FilerImageField(
        on_delete=models.SET_NULL,
        verbose_name=_('Cover'), null=True, blank=True,
    )
    content = RichTextField(
        _('content'), blank=True, null=True,
    )
    date = models.DateTimeField(default=tz.now)
    featured = models.BooleanField(
        _('featured'), default=False,
    )
    allow_comments = models.BooleanField(
        _('allow comments'), default=True,
    )

    objects = PageQuerySet.as_manager()

    detail_url_name = None


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
        return self.status == self.STATUS_DRAFT

    @property
    def is_published(self):
        return self.status == self.STATUS_PUBLISHED

    @property
    def is_trash(self):
        return self.status == self.STATUS_TRASH

    @cached_property
    def headline(self):
        if not self.content:
            return ''
        headline = headline_re.search(self.content)
        return headline.groupdict()['headline'] if headline else ''

    @classmethod
    def get_init_kwargs_from(cls, page, **kwargs):
        kwargs.setdefault('cover', page.cover)
        kwargs.setdefault('category', page.category)
        return kwargs

    @classmethod
    def from_page(cls, page, **kwargs):
        return cls(**cls.get_init_kwargs_from(page, **kwargs))


class Comment(models.Model):
    page = models.ForeignKey(
        Page, models.CASCADE, verbose_name=_('related page'),
    )
    nickname = models.CharField(_('nickname'), max_length=32)
    email = models.EmailField(_('email'), max_length=32)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField(_('content'), max_length=1024)


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


from enum import IntEnum
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.text import slugify
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

import bleach
from ckeditor_uploader.fields import RichTextUploadingField
from filer.fields.image import FilerImageField
from model_utils.managers import InheritanceQuerySet

from .station import Station


__all__ = ['Category', 'PageQuerySet', 'Page', 'Comment', 'NavItem']


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

    def parent(self, parent=None, id=None):
        """ Return pages having this parent. """
        return self.filter(parent=parent) if id is None else \
               self.filter(parent__id=id)


class BasePage(models.Model):
    """ Base class for publishable content """
    STATUS_DRAFT = 0x00
    STATUS_PUBLISHED = 0x10
    STATUS_TRASH = 0x20
    STATUS_CHOICES = (
        (STATUS_DRAFT, _('draft')),
        (STATUS_PUBLISHED, _('published')),
        (STATUS_TRASH, _('trash')),
    )

    parent = models.ForeignKey('self', models.CASCADE, blank=True, null=True,
                               db_index=True, related_name='child_set')
    title = models.CharField(max_length=100)
    slug = models.SlugField(_('slug'), max_length=120, blank=True, unique=True,
                               db_index=True)
    status = models.PositiveSmallIntegerField(
        _('status'), default=STATUS_DRAFT, choices=STATUS_CHOICES,
    )
    cover = FilerImageField(
        on_delete=models.SET_NULL,
        verbose_name=_('cover'), null=True, blank=True,
    )
    content = RichTextUploadingField(
        _('content'), blank=True, null=True,
    )

    objects = PageQuerySet.as_manager()

    detail_url_name = None
    item_template_name = 'aircox/widgets/page_item.html'

    class Meta:
        abstract = True

    def __str__(self):
        return '{}'.format(self.title or self.pk)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
            count = Page.objects.filter(slug__startswith=self.slug).count()
            if count:
                self.slug += '-' + str(count)

        if self.parent and not self.cover:
            self.cover = self.parent.cover
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

    @property
    def display_title(self):
        if self.is_published():
            return self.title
        return self.parent.display_title()

    @cached_property
    def headline(self):
        if not self.content:
            return ''
        content = bleach.clean(self.content, tags=[], strip=True)
        headline = headline_re.search(content)
        return mark_safe(headline.groupdict()['headline']) if headline else ''

    @classmethod
    def get_init_kwargs_from(cls, page, **kwargs):
        kwargs.setdefault('cover', page.cover)
        kwargs.setdefault('category', page.category)
        return kwargs

    @classmethod
    def from_page(cls, page, **kwargs):
        return cls(**cls.get_init_kwargs_from(page, **kwargs))


class Page(BasePage):
    """ Base Page model used for articles and other dated content. """
    category = models.ForeignKey(
        Category, models.SET_NULL,
        verbose_name=_('category'), blank=True, null=True, db_index=True
    )
    pub_date = models.DateTimeField(blank=True, null=True)
    featured = models.BooleanField(
        _('featured'), default=False,
    )
    allow_comments = models.BooleanField(
        _('allow comments'), default=True,
    )

    class Meta:
        verbose_name = _('Publication')
        verbose_name_plural = _('Publications')

    def save(self, *args, **kwargs):
        if self.is_published and self.pub_date is None:
            self.pub_date = tz.now()
        elif not self.is_published:
            self.pub_date = None

        if self.parent and not self.category:
            self.category = self.parent.category
        super().save(*args, **kwargs)


class StaticPage(BasePage):
    """ Static page that eventually can be attached to a specific view. """
    detail_url_name = 'static-page-detail'

    ATTACH_TO_HOME = 0x00
    ATTACH_TO_DIFFUSIONS = 0x01
    ATTACH_TO_LOGS = 0x02
    ATTACH_TO_PROGRAMS = 0x03
    ATTACH_TO_EPISODES = 0x04
    ATTACH_TO_ARTICLES = 0x05

    ATTACH_TO_CHOICES = (
        (ATTACH_TO_HOME, _('Home page')),
        (ATTACH_TO_DIFFUSIONS, _('Diffusions page')),
        (ATTACH_TO_LOGS, _('Logs page')),
        (ATTACH_TO_PROGRAMS, _('Programs list')),
        (ATTACH_TO_EPISODES, _('Episodes list')),
        (ATTACH_TO_ARTICLES, _('Articles list')),
    )
    VIEWS = {
        ATTACH_TO_HOME: 'home',
        ATTACH_TO_DIFFUSIONS: 'diffusion-list',
        ATTACH_TO_LOGS: 'log-list',
        ATTACH_TO_PROGRAMS: 'program-list',
        ATTACH_TO_EPISODES: 'episode-list',
        ATTACH_TO_ARTICLES: 'article-list',
    }

    attach_to = models.SmallIntegerField(
        _('attach to'), choices=ATTACH_TO_CHOICES, blank=True, null=True,
        help_text=_('display this page content to related element'),
    )

    def get_absolute_url(self):
        if self.attach_to:
            return reverse(self.VIEWS[self.attach_to])
        return super().get_absolute_url()


class Comment(models.Model):
    page = models.ForeignKey(
        Page, models.CASCADE, verbose_name=_('related page'),
        db_index=True,
        # TODO: allow_comment filter
    )
    nickname = models.CharField(_('nickname'), max_length=32)
    email = models.EmailField(_('email'), max_length=32)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField(_('content'), max_length=1024)

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')


class NavItem(models.Model):
    """ Navigation menu items """
    station = models.ForeignKey(
        Station, models.CASCADE, verbose_name=_('station'))
    menu = models.SlugField(_('menu'), max_length=24)
    order = models.PositiveSmallIntegerField(_('order'))
    text = models.CharField(_('title'), max_length=64)
    url = models.CharField(_('url'), max_length=256, blank=True, null=True)
    page = models.ForeignKey(StaticPage, models.CASCADE, db_index=True,
                             verbose_name=_('page'), blank=True, null=True)
    class Meta:
        verbose_name = _('Menu item')
        verbose_name_plural = _('Menu items')
        ordering = ('order', 'pk')

    def get_url(self):
        return self.url if self.url else \
            self.page.get_absolute_url() if self.page else None

    def render(self, request, css_class='', active_class=''):
        url = self.get_url()
        if active_class and request.path.startswith(url):
            css_class += ' ' + active_class

        if not url:
            return self.text
        elif not css_class:
            return format_html('<a href="{}">{}</a>', url, self.text)
        else:
            return format_html('<a href="{}" class="{}">{}</a>', url,
                               css_class, self.text)


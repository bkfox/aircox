from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape, format_html, mark_safe
from django.urls import reverse

from .image import ImageBase, Image
from .richtext import RichText


__all__ = ['ImageBase', 'Image', 'RichText']


class Link(models.Model):
    url = models.CharField(
        _('url'), max_length=128, null=True, blank=True,
    )
    page = models.ForeignKey(
        'Page', models.SET_NULL, null=True, blank=True,
        verbose_name=_('Link to a page')
    )
    text = models.CharField(_('text'), max_length=64, null=True, blank=True)
    info = models.CharField(_('info'), max_length=128, null=True, blank=True,
                            help_text=_('link description displayed as tooltip'))
    blank = models.BooleanField(_('new window'), default=False,
                                help_text=_('open in a new window'))
    css_class=""

    def get_url(self):
        if self.page:
            return self.page.path #reverse('page', args=[self.page.path])
        return self.url or ''

    def render(self):
        # FIXME: quote
        return format_html(
            '<a href="{}" title="{}"{}>{}</a>',
            self.get_url(), escape(self.info),
            ' class=' + escape(self.css_class) + ''
            if self.css_class else '',
            self.text or (self.page and self.page.title) or '',
        )

    class Meta:
        abstract = True


class Search(models.Model):
    class Meta:
        abstract = True



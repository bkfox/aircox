from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import models as auth

from content_editor.models import Region, create_plugin_base
from feincms3 import plugins
from feincms3.pages import AbstractPage

from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices
from filer.fields.image import FilerImageField

from aircox import models as aircox


class Site(models.Model):
    station = models.ForeignKey(
        aircox.Station, on_delete=models.SET_NULL, null=True,
    )

    # main settings
    title = models.CharField(
        _('Title'), max_length=32,
        help_text=_('Website title used at various places'),
    )
    logo = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Logo'),
        related_name='+',
    )
    favicon = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Favicon'),
        related_name='+',
    )

    # meta descriptors
    description = models.CharField(
        _('Description'), max_length=128,
        blank=True, null=True,
    )
    tags = models.CharField(
        _('Tags'), max_length=128,
        blank=True, null=True,
    )

    regions = [
        Region(key='topnav', title=_('Navigation'), inherited=True),
        Region(key='sidenav', title=_('Side Navigation'), inherited=True),
    ]


SitePlugin = create_plugin_base(Site)

class SiteRichText(plugins.richtext.RichText, SitePlugin):
    pass


class SiteImage(plugins.image.Image, SitePlugin):
    caption = models.CharField(_("caption"), max_length=200, blank=True)



class Page(AbstractPage, TimeStampedModel, StatusModel):
    STATUS = Choices('draft', 'published')
    regions = [
        Region(key="main", title=_("Content")),
    ]

    # metadata
    by = models.ForeignKey(
        auth.User, models.SET_NULL, blank=True, null=True,
        verbose_name=_('Author'),
    )
    by_program = models.ForeignKey(
        aircox.Program, models.SET_NULL, blank=True, null=True,
        related_name='authored_pages',
        limit_choices_to={'schedule__isnull': False},
        verbose_name=_('Show program as author'),
        help_text=_("If nothing is selected, display user's name"),
    )

    # options
    show_author = models.BooleanField(
        _('Show author'), default=True,
    )
    featured = models.BooleanField(
        _('featured'), default=False,
    )
    allow_comments = models.BooleanField(
        _('allow comments'), default=True,
    )

    # content
    title = models.CharField(
        _('title'), max_length=64,
    )
    summary = models.TextField(
        _('Summary'),
        max_length=128, blank=True, null=True,
    )
    cover = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Cover'),
    )

    diffusion = models.OneToOneField(
        aircox.Diffusion, models.CASCADE,
        blank=True, null=True,
    )
    program = models.OneToOneField(
        aircox.Program, models.CASCADE,
        blank=True, null=True,
    )


PagePlugin = create_plugin_base(Page)

class PageRichText(plugins.richtext.RichText, PagePlugin):
    pass


class PageImage(plugins.image.Image, PagePlugin):
    caption = models.CharField(_("caption"), max_length=200, blank=True)




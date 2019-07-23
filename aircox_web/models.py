from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from content_editor.models import Region, create_plugin_base

from model_utils.models import TimeStampedModel, StatusModel
from model_utils.managers import InheritanceQuerySet
from model_utils import Choices
from filer.fields.image import FilerImageField

from aircox import models as aircox
from . import plugins


class Site(models.Model):
    station = models.ForeignKey(
        aircox.Station, on_delete=models.SET_NULL, null=True,
    )
    #hosts = models.TextField(
    #    _('hosts'),
    #    help_text=_('website addresses (one per line)'),
    #)

    # main settings
    title = models.CharField(
        _('title'), max_length=32,
        help_text=_('website title displayed to users'),
    )
    logo = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('logo'),
        related_name='+',
    )
    favicon = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('favicon'),
        related_name='+',
    )
    default = models.BooleanField(_('is default'),
        default=False,
        help_text=_('use this website by default'),
    )

    # meta descriptors
    description = models.CharField(
        _('description'), max_length=128,
        blank=True, null=True,
    )
    tags = models.CharField(
        _('tags'), max_length=128,
        blank=True, null=True,
    )

    regions = [
        Region(key='topnav', title=_('Navigation'), inherited=True),
        Region(key='sidenav', title=_('Side Navigation'), inherited=True),
    ]


SitePlugin = create_plugin_base(Site)

class SiteRichText(plugins.RichText, SitePlugin):
    pass

class SiteImage(plugins.Image, SitePlugin):
    pass

class SiteLink(plugins.Link, SitePlugin):
    css_class="navbar-item"


#-----------------------------------------------------------------------
class PageQueryset(InheritanceQuerySet):
    def live(self):
        return self.filter(status=Page.STATUS.published)

    def descendants(self, page, direct=True, inclusive=True):
        qs = self.filter(parent=page) if direct else \
             self.filter(path__startswith=page.path)
        if not inclusive:
            qs = qs.exclude(pk=page.pk)
        return qs

    def ancestors(self, page, inclusive=True):
        path, paths = page.path, []
        index = path.find('/')
        while index != -1 and index+1 < len(path):
            paths.append(path[0:index+1])
            index = path.find('/', index+1)
        return self.filter(path__in=paths)


class Page(StatusModel):
    """
    Base class for views whose url path can be defined by users.
    Page parenting is based on foreignkey to parent and page path.
    """
    STATUS = Choices('draft', 'published', 'trash')

    parent = models.ForeignKey(
        'self', models.CASCADE,
        verbose_name=_('parent page'),
        blank=True, null=True,
    )
    title = models.CharField(max_length=128)
    slug = models.SlugField(_('slug'))
    headline = models.TextField(
        _('headline'), max_length=128, blank=True, null=True,
    )

    objects = PageQueryset.as_manager()

    @property
    def path(self):
        return reverse('page', kwargs={'slug': self.slug})

    def get_view_class(self):
        """ Page view class"""
        raise NotImplementedError('not implemented')

    def view(self, request, *args, site=None, **kwargs):
        """ Page view function """
        view = self.get_view_class().as_view(site=site, page=self)
        return view(request, *args, **kwargs)

    def __str__(self):
        return '{}: {}'.format(self._meta.verbose_name,
                               self.title or self.pk)


class Article(Page):
    """ User's pages """
    regions = [
        Region(key="content", title=_("Content")),
    ]

    # metadata
    as_program = models.ForeignKey(
        aircox.Program, models.SET_NULL, blank=True, null=True,
        related_name='+',
        # SO#51948640
        # limit_choices_to={'schedule__isnull': False},
        verbose_name=_('Show program as author'),
        help_text=_("Show program as author"),
    )

    # options
    featured = models.BooleanField(
        _('featured'), default=False,
    )
    allow_comments = models.BooleanField(
        _('allow comments'), default=True,
    )

    # content
    cover = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Cover'),
    )



class DiffusionPage(Article):
    diffusion = models.OneToOneField(
        aircox.Diffusion, models.CASCADE,
        related_name='page',
        limit_choices_to={'initial__isnull': True}
    )

    @property
    def path(self):
        return reverse('diffusion-page', kwargs={'slug': self.slug})


class ProgramPage(Article):
    detail_url_name = 'program-page'

    program = models.OneToOneField(
        aircox.Program, models.CASCADE,
        related_name='page',
    )

    @property
    def path(self):
        return reverse('program-page', kwargs={'slug': self.slug})


#-----------------------------------------------------------------------
ArticlePlugin = create_plugin_base(Article)

class ArticleRichText(plugins.RichText, ArticlePlugin):
    pass

class ArticleImage(plugins.Image, ArticlePlugin):
    pass




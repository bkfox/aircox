from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Concat, Substr
from django.utils.translation import ugettext_lazy as _

from content_editor.models import Region, create_plugin_base

from model_utils.models import TimeStampedModel, StatusModel
from model_utils.managers import InheritanceQuerySet
from model_utils import Choices
from filer.fields.image import FilerImageField

from aircox import models as aircox
from . import plugins
from .converters import PagePathConverter


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

    default = models.BooleanField(_('default site'),
        default=False,
        help_text=_('Use as default site'),
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

class SiteRichText(plugins.RichText, SitePlugin):
    pass

class SiteImage(plugins.Image, SitePlugin):
    pass

class SiteLink(plugins.Link, SitePlugin):
    css_class="navbar-item"


#-----------------------------------------------------------------------
class PageQueryset(InheritanceQuerySet):
    def active(self):
        return self.filter(Q(status=Page.STATUS.announced) |
                           Q(status=Page.STATUS.published))

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
    STATUS = Choices('draft', 'announced', 'published')

    parent = models.ForeignKey(
        'self', models.CASCADE,
        verbose_name=_('parent page'),
        blank=True, null=True,
    )
    title = models.CharField(max_length=128)
    slug = models.SlugField(_('slug'))
    path = models.CharField(
        _("path"), max_length=1000,
        blank=True, db_index=True, unique=True,
        validators=[RegexValidator(
            regex=PagePathConverter.regex,
            message=_('Path accepts alphanumeric and "_-" characters '
                      'and must be surrounded by "/"')
        )],
    )
    static_path = models.BooleanField(
        _('static path'), default=False,
        # FIXME: help
        help_text=_('Update path using parent\'s page path and page title')
    )
    headline = models.TextField(
        _('headline'), max_length=128, blank=True, null=True,
    )

    objects = PageQueryset.as_manager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_path = self.path
        self._initial_parent = self.parent
        self._initial_slug = self.slug

    def get_view_class(self):
        """ Page view class"""
        raise NotImplementedError('not implemented')

    def view(self, request, *args, site=None, **kwargs):
        """ Page view function """
        view = self.get_view_class().as_view(site=site, page=self)
        return view(request, *args, **kwargs)

    def update_descendants(self):
        """ Update descendants pages' path if required. """
        if self.path == self._initial_path:
            return

        # FIXME: draft -> draft children?
        # FIXME: Page.objects (can't use Page since its an abstract model)
        if len(self._initial_path):
            expr = Concat('path', Substr(F('path'), len(self._initial_path)))
            Page.objects.filter(path__startswith=self._initial_path) \
                        .update(path=expr)

    def sync_generations(self, update_descendants=True):
        """
        Update fields (path, ...) based on parent. Update childrens if
        ``update_descendants`` is True.
        """
        # TODO: set parent based on path (when static path)
        # TODO: ensure unique path fallback
        if self.path == self._initial_path and \
                self.slug == self._initial_slug and \
                self.parent == self._initial_parent:
            return

        if not self.title or not self.path or self.static_path and \
                self.slug != self._initial_slug:
            self.path = self.parent.path + self.slug \
                if self.parent is not None else '/' + self.slug

        if self.path[0] != '/':
            self.path = '/' + self.path
        if self.path[-1] != '/':
            self.path += '/'
        if update_descendants:
            self.update_descendants()

    def save(self, *args, update_descendants=True, **kwargs):
        self.sync_generations(update_descendants)
        super().save(*args, **kwargs)

    def __str__(self):
        return '{}: {}'.format(self._meta.verbose_name,
                               self.title or self.pk)


class Article(Page, TimeStampedModel):
    """ User's pages """
    regions = [
        Region(key="content", title=_("Content")),
    ]

    # metadata
    as_program = models.ForeignKey(
        aircox.Program, models.SET_NULL, blank=True, null=True,
        related_name='published_pages',
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

    def get_view_class(self):
        from .views import ArticleView
        return ArticleView


class DiffusionPage(Article):
    diffusion = models.OneToOneField(
        aircox.Diffusion, models.CASCADE,
        related_name='page',
    )


class ProgramPage(Article):
    program = models.OneToOneField(
        aircox.Program, models.CASCADE,
        related_name='page',
    )

    def get_view_class(self):
        from .views import ProgramView
        return ProgramView


#-----------------------------------------------------------------------
ArticlePlugin = create_plugin_base(Article)

class ArticleRichText(plugins.RichText, ArticlePlugin):
    pass

class ArticleImage(plugins.Image, ArticlePlugin):
    pass




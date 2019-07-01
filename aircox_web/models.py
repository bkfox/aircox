from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F
from django.db.models.functions import Concat, Substr
from django.utils.translation import ugettext_lazy as _

from content_editor.models import Region, create_plugin_base

from model_utils.models import TimeStampedModel, StatusModel
from model_utils.managers import InheritanceManager
from model_utils import Choices
from filer.fields.image import FilerImageField

from aircox import models as aircox
from . import plugins


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
class BasePage(StatusModel):
    """
    Base abstract class for views whose url path is defined by users.
    Page parenting is based on foreignkey to parent and page path.

    Inspired by Feincms3.
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
        validators=[
            RegexValidator(
                regex=r"^/(|.+/)$",
                message=_("Path must start and end with a slash (/)."),
            )
        ],
    )
    static_path = models.BooleanField(
        _('static path'), default=False,
        help_text=_('Update path using parent\'s page path and page title')
    )

    objects = InheritanceManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_path = self.path
        self._initial_parent = self.parent
        self._initial_slug = self.slug

    def view(self, request, *args, **kwargs):
        """ Page view function """
        from django.http import HttpResponse
        return HttpResponse('Not implemented')

    def update_descendants(self):
        """ Update descendants pages' path if required. """
        if self.path == self._initial_path:
            return

        # FIXME: draft -> draft children?
        expr = Concat(self.path, Substr(F('path'), len(self._initial_path)))
        BasePage.objects.filter(path__startswith=self._initial_path) \
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
            self.path = self.parent.path + '/' + self.slug \
                if self.parent is not None else '/' + self.slug

        if self.path[-1] != '/':
            self.path += '/'
        if self.path[0] != '/':
            self.path = '/' + self.path
        if update_descendants:
            self.update_descendants()

    def save(self, *args, update_descendants=True, **kwargs):
        self.sync_generations(update_descendants)
        super().save(*args, **kwargs)


class Page(BasePage, TimeStampedModel):
    """ User's pages """
    regions = [
        Region(key="main", title=_("Content")),
    ]

    # metadata
    as_program = models.ForeignKey(
        aircox.Program, models.SET_NULL, blank=True, null=True,
        related_name='published_pages',
        limit_choices_to={'schedule__isnull': False},
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
    headline = models.TextField(
        _('headline'), max_length=128, blank=True, null=True,
    )
    cover = FilerImageField(
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_('Cover'),
    )

    def get_view_class(self):
        from .views import PageView
        return PageView

    def view(self, request, *args, **kwargs):
        """ Page view function """
        view = self.get_view_class().as_view()
        return view(request, *args, **kwargs)


class DiffusionPage(Page):
    diffusion = models.OneToOneField(
        aircox.Diffusion, models.CASCADE,
        blank=True, null=True,
    )


class ProgramPage(Page):
    program = models.OneToOneField(
        aircox.Program, models.CASCADE,
        blank=True, null=True,
    )


#-----------------------------------------------------------------------
PagePlugin = create_plugin_base(Page)

class PageRichText(plugins.RichText, PagePlugin):
    pass

class PageImage(plugins.Image, PagePlugin):
    pass




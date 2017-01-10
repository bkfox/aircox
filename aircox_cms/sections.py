import datetime
import re
from enum import IntEnum

from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.functional import cached_property
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel, FieldRowPanel, \
        MultiFieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel
from wagtail.wagtailsearch import index

from wagtail.wagtailcore.utils import camelcase_to_underscore

# snippets
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
from wagtail.wagtailsnippets.models import register_snippet

# tags
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

# aircox
import aircox.models


def related_pages_filter(reset_cache=False):
    """
    Return a dict that can be used to filter foreignkey to pages'
    subtype declared in aircox_cms.models.

    This value is stored in cache, but it is possible to reset the
    cache using the `reset_cache` parameter.
    """
    if not reset_cache and hasattr(related_pages_filter, 'cache'):
        return related_pages_filter.cache

    import aircox_cms.models as cms
    import inspect
    related_pages_filter.cache = {
        'model__in': list(name.lower() for name, member in
            inspect.getmembers(cms,
                lambda x: inspect.isclass(x) and issubclass(x, Page)
            )
            if member != Page
        ),
    }
    return related_pages_filter.cache


class ListItem:
    """
    Generic normalized element to add item in lists that are not based
    on Publication.
    """
    title = ''
    summary = ''
    url = ''
    cover = None
    date = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.specific = self


#
#   Base
#
class RelatedLinkBase(Orderable):
    url = models.URLField(
        _('url'),
        null=True, blank=True,
        help_text = _('URL of the link'),
    )
    page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('Use a page instead of a URL')
    )
    icon = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('icon'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _(
            'icon from the gallery'
        ),
    )
    icon_path = models.CharField(
        _('icon path'),
        null=True, blank=True,
        max_length=128,
        help_text = _(
            'icon from a given URL or path in the directory of static files'
        )
    )
    text = models.CharField(
        _('text'),
        max_length = 64,
        null = True, blank=True,
        help_text = _('text of the link'),
    )
    info = models.CharField(
        _('info'),
        max_length = 128,
        null=True, blank=True,
        help_text = _(
            'description displayed in a popup when the mouse hovers '
            'the link'
        )
    )

    class Meta:
        abstract = True

    panels = [
        MultiFieldPanel([
            FieldPanel('text'),
            FieldPanel('info'),
            ImageChooserPanel('icon'),
            FieldPanel('icon_path'),
            FieldPanel('url'),
            PageChooserPanel('page'),
        ], heading=_('link'))
    ]

    def icon_url(self):
        """
        Return icon_path as a complete url, since it can either be an
        url or a path to static file.
        """
        if self.icon_path.startswith('http://') or \
                self.icon_path.startswith('https://'):
            return self.icon_path
        return static(self.icon_path)

    def as_dict(self):
        """
        Return compiled values from parameters as dict with
        'url', 'icon', 'text'
        """
        if self.page:
            url, text = self.page.url, self.text or self.page.title
        else:
            url, text = self.url, self.text or self.url
        return {
            'url': url,
            'text': text,
            'info': self.info,
            'icon': self.icon,
            'icon_path': self.icon_path and self.icon_url(),
        }


class ListBase(models.Model):
    """
    Generic list
    """
    class DateFilter(IntEnum):
        none = 0x00
        previous = 0x01
        next = 0x02
        before_related = 0x03,
        after_related = 0x04,

    date_filter = models.SmallIntegerField(
        verbose_name = _('filter by date'),
        choices = [ (int(y), _(x.replace('_', ' ')))
                        for x,y in DateFilter.__members__.items() ],
        blank = True, null = True,
    )
    model = models.ForeignKey(
        ContentType,
        verbose_name = _('filter by type'),
        blank = True, null = True,
        on_delete=models.SET_NULL,
        help_text = _('if set, select only elements that are of this type'),
        limit_choices_to = related_pages_filter,
    )
    related = models.ForeignKey(
        Page,
        verbose_name = _('filter by a related page'),
        blank = True, null = True,
        on_delete=models.SET_NULL,
        help_text = _('if set, select children or siblings related to this page'),
    )
    siblings = models.BooleanField(
        verbose_name = _('select siblings of related'),
        default = False,
        help_text = _(
            'if checked, related publications are siblings instead of '
            'the children.'
        ),
    )
    asc = models.BooleanField(
        verbose_name = _('ascending order'),
        default = True,
        help_text = _('if selected sort list in the ascending order by date')
    )

    class Meta:
        abstract = True

    panels = [
        MultiFieldPanel([
            FieldPanel('model'),
            PageChooserPanel('related'),
            FieldPanel('siblings'),
        ], heading=_('filters')),
        MultiFieldPanel([
            FieldPanel('date_filter'),
            FieldPanel('asc'),
        ], heading=_('sorting'))
    ]

    def __get_related(self, qs):
        related = self.related and self.related.specific

        if self.siblings:
            qs = qs.sibling_of(related)
        else:
            qs = qs.descendant_of(related)

        date = related.date if hasattr(related, 'date') else \
                related.first_published_at
        if self.date_filter == self.DateFilter.before_related:
            qs = qs.filter(date__lt = date)
        elif self.date_filter == self.DateFilter.after_related:
            qs = qs.filter(date__gte = date)
        return qs

    def get_queryset(self):
        """
        Get queryset based on the arguments. This class is intended to be
        reusable by other classes if needed.
        """
        from aircox_cms.models import Publication

        # model
        if self.model:
            qs = self.model.model_class().objects.all()
        else:
            qs = Publication.objects.all()
        qs = qs.live().not_in_menu()

        # related
        if self.related:
            qs = self.__get_related(qs)

        # date
        date = tz.now()
        if self.date_filter == self.DateFilter.previous:
            qs = qs.filter(date__lt = date)
        elif self.date_filter == self.DateFilter.next:
            qs = qs.filter(date__gte = date)

        # sort
        if self.asc:
            return qs.order_by('date', 'pk')
        return qs.order_by('-date', '-pk')

    def to_url(self, list_page = None, **kwargs):
        """
        Return a url parameters from self. Extra named parameters are used
        to override values of self or add some to the parameters.

        If there is related field use it to get the page, otherwise use the
        given list_page or the first DynamicListPage it finds.
        """
        import aircox_cms.models as models

        params = {
            'date_filter': self.get_date_filter_display(),
            'model': self.model and self.model.model,
            'asc': self.asc,
            'related': self.related,
            'siblings': self.siblings,
        }
        params.update(kwargs)

        page = params.get('related') or list_page or \
                models.DynamicListPage.objects.all().first()

        if params.get('related'):
            params['related'] = True

        params = '&'.join([
            key if value == True else '{}={}'.format(key, value)
            for key, value in params.items()
            if value
        ])
        return page.url + '?' + params

    @classmethod
    def from_request(cl, request, related = None, context = None,
                     *args, **kwargs):
        """
        Return a queryset from the request's GET parameters. Context
        can be used to update relative informations.

        This function can be used by other views if needed

        Parameters:
        * date_filter: one of DateFilter attribute's key.
        * model:    ['program','diffusion','event'] type of the publication
        * asc:      if present, sort ascending instead of descending
        * related:  children of the thread passed in arguments only
        * siblings: sibling of the related instead of children

        * tag:      tag to search for
        * search:   query to search in the publications
        * page:     page number

        Context's fields:
        * object_list:      the final queryset
        * list_selector:    dict of { 'tag_query', 'search_query' } plus
                            arguments passed to ListBase.get_base_queryset
        * paginator:        paginator object
        """
        def set(key, value):
            if context is not None:
                context[key] = value

        date_filter = request.GET.get('date_filter')
        model = request.GET.get('model')

        kwargs = {
            'date_filter':
                int(getattr(cl.DateFilter, date_filter))
                if date_filter and hasattr(cl.DateFilter, date_filter)
                else None,
            'model':
                ProgramPage if model == 'program' else
                DiffusionPage if model == 'diffusion' else
                EventPage if model == 'event' else None,
            'related': 'related' in request.GET and related,
            'siblings': 'siblings' in request.GET,
            'asc': 'asc' in request.GET,
        }

        base_list = cl(**{ k:v for k,v in kwargs.items() if v })
        qs = base_list.get_queryset()

        # filter by tag
        tag = request.GET.get('tag')
        if tag:
            kwargs['terms'] = tag
            qs = qs.filter(tags__name = tag)

        # search
        search = request.GET.get('search')
        if search:
            kwargs['terms'] = search
            qs = qs.search(search)

        set('list_selector', kwargs)

        # paginator
        if qs:
            paginator = Paginator(qs, 30)
            try:
                qs = paginator.page(request.GET.get('page') or 1)
            except PageNotAnInteger:
                qs = paginator.page(1)
            except EmptyPage:
                qs = parginator.page(paginator.num_pages)
            set('paginator', paginator)
        set('object_list', qs)
        return qs


class DatedListBase(models.Model):
    """
    List that display items per days. Renders a navigation section on the
    top.
    """
    nav_days = models.SmallIntegerField(
        _('navigation days count'),
        default = 7,
        help_text = _('number of days to display in the navigation header '
                      'when we use dates')
    )
    nav_per_week = models.BooleanField(
        _('navigation per week'),
        default = False,
        help_text = _('if selected, show dates navigation per weeks instead '
                      'of show days equally around the current date')
    )

    class Meta:
        abstract = True

    panels = [
        MultiFieldPanel([
            FieldPanel('nav_days'),
            FieldPanel('nav_per_week'),
        ], heading=_('Navigation')),
    ]

    @staticmethod
    def str_to_date(date):
        """
        Parse a string and return a regular date or None.
        Format is either "YYYY/MM/DD" or "YYYY-MM-DD" or "YYYYMMDD"
        """
        try:
            exp = r'(?P<year>[0-9]{4})(-|\/)?(?P<month>[0-9]{1,2})(-|\/)?' \
                  r'(?P<day>[0-9]{1,2})'
            date = re.match(exp, date).groupdict()
            return datetime.date(
                year = int(date['year']), month = int(date['month']),
                day = int(date['day'])
            )
        except:
            return None

    def get_nav_dates(self, date):
        """
        Return a list of dates availables for the navigation
        """
        if self.nav_per_week:
            first = date.weekday()
        else:
            first = int((self.nav_days - 1) / 2)
        first = date - tz.timedelta(days = first)
        return [ first + tz.timedelta(days=i)
                    for i in range(0, self.nav_days) ]

    def get_date_context(self, date = None):
        """
        Return a dict that can be added to the context to be used by
        a date_list.
        """
        today = tz.now().date()
        if not date:
            date = today

        # next/prev weeks/date bunch
        dates = self.get_nav_dates(date)
        next = date + tz.timedelta(days=self.nav_days)
        prev = date - tz.timedelta(days=self.nav_days)

        # context dict
        return {
            'nav_dates': {
                'today': today,
                'date': date,
                'next': next,
                'prev': prev,
                'dates': dates,
            }
        }


class TemplateMixinMeta(models.base.ModelBase):
    """
    Metaclass for SectionItem, assigning needed values such as `template`.

    It needs to load the item's template if the section uses the default
    one, and throw error if there is an error in the template.
    """
    def __new__(cls, name, bases, attrs):
        from django.template.loader import get_template
        from django.template import TemplateDoesNotExist

        cl = super().__new__(cls, name, bases, attrs)
        if not hasattr(cl, '_meta'):
            return cl

        if not 'template' in attrs:
            cl.snake_name = camelcase_to_underscore(name)
            cl.template = '{}/sections/{}.html'.format(
                cl._meta.app_label,
                cl.snake_name,
            )
            if name != 'SectionItem':
                try:
                    get_template(cl.template)
                except TemplateDoesNotExist:
                    cl.template = 'aircox_cms/sections/section_item.html'
        return cl


class TemplateMixin(metaclass=TemplateMixinMeta):
    def get_context(self, request, page):
        """
        Default context attributes:
        * self: section being rendered
        * page: current page being rendered
        * request: request used to render the current page

        Other context attributes usable in the default template:
        * content: **safe string** set as content of the section
        * hide: DO NOT render the section, render only an empty string
        """
        return {
            'self': self,
            'page': page,
            'request': request,
        }

    def render(self, request, page, context, *args, **kwargs):
        """
        Render the section. Page is the current publication being rendered.

        Rendering is similar to pages, using 'template' attribute set
        by default to the app_label/sections/model_name_snake_case.html

        If the default template is not found, use SectionItem's one,
        that can have a context attribute 'content' that is used to render
        content.
        """
        context_ = self.get_context(request, *args, page=page, **kwargs)
        if context:
            context_.update(context)

        if context.get('hide'):
            return ''
        return render_to_string(self.template, context_)



#
# Sections
#
@register_snippet
class Section(ClusterableModel):
    """
    Section is a container of multiple items of different types
    that are used to render extra content related or not the current
    page.

    A section has an assigned position in the page, and can be restrained
    to a given type of page.
    """
    name = models.CharField(
        _('name'),
        max_length=32,
        blank = True, null = True,
        help_text=_('name of this section (not displayed)'),
    )
    position = models.CharField(
        _('position'),
        max_length=16,
        blank = True, null = True,
        help_text = _('name of the template block in which the section must '
                      'be set'),
    )
    order = models.IntegerField(
        _('order'),
        default = 100,
        help_text = _('order of rendering, the higher the latest')
    )
    model = models.ForeignKey(
        ContentType,
        verbose_name = _('model'),
        blank = True, null = True,
        help_text=_('this section is displayed only when the current '
                    'page or publication is of this type'),
        limit_choices_to = related_pages_filter,
    )
    page = models.ForeignKey(
        Page,
        verbose_name = _('page'),
        blank = True, null = True,
        help_text=_('this section is displayed only on this page'),
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('position'),
            FieldPanel('model'),
            FieldPanel('page'),
        ], heading=_('General')),
        # InlinePanel('items', label=_('Section Items')),
    ]

    @classmethod
    def get_sections_at (cl, position, page = None):
        """
        Return a queryset of sections that are at the given position.
        Filter out Section that are not for the given page.
        """
        qs = Section.objects.filter(position = position)
        if page:
            qs = qs.filter(
                models.Q(page__isnull = True) |
                models.Q(page = page)
            )
            qs = qs.filter(
                models.Q(model__isnull = True) |
                models.Q(
                    model = ContentType.objects.get_for_model(page).pk
                )
            )
        return qs.order_by('order','pk')

    def add_item(self, item):
        """
        Add an item to the section. Automatically save the item and
        create the corresponding SectionPlace.
        """
        item.section = self
        item.save()

    def render(self, request, page = None, context = None, *args, **kwargs):
        return ''.join([
            item.specific.render(request, page, context, *args, **kwargs)
            for item in self.items.all().order_by('order','pk')
        ])

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.name or self.pk)


@register_snippet
class SectionItem(models.Model,TemplateMixin):
    """
    Base class for a section item.
    """
    section = ParentalKey(Section, related_name='items')
    order = models.IntegerField(
        _('order'),
        default = 100,
        help_text = _('order of rendering, the higher the latest')
    )
    real_type = models.CharField(
        max_length=32,
        blank = True, null = True,
    )
    title = models.CharField(
        _('title'),
        max_length=32,
        blank = True, null = True,
    )
    show_title = models.BooleanField(
        _('show title'),
        default = False,
        help_text=_('if set show a title at the head of the section'),
    )
    css_class = models.CharField(
        _('CSS class'),
        max_length=64,
        blank = True, null = True,
        help_text=_('section container\'s "class" attribute')
    )
    panels = [
        MultiFieldPanel([
            FieldPanel('section'),
            FieldPanel('title'),
            FieldPanel('show_title'),
            FieldPanel('order'),
            FieldPanel('css_class'),
        ], heading=_('General')),
    ]

    @cached_property
    def specific(self):
        """
        Return a downcasted version of the post if it is from another
        model, or itself
        """
        if not self.real_type or type(self) != SectionItem:
            return self
        return getattr(self, self.real_type)

    def save(self, *args, **kwargs):
        if type(self) != SectionItem and not self.real_type:
            self.real_type = type(self).__name__.lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return '{}: {}'.format(
            (self.real_type or 'section item').replace('section','section '),
            self.title or self.pk
        )

class SectionRelativeItem(SectionItem):
    is_related = models.BooleanField(
        _('is related'),
        default = False,
        help_text=_(
            'if set, section is related to the page being processed '
            'e.g rendering a list of links will use thoses of the '
            'publication instead of an assigned one.'
        )
    )

    class Meta:
        abstract=True

    panels = SectionItem.panels.copy()
    panels[-1] = MultiFieldPanel(
        panels[-1].children + [ FieldPanel('is_related') ],
        heading = panels[-1].heading
    )

    def related_attr(self, page, attr):
        """
        Return an attribute from the given page if self.is_related,
        otherwise retrieve the attribute from self.
        """
        return self.is_related and hasattr(page, attr) \
                and getattr(page, attr)

@register_snippet
class SectionText(SectionItem):
    body = RichTextField()
    panels = SectionItem.panels + [
        FieldPanel('body'),
    ]

    def get_context(self, request, page):
        from wagtail.wagtailcore.rich_text import expand_db_html
        context = super().get_context(request, page)
        context['content'] = expand_db_html(self.body)
        return context

@register_snippet
class SectionImage(SectionRelativeItem):
    class ResizeMode(IntEnum):
        max = 0x00
        min = 0x01
        crop = 0x02

    image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('image'),
        related_name='+',
        blank=True, null=True,
        help_text=_(
            'If this item is related to the current page, this image will '
            'be used only when the page has not a cover'
        )
    )
    width = models.SmallIntegerField(
        _('width'),
        blank=True, null=True,
        help_text=_('if set and > 0, sets a maximum width for the image'),
    )
    height = models.SmallIntegerField(
        _('height'),
        blank=True, null=True,
        help_text=_('if set 0 and > 0, sets a maximum height for the image'),
    )
    resize_mode = models.SmallIntegerField(
        verbose_name = _('resize mode'),
        choices = [ (int(y), _(x)) for x,y in ResizeMode.__members__.items() ],
        default = int(ResizeMode.max),
        help_text=_('if the image is resized, set the resizing mode'),
    )

    panels = SectionItem.panels + [
        ImageChooserPanel('image'),
        MultiFieldPanel([
            FieldPanel('width'),
            FieldPanel('height'),
            FieldPanel('resize_mode'),
        ], heading=_('Resizing'))
    ]

    def get_filter(self):
        return \
            'original' if not (self.height or self.width) else \
            'width-{}'.format(self.width) if not self.height else \
            'height-{}'.format(self.height) if not self.width else \
            '{}-{}x{}'.format(
                self.get_resize_mode_display(),
                self.width, self.height
            )

    def get_context(self, request, page):
        from wagtail.wagtailimages.views.serve import generate_signature
        context = super().get_context(request, page)

        image = self.related_attr(page, 'cover') or self.image
        if not image:
            return context

        if self.width or self.height:
            filter_spec = self.get_filter()
            filter_spec = (image.id, filter_spec)
            url = reverse(
                'wagtailimages_serve',
                args=(generate_signature(*filter_spec), *filter_spec)
            )
        else:
            url = image.file.url

        context['content'] = '<img src="{}"/>'.format(url)
        return context


@register_snippet
class SectionLinkList(ClusterableModel, SectionItem):
    panels = SectionItem.panels + [
        InlinePanel('links', label=_('Links')),
    ]


@register_snippet
class SectionLink(RelatedLinkBase,TemplateMixin):
    """
    Render a link to a page or a given url.
    Can either be used standalone or in a SectionLinkList
    """
    template = 'aircox_cms/snippets/link.html'
    parent = ParentalKey(
        'SectionLinkList', related_name = 'links',
        null = True
    )

    def __str__(self):
        return 'link: {} #{}'.format(
            self.text or (self.page and self.page.title) or self.title,
            self.pk
        )


@register_snippet
class SectionList(ListBase, SectionRelativeItem):
    """
    This one is quite badass, but needed: render a list of pages
    using given parameters (cf. ListBase).

    If focus_available, the first article in the list will be the last
    article with a focus, and will be rendered in a bigger size.
    """
    focus_available = models.BooleanField(
        _('focus available'),
        default = False,
        help_text = _('if true, highlight the first focused article found')
    )
    count = models.SmallIntegerField(
        _('count'),
        default = 5,
        help_text = _('number of items to display in the list'),
    )
    url_text = models.CharField(
        _('text of the url'),
        max_length=32,
        blank = True, null = True,
        help_text = _('use this text to display an URL to the complete '
                      'list. If empty, does not print an address'),
    )

    panels = SectionRelativeItem.panels + [
        MultiFieldPanel([
        FieldPanel('focus_available'),
        FieldPanel('count'),
        FieldPanel('url_text'),
        ], heading=_('Rendering')),
    ] + ListBase.panels

    def get_context(self, request, page):
        from aircox_cms.models import Publication
        context = super().get_context(request, page)

        if self.is_related:
            self.related = page

        qs = self.get_queryset()
        qs = qs.live()
        if self.focus_available:
            focus = qs.type(Publication).filter(focus = True).first()
            if focus:
                focus.css_class = 'focus'
                qs = qs.exclude(pk = focus.pk)
        else:
            focus = None

        if not qs.count():
            return { 'hide': True }

        pages = qs[:self.count - (focus != None)]

        context['focus'] = focus
        context['object_list'] = pages
        if self.url_text:
            context['url'] = self.to_url(
                list_page = self.is_related and page
            )
        return context


@register_snippet
class SectionLogsList(SectionItem):
    station = models.ForeignKey(
        aircox.models.Station,
        verbose_name = _('station'),
        null = True,
        on_delete=models.SET_NULL,
        help_text = _('(required) the station on which the logs happened')
    )
    count = models.SmallIntegerField(
        _('count'),
        default = 5,
        help_text = _('number of items to display in the list (max 100)'),
    )

    class Meta:
        verbose_name = _('list of logs')
        verbose_name_plural = _('lists of logs')

    panels = SectionItem.panels + [
        FieldPanel('station'),
        FieldPanel('count'),
    ]

    @staticmethod
    def as_item(log):
        """
        Return a log object as a DiffusionPage or ListItem.
        Supports: Log/Track, Diffusion
        """
        from aircox_cms.models import DiffusionPage
        if type(log) == aircox.models.Diffusion:
            return DiffusionPage.as_item(log)

        related = log.related
        return ListItem(
            title = '{artist} -- {title}'.format(
                artist = related.artist,
                title = related.title,
            ),
            summary = related.info,
            date = log.date,
            info = '♫',
            css_class = 'track'
        )

    def get_context(self, request, page):
        context = super().get_context(request, page)
        context['object_list'] = [
            self.as_item(item)
            for item in self.station.on_air(count = min(self.count, 100))
        ]
        return context


@register_snippet
class SectionTimetable(SectionItem,DatedListBase):
    class Meta:
        verbose_name = _('Section: Timetable')
        verbose_name_plural = _('Sections: Timetable')

    panels = SectionItem.panels + DatedListBase.panels

    def get_queryset(self, context):
        from aircox_cms.models import DiffusionPage
        diffs = []
        for date in context['nav_dates']['dates']:
            items = aircox.models.Diffusion.objects.get_at(date).order_by('start')
            items = [ DiffusionPage.as_item(item) for item in items ]
            diffs.append((date, items))
        return diffs

    def get_context(self, request, page):
        context = super().get_context(request, page)
        context.update(self.get_date_context())
        context['object_list'] = self.get_queryset(context)
        return context


@register_snippet
class SectionPublicationInfo(SectionItem):
    class Meta:
        verbose_name = _('Section: publication\'s info')
        verbose_name_plural = _('Sections: publication\'s info')

@register_snippet
class SectionSearchField(SectionItem):
    default_text = models.CharField(
        _('default text'),
        max_length=32,
        default=_('search'),
        help_text=_('text to display when the search field is empty'),
    )

    class Meta:
        verbose_name = _('Section: search field')
        verbose_name_plural = _('Sections: search field')

    panels = SectionItem.panels + [
        FieldPanel('default_text'),
    ]

    def get_context(self, request, page):
        # FIXME ?????
        from aircox_cms.models import DynamicListPage
        context = super().get_context(request, page)
        return context


@register_snippet
class SectionPlayer(SectionItem):
    live_title = models.CharField(
        _('live title'),
        max_length = 32,
        help_text = _('text to display when it plays live'),
    )
    streams = models.TextField(
        _('audio streams'),
        help_text = _('one audio stream per line'),
    )

    class Meta:
        verbose_name = _('Section: Player')

    panels = SectionItem.panels + [
        FieldPanel('live_title'),
        FieldPanel('streams'),
    ]

    def get_context(self, request, page):
        context = super().get_context(request, page)
        context['streams'] = self.streams.split('\r\n')
        return context



import datetime
import re
from enum import IntEnum

from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.functional import cached_property
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel, FieldRowPanel, \
        MultiFieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel
from wagtail.wagtailsearch import index

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
from aircox_cms.template import TemplateMixin


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
    headline = ''
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


class BaseList(models.Model):
    """
    Generic list
    """
    class DateFilter(IntEnum):
        none = 0x00
        previous = 0x01
        next = 0x02
        before_related = 0x03
        after_related = 0x04

    class RelationFilter(IntEnum):
        none = 0x00
        subpages = 0x01
        siblings = 0x02
        subpages_or_siblings = 0x03

    # rendering
    use_focus = models.BooleanField(
        _('focus available'),
        default = False,
        help_text = _('if true, highlight the first focused article found')
    )
    count = models.SmallIntegerField(
        _('count'),
        default = 30,
        help_text = _('number of items to display in the list'),
    )
    asc = models.BooleanField(
        verbose_name = _('ascending order'),
        default = True,
        help_text = _('if selected sort list in the ascending order by date')
    )

    # selectors
    date_filter = models.SmallIntegerField(
        verbose_name = _('filter on date'),
        choices = [ (int(y), _(x.replace('_', ' ')))
                        for x,y in DateFilter.__members__.items() ],
        blank = True, null = True,
        help_text = _(
            'select pages whose date follows the given constraint'
        )
    )
    model = models.ForeignKey(
        ContentType,
        verbose_name = _('filter on page type'),
        blank = True, null = True,
        on_delete=models.SET_NULL,
        help_text = _('if set, select only elements that are of this type'),
        limit_choices_to = related_pages_filter,
    )
    related = models.ForeignKey(
        Page,
        verbose_name = _('related page'),
        blank = True, null = True,
        on_delete=models.SET_NULL,
        help_text = _(
            'if set, select children or siblings of this page'
        ),
        related_name = '+'
    )
    relation = models.SmallIntegerField(
        verbose_name = _('relation'),
        choices = [ (int(y), _(x.replace('_', ' ')))
                        for x,y in RelationFilter.__members__.items() ],
        default = 1,
        help_text = _(
            'when the list is related to a page, only select pages that '
            'correspond to this relationship'
        ),
    )
    search = models.CharField(
        verbose_name = _('filter on search'),
        blank = True, null = True,
        max_length = 128,
        help_text = _(
            'keep only pages that matches the given search'
        )
    )
    tags = models.CharField(
        verbose_name = _('filter on tag'),
        blank = True, null = True,
        max_length = 128,
        help_text = _(
            'keep only pages with the given tags (separated by a colon)'
        )
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('count'),
            FieldPanel('use_focus'),
            FieldPanel('asc'),
        ], heading=_('rendering')),
        MultiFieldPanel([
            FieldPanel('date_filter'),
            FieldPanel('model'),
            PageChooserPanel('related'),
            FieldPanel('relation'),
            FieldPanel('search'),
            FieldPanel('tags'),
        ], heading=_('filters'))
    ]

    class Meta:
        abstract = True

    def __get_related(self, qs):
        related = self.related and self.related.specific

        filter = self.RelationFilter

        if self.relation in (filter.subpages, filter.subpages_or_siblings):
            qs =  qs.descendant_of(related)
            if not qs.count() and self.relation == filter.subpages_or_siblings:
                qs = qs.sibling_of(related)
        else:
            qs = qs.sibling_of(related)

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
        # FIXME: check if related is published

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

        # date_filter
        date = tz.now()
        if self.date_filter == self.DateFilter.previous:
            qs = qs.filter(date__lt = date)
        elif self.date_filter == self.DateFilter.next:
            qs = qs.filter(date__gte = date)

        # sort
        qs = qs.order_by('date', 'pk') \
                if self.asc else qs.order_by('-date', '-pk')

        # tags
        if self.tags:
            qs = qs.filter(tags__name__in = ','.split(self.tags))

        # search
        if self.search:
            # this qs.search does not return a queryset
            qs = qs.search(self.search)

        return qs

    def get_context(self, request, qs = None, paginate = True):
        """
        Return a context object using the given request and arguments.
        @param paginate: paginate and include paginator into context

        Context arguments:
            - object_list: queryset of the list's objects
            - paginator: [if paginate] paginator object for this list
            - list_url_args: GET arguments of the url as string

        ! Note: BaseList does not inherit from Wagtail.Page, and calling
                this method won't call other super() get_context.
        """
        qs = qs or self.get_queryset()
        paginator = None
        context = {}
        if qs.count():
            if paginate:
                context.update(self.paginate(request, qs))
            else:
                context['object_list'] = qs[:self.count]
        else:
            # keep empty queryset
            context['object_list'] = qs
        context['list_url_args'] = self.to_url(full_url = False)
        context['list_selector'] = self
        return context

    def paginate(self, request, qs):
        # paginator
        paginator = Paginator(qs, self.count)
        try:
            qs = paginator.page(request.GET.get('page') or 1)
        except PageNotAnInteger:
            qs = paginator.page(1)
        except EmptyPage:
            qs = paginator.page(paginator.num_pages)
        return {
            'paginator': paginator,
            'object_list': qs
        }

    def to_url(self, page = None, **kwargs):
        """
        Return a url to a given page with GET corresponding to this
        list's parameters.
        @param page: if given use it to prepend url with page's url instead of giving only
                     GET parameters
        @param **kwargs: override list parameters

        If there is related field use it to get the page, otherwise use
        the given list_page or the first BaseListPage it finds.
        """
        params = {
            'asc': self.asc,
            'date_filter': self.get_date_filter_display(),
            'model': self.model and self.model.model,
            'relation': self.get_relation_display(),
            'search': self.search,
            'tags': self.tags
        }
        params.update(kwargs)

        if self.related:
            params['related'] = self.related.pk

        params = '&'.join([
            key if value == True else '{}={}'.format(key, value)
            for key, value in params.items() if value
        ])
        if not page:
            return params
        return page.url + '?' + params

    @classmethod
    def from_request(cl, request, related = None):
        """
        Return a context from the request's GET parameters. Context
        can be used to update relative informations, more information
        on this object from BaseList.get_context()

        @param request: get params from this request
        @param related: reference page for a related list
        @return context object from BaseList.get_context()

        This function can be used by other views if needed

        Parameters:
        * asc:      if present, sort ascending instead of descending
        * date_filter: one of DateFilter attribute's key.
        * model:    ['program','diffusion','event'] type of the publication
        * relation: one of RelationFilter attribute's key
        * related:  list is related to the method's argument `related`.
                    It can be a page id.

        * tag:      tag to search for
        * search:   query to search in the publications
        * page:     page number
        """
        date_filter = request.GET.get('date_filter')
        model = request.GET.get('model')
        relation = request.GET.get('relation')

        related_= request.GET.get('related')
        if related_:
            try:
                related_ = int(related_)
                related_ = Page.objects.filter(pk = related_).first()
                related_ = related_ and related_.specific
            except:
                related_ = None

        kwargs = {
            'asc': 'asc' in request.GET,
            'date_filter':
                int(getattr(cl.DateFilter, date_filter))
                if date_filter and hasattr(cl.DateFilter, date_filter)
                else None,
            'model':
                ProgramPage if model == 'program' else
                DiffusionPage if model == 'diffusion' else
                EventPage if model == 'event' else None,
            'related': related_,
            'relation':
                int(getattr(cl.RelationFilter, relation))
                if relation and hasattr(cl.RelationFilter, relation)
                else None,
            'tags': request.GET.get('tags'),
            'search': request.GET.get('search'),
        }

        base_list = cl(
            count = 30, **{ k:v for k,v in kwargs.items() if v }
        )
        return base_list.get_context(request)


class DatedBaseList(models.Model):
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
    hide_icons = models.BooleanField(
        _('hide icons'),
        default = False,
        help_text = _('if selected, images of publications will not be '
                      'displayed in the list')
    )

    class Meta:
        abstract = True

    panels = [
        MultiFieldPanel([
            FieldPanel('nav_days'),
            FieldPanel('nav_per_week'),
            FieldPanel('hide_icons'),
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
class SectionItem(TemplateMixin):
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

    cache = ""


    def get_filter(self):
        return \
            'original' if not (self.height or self.width) else \
            'width-{}'.format(self.width) if not self.height else \
            'height-{}'.format(self.height) if not self.width else \
            '{}-{}x{}'.format(
                self.get_resize_mode_display(),
                self.width, self.height
            )

    def ensure_cache(self, image):
        """
        Ensure that we have a generated image and that it is put in cache.
        We use this method since generating dynamic signatures don't generate
        static images (and we need it).
        """
        # Note: in order to put the generated image in db, we first need a way
        #       to get save events from related page or image.
        if self.cache:
            return self.cache

        if self.width or self.height:
            template = Template(
                '{% load wagtailimages_tags %}\n' +
                '{{% image source {filter} as img %}}'.format(
                    filter = self.get_filter()
                ) +
                '<img src="{{ img.url }}">'
            )
            context = Context({
                "source": image
            })
            self.cache = template.render(context)
        else:
            self.cache = '<img src="{}"/>'.format(image.file.url)
        return self.cache

    def get_context(self, request, page):
        from wagtail.wagtailimages.views.serve import generate_signature
        context = super().get_context(request, page)

        image = self.related_attr(page, 'cover') or self.image
        if not image:
            return context

        context['content'] = self.ensure_cache(image)
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
    template_name = 'aircox_cms/snippets/link.html'
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
class SectionList(BaseList, SectionRelativeItem):
    """
    This one is quite badass, but needed: render a list of pages
    using given parameters (cf. BaseList).

    If focus_available, the first article in the list will be the last
    article with a focus, and will be rendered in a bigger size.
    """
    # TODO/FIXME: focus, quid?
    # TODO: logs in menu show headline???
    url_text = models.CharField(
        _('text of the url'),
        max_length=32,
        blank = True, null = True,
        help_text = _('use this text to display an URL to the complete '
                      'list. If empty, no link is displayed'),
    )

    panels = SectionRelativeItem.panels + [
        FieldPanel('url_text'),
    ] + BaseList.panels

    def get_context(self, request, page):
        import aircox_cms.models as cms
        if self.is_related and not self.related:
            # set current page if there is not yet a related page only
            self.related = page

        context = BaseList.get_context(self, request, paginate = False)
        if not context['object_list'].count():
            return { 'hide': True }

        context.update(SectionRelativeItem.get_context(self, request, page))
        if self.url_text:
            self.related = self.related.specific
            target = None
            if self.related and hasattr(self.related, 'get_list_page'):
                target = self.related.get_list_page()

            if not target:
                settings = cms.WebsiteSettings.for_site(request.site)
                target = settings.list_page
            context['url'] = self.to_url(page = target) + '&view=list'
        return context

SectionList._meta.get_field('count').default = 5


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
        if log.diffusion:
            return DiffusionPage.as_item(log.diffusion)

        track = log.track
        return ListItem(
            title = '{artist} -- {title}'.format(
                artist = track.artist,
                title = track.title,
            ),
            headline = track.info,
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
class SectionTimetable(SectionItem,DatedBaseList):
    class Meta:
        verbose_name = _('Section: Timetable')
        verbose_name_plural = _('Sections: Timetable')

    station = models.ForeignKey(
        aircox.models.Station,
        verbose_name = _('station'),
        help_text = _('(required) related station')
    )
    target = models.ForeignKey(
        'aircox_cms.TimetablePage',
        verbose_name = _('timetable page'),
        blank = True, null = True,
        help_text = _('select a timetable page used to show complete timetable'),
    )
    nav_visible = models.BooleanField(
        _('show date navigation'),
        default = True,
        help_text = _('if checked, navigation dates will be shown')
    )

    # TODO: put in multi-field panel of DatedBaseList
    panels = SectionItem.panels + DatedBaseList.panels + [
        MultiFieldPanel([
            FieldPanel('nav_visible'),
            FieldPanel('station'),
            FieldPanel('target'),
        ], heading=_('Timetable')),
    ]

    def get_queryset(self, context):
        from aircox_cms.models import DiffusionPage
        diffs = []
        for date in context['nav_dates']['dates']:
            items = aircox.models.Diffusion.objects.at(self.station, date)
            items = [ DiffusionPage.as_item(item) for item in items ]
            diffs.append((date, items))
        return diffs

    def get_context(self, request, page):
        context = super().get_context(request, page)
        context.update(self.get_date_context())
        context['object_list'] = self.get_queryset(context)
        context['target'] = self.target
        if not self.nav_visible:
            del context['nav_dates']['dates'];
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



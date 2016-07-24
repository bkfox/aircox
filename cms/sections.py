import datetime
import re
from enum import Enum, IntEnum


from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
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


def related_pages_filter():
    """
    Return a dict that can be used to filter foreignkey to pages'
    subtype declared in aircox.cms.models.

    Note: the filter is calculated at the first call of the function.
    """
    if hasattr(related_pages_filter, 'filter'):
        return related_pages_filter.filter

    import aircox.cms.models as cms
    import inspect
    related_pages_filter.filter = {
        'model__in': (name.lower() for name, member in
            inspect.getmembers(cms,
                lambda x: inspect.isclass(x) and issubclass(x, Page)
            )
            if member != Page
        ),
    }
    return related_pages_filter.filter


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
        help_text = _('icon to display before the url'),
    )
    text = models.CharField(
        _('text'),
        max_length = 64,
        null = True, blank=True,
        help_text = _('text to display of the link'),
    )

    class Meta:
        abstract = True

    panels = [
        MultiFieldPanel([
            FieldPanel('text'),
            ImageChooserPanel('icon'),
            FieldPanel('url'),
            PageChooserPanel('page'),
        ], heading=_('link'))
    ]


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

    filter_date = models.SmallIntegerField(
        verbose_name = _('filter by date'),
        choices = [ (int(y), _(x.replace('_', ' ')))
                        for x,y in DateFilter.__members__.items() ],
        blank = True, null = True,
    )
    filter_model = models.ForeignKey(
        ContentType,
        verbose_name = _('filter by type'),
        blank = True, null = True,
        help_text = _('if set, select only elements that are of this type'),
        limit_choices_to = related_pages_filter,
    )
    filter_related = models.ForeignKey(
        'Publication',
        verbose_name = _('filter by a related publication'),
        blank = True, null = True,
        help_text = _('if set, select children or siblings of this publication'),
    )
    related_sibling = models.BooleanField(
        verbose_name = _('related is a sibling'),
        default = False,
        help_text = _('if selected select related publications that are '
                      'siblings of this one'),
    )
    sort_asc = models.BooleanField(
        verbose_name = _('order ascending'),
        default = True,
        help_text = _('if selected sort list in the ascending order by date')
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('filter_model'),
            FieldPanel('filter_related'),
            FieldPanel('related_sibling'),
        ], heading=_('filters')),
        MultiFieldPanel([
            FieldPanel('filter_date'),
            FieldPanel('sort_asc'),
        ], heading=_('sorting'))
    ]

    class Meta:
        abstract = True

    @classmethod
    def get_base_queryset(cl, filter_date = None, filter_model = None,
                            filter_related = None, related_siblings = None,
                            sort_asc = True):
        """
        Get queryset based on the arguments. This class is intended to be
        reusable by other classes if needed.
        """
        # model
        if filter_model:
            qs = filter_model.objects.all()
        else:
            qs = Publication.objects.all()
        qs = qs.live().not_in_section()

        # related
        if filter_related:
            if related_siblings:
                qs = qs.sibling_of(filter_related)
            else:
                qs = qs.descendant_of(filter_related)

            date = filter_related.date
            if filter_date == cl.DateFilter.before_related:
                qs = qs.filter(date__lt = date)
            elif filter_date == cl.DateFilter.after_related:
                qs = qs.filter(date__gte = date)
        # date
        else:
            date = tz.now()
            if filter_date == cl.DateFilter.previous:
                qs = qs.filter(date__lt = date)
            elif filter_date == cl.DateFilter.next:
                qs = qs.filter(date__gte = date)

        # sort
        if sort_asc:
            return qs.order_by('date', 'pk')
        return qs.order_by('-date', '-pk')

    @classmethod
    def get_queryset_from_request(cl, request, *args,
                                  related = None, context = {},
                                  **kwargs):
        """
        Return a queryset from the request's GET parameters. Context
        can be used to update relative informations.

        This function can be used by other views if needed

        Parameters:
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
        model = request.GET.get('model')

        kwargs = {
            'filter_model': ProgramPage if model == 'program' else \
                            DiffusionPage if model == 'diffusion' else \
                            EventPage if model == 'event' else None,
            'filter_related': 'related' in request.GET and related,
            'related_siblings': 'siblings' in request.GET,
            'sort_asc': 'asc' in request.GET,
        }
        qs = cl.get_base_queryset(**kwargs)

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

        context['list_selector'] = kwargs

        # paginator
        if qs:
            paginator = Paginator(qs, 30)
            try:
                qs = paginator.page('page')
            except PageNotAnInteger:
                qs = paginator.page(1)
            except EmptyPage:
                qs = parginator.page(paginator.num_pages)
            context['paginator'] = paginator
        context['object_list'] = qs
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

    def get_date_context(self, date):
        """
        Return a dict that can be added to the context to be used by
        a date_list.
        """
        today = tz.now().today()
        if not date:
            date = today

        # next/prev weeks/date bunch
        dates = self.get_nav_dates(date)
        next = date + tz.timedelta(days=self.nav_days)
        prev = date - tz.timedelta(days=self.nav_days)

        # context dict
        return {
            'nav_dates': {
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
    model = models.ForeignKey(
        ContentType,
        verbose_name = _('model'),
        blank = True, null = True,
        help_text=_('this section is displayed only when the current '
                    'page or publication is of this type'),
        limit_choices_to = related_pages_filter,
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('position'),
            FieldPanel('model'),
        ], heading=_('General')),
        InlinePanel('places', label=_('Section Items')),
    ]

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.name or self.pk)

    def render(self, request, page = None, *args, **kwargs):
        return ''.join([
            place.item.render(request, page, *args, **kwargs)
            for place in self.places
        ])


class SectionPlace(Orderable):
    section = ParentalKey(Section, related_name='places')
    item = models.ForeignKey(
        'SectionItem',
        verbose_name=_('item')
    )

    panels = [
        SnippetChooserPanel('item'),
        FieldPanel('model'),
    ]

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.title or self.pk)


class SectionItemMeta(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        cl = super().__new__(name, bases, attrs)
        if not 'template' in attrs:
            attrs['template'] = 'cms/sections/{}.html' \
                .format(camelcase_to_underscore(name))
        return cl


@register_snippet
class SectionItem(models.Model):
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
    related = models.BooleanField(
        _('related'),
        default = False,
        help_text=_('if set, section is related to the current publication. '
                    'e.g rendering a list related to it instead of to all '
                    'publications'),
    )
    css_class = models.CharField(
        _('CSS class'),
        max_length=64,
        blank = True, null = True,
        help_text=_('section container\'s "class" attribute')
    )
    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('show_title'),
            FieldPanel('css_class'),
        ], heading=_('General')),
    ]

    def model_name(self):
        return self.__class__.__name__.lower()

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

    def get_context(self, request, page, *args, **kwargs):
        return {
            'self': self,
            'page': page,
        }

    def render(self, request, page, *args, **kwargs):
        """
        Render the section. Page is the current publication being rendered.
        """
        return render_to_string(
            request, self.template,
            self.get_context(request, *args, page=page, **kwargs)
        )

    def __str__(self):
        return '{}: {}'.format(
            (self.real_type or 'section item').replace('section','section '),
            self.title or self.pk
        )


@register_snippet
class SectionText(SectionItem):
    body = RichTextField()
    panels = SectionItem.panels + [
        FieldPanel('body'),
    ]


@register_snippet
class SectionImage(SectionItem):
    image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('image'),
        related_name='+',
    )
    panels = SectionItem.panels + [
        ImageChooserPanel('image'),
    ]


@register_snippet
class SectionLink(RelatedLinkBase,SectionItem):
    """
    Can either be used standalone or in a SectionLinkList
    """
    parent = ParentalKey('SectionLinkList', related_name='links',
                         blank=True, null=True)
    panels = SectionItem.panels + RelatedLinkBase.panels


@register_snippet
class SectionLinkList(SectionItem,ClusterableModel):
    panels = SectionItem.panels + [
        InlinePanel('links', label=_('links'))
    ]


@register_snippet
class SectionPublicationList(ListBase,SectionItem):
    focus_available = models.BooleanField(
        _('focus available'),
        default = False,
        help_text = _('if true, highlight the first focused article found')
    )
    panels = SectionItem.panels + [ FieldPanel('focus_available') ] +\
             ListBase.panels




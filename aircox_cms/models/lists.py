"""
Generic list manipulation used to render list of items

Includes various usefull class and abstract models to make lists and
list items.
"""
import datetime
import re
from enum import IntEnum

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.utils.functional import cached_property

from wagtail.wagtailadmin.edit_handlers import *
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailimages.models import Image
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from aircox_cms.utils import related_pages_filter


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


class RelatedLinkBase(Orderable):
    """
    Base model to make a link item. It can link to an url, or a page and
    includes some common fields.
    """
    url = models.URLField(
        _('url'),
        null=True, blank=True,
        help_text = _('URL of the link'),
    )
    page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('Use a page instead of a URL')
    )
    icon = models.ForeignKey(
        Image,
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
        help_text = _('filter pages on their date')
    )
    model = models.ForeignKey(
        ContentType,
        verbose_name = _('filter on page type'),
        blank = True, null = True,
        on_delete=models.SET_NULL,
        help_text = _('keep only elements of this type'),
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
            qs_ = qs.descendant_of(related)
            if self.relation == filter.subpages_or_siblings and \
                    not qs.count():
                qs_ = qs.sibling_of(related)
            qs = qs_
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
            'relation': self.relation,
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
        if relation is not None:
            try:
                relation = int(relation)
            except:
                relation = None

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
            'relation': relation,
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




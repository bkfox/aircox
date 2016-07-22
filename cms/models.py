import datetime
import re
from enum import Enum, IntEnum

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

# pages and panels
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailcore.models import Page, Orderable, \
        PageManager, PageQuerySet
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel, FieldRowPanel, \
        MultiFieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel

# snippets
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
from wagtail.wagtailsnippets.models import register_snippet

# tags
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

# comment clean-up
import bleach

import aircox.programs.models as programs
import aircox.controllers.models as controllers
import aircox.cms.settings as settings


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


@register_setting
class WebsiteSettings(BaseSetting):
    logo = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('logo'),
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('logo of the website'),
    )
    favicon = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('favicon'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('favicon for the website'),
    )
    accept_comments = models.BooleanField(
        default = True,
        help_text = _('publish comments automatically without verifying'),
    )
    allow_comments = models.BooleanField(
        default = True,
        help_text = _('publish comments automatically without verifying'),
    )
    comment_success_message = models.TextField(
        _('success message'),
        default = _('Your comment has been successfully posted!'),
        help_text = _('message to display when a post has been posted'),
    )
    comment_wait_message = models.TextField(
        _('waiting message'),
        default = _('Your comment is awaiting for approval.'),
        help_text = _('message to display when a post waits to be reviewed'),
    )
    comment_error_message = models.TextField(
        _('error message'),
        default = _('We could not save your message. Please correct the error(s) below.'),
        help_text = _('message to display there is an error an incomplete form.'),
    )

    panels = [
        ImageChooserPanel('logo'),
        ImageChooserPanel('favicon'),
        MultiFieldPanel([
            FieldPanel('allow_comments'),
            FieldPanel('accept_comments'),
            FieldPanel('comment_success_message'),
            FieldPanel('comment_wait_message'),
            FieldPanel('comment_error_message'),
        ], heading = _('Comments'))
    ]

    class Meta:
        verbose_name = _('website settings')


#
#   Base
#
class BaseRelatedLink(Orderable):
    url = models.URLField(
        _('url'),
        help_text = _('URL of the link'),
    )
    icon = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('icon'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('icon to display before the url'),
    )
    title = models.CharField(
        _('title'),
        max_length = 64,
        null = True, blank=True,
        help_text = _('text to display of the link'),
    )

    class Meta:
        abstract = True

    panels = [
        FieldPanel('url'),
        FieldRowPanel([
            FieldPanel('title'),
            ImageChooserPanel('icon'),
        ]),
    ]


#
# Publications
#
@register_snippet
class Comment(models.Model):
    publication = models.ForeignKey(
        'Publication',
    )
    published = models.BooleanField(
        verbose_name = _('public'),
        default = False
    )
    author = models.CharField(
        verbose_name = _('author'),
        max_length = 32,
    )
    email = models.EmailField(
        verbose_name = _('email'),
        blank = True, null = True,
    )
    url = models.URLField(
        verbose_name = _('website'),
        blank = True, null = True,
    )
    date = models.DateTimeField(
        _('date'),
        auto_now_add = True,
    )
    content = models.TextField (
        _('comment'),
    )

    def make_safe(self):
        self.author = bleach.clean(self.author, tags=[])
        if self.email:
            self.email = bleach.clean(self.email, tags=[])
            self.email = self.email.replace('"', '%22')
        if self.url:
            self.url = bleach.clean(self.url, tags=[])
            self.url = self.url.replace('"', '%22')
        self.content = bleach.clean(
            self.content,
            tags=settings.AIRCOX_CMS_BLEACH_COMMENT_TAGS,
            attributes=settings.AIRCOX_CMS_BLEACH_COMMENT_ATTRS
        )

    def save(self, make_safe = True, *args, **kwargs):
        if make_safe:
            self.make_safe()
        return super().save(*args, **kwargs)


class RelatedLink(BaseRelatedLink):
    parent = ParentalKey('Publication', related_name='related_links')

class PublicationTag(TaggedItemBase):
    content_object = ParentalKey('Publication', related_name='tagged_items')


class Publication(Page):
    order_field = 'first_published_at'

    publish_as = models.ForeignKey(
        'ProgramPage',
        verbose_name = _('publish as program'),
        on_delete=models.SET_NULL,
        blank = True, null = True,
        help_text = _('use this program as the author of the publication'),
    )
    focus = models.BooleanField(
        _('focus'),
        default = False,
        help_text = _('the publication is highlighted;'),
    )
    allow_comments = models.BooleanField(
        _('allow comments'),
        default = True,
        help_text = _('allow comments')
    )

    body = RichTextField(blank=True)
    cover = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('cover'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('image to use as cover of the publication'),
    )
    summary = models.TextField(
        _('summary'),
        blank = True, null = True,
        help_text = _('summary of the publication'),
    )
    tags = ClusterTaggableManager(
        verbose_name = _('tags'),
        through=PublicationTag,
        blank=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full")
    ]
    promote_panels = [
        MultiFieldPanel([
            ImageChooserPanel('cover'),
            FieldPanel('summary'),
            FieldPanel('tags'),
            FieldPanel('focus'),
        ]),
        InlinePanel('related_links', label=_('Links'))
    ] + Page.promote_panels
    settings_panels = Page.settings_panels + [
        FieldPanel('publish_as'),
        FieldPanel('allow_comments'),
    ]

    @property
    def date(self):
        return self.first_published_at

    @property
    def recents(self):
        return self.get_children().not_in_menu() \
                   .order_by('-first_published_at')

    @property
    def comments(self):
        return Comment.objects.filter(
            publication = self,
            published = True,
        ).order_by('-date')

    def get_context(self, request, *args, **kwargs):
        from aircox.cms.forms import CommentForm
        context = super().get_context(request, *args, **kwargs)
        view = request.GET.get('view')
        page = request.GET.get('page')

        if self.allow_comments and \
                WebsiteSettings.for_site(request.site).allow_comments:
            context['comment_form'] = CommentForm()

        if view == 'list':
            context['object_list'] = ListPage.get_queryset(
                request, *args, context = context, thread = self, **kwargs
            )
        return context

    def serve(self, request):
        from aircox.cms.forms import CommentForm
        if request.POST and 'comment' in request.POST['type']:
            settings = WebsiteSettings.for_site(request.site)
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.publication = self
                comment.published = settings.accept_comments
                comment.save()
                messages.success(request,
                    settings.comment_success_message
                        if comment.published else
                    settings.comment_wait_message,
                    fail_silently=True,
                )
            else:
                messages.error(
                    request, settings.comment_error_message, fail_silently=True
                )

        return super().serve(request)


class ProgramPage(Publication):
    program = models.ForeignKey(
        programs.Program,
        verbose_name = _('program'),
        related_name = 'page',
        on_delete=models.SET_NULL,
        blank=True, null=True,
    )
    # rss = models.URLField()
    email = models.EmailField(
        _('email'), blank=True, null=True,
    )
    email_is_public = models.BooleanField(
        _('email is public'),
        default = False,
        help_text = _('the email addess is accessible to the public'),
    )

    class Meta:
        verbose_name = _('Program')
        verbose_name_plural = _('Programs')

    content_panels = [
        FieldPanel('program'),
    ] + Publication.content_panels

    settings_panels = Publication.settings_panels + [
        FieldPanel('email'),
        FieldPanel('email_is_public'),
    ]

    def diffs_to_page(self, diffs):
        for diff in diffs:
            if diff.page.count():
                diff.page_ = diff.page.first()
            else:
                diff.page_ = ListItem(
                    title = '{}, {}'.format(
                        self.program.name, diff.date.strftime('%d %B %Y')
                    ),
                    cover = self.cover,
                    live = True,
                    date = diff.start,
                )
        return [
            diff.page_ for diff in diffs if diff.page_.live
        ]

    @property
    def next(self):
        now = tz.now()
        diffs = programs.Diffusion.objects \
                    .filter(end__gte = now, program = self.program) \
                    .order_by('start').prefetch_related('page')
        return self.diffs_to_page(diffs)

    @property
    def prev(self):
        now = tz.now()
        diffs = programs.Diffusion.objects \
                    .filter(end__lte = now, program = self.program) \
                    .order_by('-start').prefetch_related('page')
        return self.diffs_to_page(diffs)


class Track(programs.Track,Orderable):
    sort_order_field = 'position'

    diffusion = ParentalKey('DiffusionPage',
                            related_name='tracks')
    panels = [
        FieldRowPanel([
            FieldPanel('artist'),
            FieldPanel('title'),
        ]),
        FieldPanel('tags'),
        FieldPanel('info'),
    ]

    def save(self, *args, **kwargs):
        if self.diffusion.diffusion:
            self.related = self.diffusion.diffusion
        self.in_seconds = False
        super().save(*args, **kwargs)


class DiffusionPage(Publication):
    order_field = 'diffusion__start'

    diffusion = models.ForeignKey(
        programs.Diffusion,
        verbose_name = _('diffusion'),
        related_name = 'page',
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to = lambda: {
            'initial__isnull': True,
            'start__gt': tz.now() - tz.timedelta(days=10),
            'start__lt': tz.now() + tz.timedelta(days=10),
        }
    )

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')

    content_panels = [
        FieldPanel('diffusion'),
    ] + Publication.content_panels + [
        InlinePanel('tracks', label=_('Tracks'))
    ]

    @classmethod
    def as_item(cl, diff):
        """
        Return a DiffusionPage or ListItem from a Diffusion
        """
        if diff.page.all().count():
            item = diff.page.live().first()
        else:
            item = ListItem(
                title = '{}, {}'.format(
                    diff.program.name, diff.date.strftime('%d %B %Y')
                ),
                cover = (diff.program.page.count() and \
                            diff.program.page.first().cover) or '',
                live = True,
                date = diff.start,
            )

        if diff.initial:
            item.info = _('Rerun of %(date)s') % {
                'date': diff.initial.start.strftime('%A %d')
            }
        diff.css_class = 'diffusion'

        return item

    def save(self, *args, **kwargs):
        if self.diffusion:
            self.first_published_at = self.diffusion.start
        super().save(*args, **kwargs)

class EventPageQuerySet(PageQuerySet):
    def upcoming(self):
        now = tz.now().date()
        return self.filter(start_date__gte=now)


class EventPage(Publication):
    order_field = 'start'

    start = models.DateTimeField(
        _('start'),
        help_text = _('when it happens'),
    )
    end = models.DateTimeField(
        _('end'),
        blank = True, null = True,
    )
    place = models.TextField(
        _('place'),
        help_text = _('address where the event takes place'),
    )
    price = models.CharField(
        _('price'),
        max_length=64,
        blank = True, null = True,
        help_text = _('price of the event'),
    )
    info = models.TextField(
        _('info'),
        blank = True, null = True,
        help_text = _('additional information'),
    )

    objects = PageManager.from_queryset(EventPageQuerySet)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    content_panels = Publication.content_panels + [
        FieldRowPanel([
            FieldPanel('start'),
            FieldPanel('end'),
        ]),
        FieldPanel('place'),
    ]

    def save(self, *args, **kwargs):
        self.first_published_at = self.start
        super().save(*args, **kwargs)


#
# Lists
#
class BaseDateList(models.Model):
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

    def get_date_context(self, date, date_max = None):
        """
        Return a dict that can be added to the context to be used by
        a date_list.
        """
        if not date:
            date = tz.now().today()

        if date_max:
            date = min(date, date_max)

        # dates
        if date_max == date:
            first = self.nav_days - 1
        elif self.nav_per_week:
            first = date.weekday()
        else:
            first = int((self.nav_days - 1) / 2)
        first = date - tz.timedelta(days = first)
        dates = [ first + tz.timedelta(days=i)
                    for i in range(0, self.nav_days) ]

        # next/prev weeks/date bunch
        next = date + tz.timedelta(days=self.nav_days)
        prev = date - tz.timedelta(days=self.nav_days)

        if date_max:
            dates = [ date for date in dates if date <= date_max ]
            next = min(next, date_max)
            if next in dates:
                next = None
            prev = min(prev, date_max)

        # context dict
        return {
            'nav_dates': {
                'date': date,
                'next': next,
                'prev': prev,
                'dates': dates,
            }
        }


class ListPage(Page):
    """
    Page for simple lists, query is done though request' GET fields.
    Look at get_queryset for more information.
    """
    summary = models.TextField(
        _('summary'),
        blank = True, null = True,
        help_text = _('some short description if you want to, just for fun'),
    )

    @classmethod
    def get_queryset(cl, request, *args,
                     thread = None, context = {},
                     **kwargs):
        """
        Return a queryset from the request's GET parameters. Context
        can be used to update relative informations.

        This function can be used by other views if needed

        Parameters:
        * type:     ['program','diffusion','event'] type of the publication
        * tag:      tag to search for
        * search:   query to search in the publications
        * thread:   children of the thread passed in arguments only
        * order:    ['asc','desc'] sort ordering
        * page:     page number

        Context's fields:
        * object_list:      the final queryset
        * list_type:        type of the items in the list (as Page subclass)
        * tag_query:        tag searched for
        * search_query:     search terms
        * thread_query:     thread
        * paginator:        paginator object
        """
        if 'thread' in request.GET and thread:
            qs = thread.get_children().not_in_menu()
            context['thread_query'] = thread
        else:
            qs = Publication.objects.all()
        qs = qs.live()

        # ordering
        order = request.GET.get('order')
        if order not in ('asc','desc'):
            order = 'desc'
        qs = qs.order_by(
            ('-' if order == 'desc' else '') + 'first_published_at'
        )

        # type
        type = request.GET.get('type')
        if type == 'program':
            qs = qs.type(ProgramPage)
            context['list_type'] = ProgramPage
        elif type == 'diffusion':
            qs = qs.type(DiffusionPage)
            context['list_type'] = DiffusionPage
        elif type == 'event':
            qs = qs.type(EventPage)
            context['list_type'] = EventPage

        # filter by tag
        tag = request.GET.get('tag')
        if tag:
            context['tag_query'] = tag
            qs = qs.filter(tags__name = tag)

        # search
        search = request.GET.get('search')
        if search:
            context['search_query'] = search
            qs = qs.search(search)

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

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        qs = self.get_queryset(request, context=context)
        context['object_list'] = qs
        return context


class LogsPage(BaseDateList,Page):
    summary = models.TextField(
        _('summary'),
        blank = True, null = True,
        help_text = _('some short description if you want to, just for fun'),
    )
    station = models.ForeignKey(
        controllers.Station,
        verbose_name = _('station'),
        null = True,
        on_delete=models.SET_NULL,
        help_text = _('(required for logs) the station on which the logs '
                      'happened')
    )
    max_days = models.IntegerField(
        _('maximum days'),
        default=15,
        help_text = _('maximum days in the past allowed to be shown. '
                      '0 means no limit')
    )

    class Meta:
        verbose_name = _('Logs Page')

    content_panels = [
        FieldPanel('title'),
        MultiFieldPanel([
            FieldPanel('station'),
            FieldPanel('max_days'),
        ], heading=_('Configuration')),
    ] + BaseDateList.panels

    def as_item(cl, log):
        """
        Return a log object as a DiffusionPage or ListItem.
        Supports: Log/Track, Diffusion
        """
        if type(log) == programs.Diffusion:
            return DiffusionPage.as_item(log)
        return ListItem(
            title = '{artist} -- {title}'.format(
                artist = log.related.artist,
                title = log.related.title,
            ),
            summary = log.related.info,
            date = log.date,
            info = '♫',
            css_class = 'track'
        )

    def get_queryset(self, request, context):
        logs = []
        for date in context['nav_dates']['dates']:
            items = self.station.get_on_air(date)
            items = [ self.as_item(item) for item in items ]
            logs.append((date, items))
        return logs

    def get_context(self, request, *args, **kwargs):
        """
        note: context is updated using self.get_date_context
        """
        context = super().get_context(request, *args, **kwargs)

        # date navigation
        if 'date' in request.GET:
            date = request.GET.get('date')
            date = self.str_to_date(date)

            if date and self.max_days:
                date = max(
                    tz.now().date() - tz.timedelta(days=self.max_days),
                    date
                )
        else:
            date = tz.now().date()
        context.update(self.get_date_context(date, date_max=tz.now().date()))

        # queryset
        context['object_list'] = self.get_queryset(request, context)
        return context


class TimetablePage(BaseDateList,Page):
    class Meta:
        verbose_name = _('Timetable')

    content_panels = Page.content_panels + BaseDateList.panels

    def get_queryset(self, request, context):
        diffs = []
        for date in context['nav_dates']['dates']:
            items = programs.Diffusion.objects.get_at(date).order_by('start')
            items = [ DiffusionPage.as_item(item) for item in items ]
            diffs.append((date, items))
        return diffs

    def get_context(self, request, *args, **kwargs):
        """
        note: context is updated using self.get_date_context
        """
        context = super().get_context(request, *args, **kwargs)

        # date navigation
        if 'date' in request.GET:
            date = request.GET.get('date')
            date = self.str_to_date(date)
        else:
            date = tz.now().date()
        context.update(self.get_date_context(date))

        # queryset
        context['object_list'] = self.get_queryset(request, context)
        return context

#
# Menus and Sections
#

@register_snippet
class Menu(ClusterableModel):
    name = models.CharField(
        _('name'),
        max_length=32,
        blank = True, null = True,
        help_text=_('name of this menu (not displayed)'),
    )
    css_class = models.CharField(
        _('CSS class'),
        max_length=64,
        blank = True, null = True,
        help_text=_('menu container\'s "class" attribute')
    )
    related = models.ForeignKey(
        ContentType,
        blank = True, null = True,
        help_text=_('this menu is displayed only for this model')
    )
    position = models.CharField(
        _('position'),
        max_length=16,
        blank = True, null = True,
        help_text = _('name of the template block in which the menu must '
                      'be set'),
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('css_class'),
        ], heading=_('General')),
        MultiFieldPanel([
            FieldPanel('related'),
            FieldPanel('position'),
        ], heading=_('Position')),
        InlinePanel('menu_items', label=_('menu items')),
    ]


@register_snippet
class MenuItem(models.Model):
    real_type = models.CharField(
        max_length=32,
        blank = True, null = True,
    )
    title = models.CharField(
        _('title'),
        max_length=32,
        blank = True, null = True,
    )
    css_class = models.CharField(
        _('CSS class'),
        max_length=64,
        blank = True, null = True,
        help_text=_('menu container\'s "class" attribute')
    )
    menu = ParentalKey(Menu, related_name='menu_items')

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('css_class'),
        ], heading=_('General')),
    ]

    def specific(self):
        """
        Return a downcasted version of the post if it is from another
        model, or itself
        """
        if not self.real_type or type(self) != Post:
            return self
        return getattr(self, self.real_type)

    def save(self, make_safe = True, *args, **kwargs):
        if type(self) != MenuItem and not self.real_type:
            self.real_type = type(self).__name__.lower()
        return super().save(*args, **kwargs)




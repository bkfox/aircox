import datetime

from django.db import models
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
from wagtail.wagtailsearch import index

# snippets
from wagtail.wagtailsnippets.models import register_snippet

# tags
from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

# comment clean-up
import bleach

import aircox.programs.models as programs
import aircox.controllers.models as controllers
import aircox.cms.settings as settings

from aircox.cms.sections import *


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


class RelatedLink(RelatedLinkBase):
    parent = ParentalKey('Publication', related_name='related_links')

class PublicationTag(TaggedItemBase):
    content_object = ParentalKey('Publication', related_name='tagged_items')


class Publication(Page):
    order_field = 'date'

    date = models.DateTimeField(
        _('date'),
        blank = True, null = True,
        auto_now_add = True,
    )
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

    class Meta:
        verbose_name = _('Publication')
        verbose_name_plural = _('Publication')

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full")
    ]
    promote_panels = [
        MultiFieldPanel([
            ImageChooserPanel('cover'),
            FieldPanel('summary'),
            FieldPanel('tags'),
            FieldPanel('focus'),
        ], heading=_('Content')),
        InlinePanel('related_links', label=_('Links'))
    ] + Page.promote_panels
    settings_panels = Page.settings_panels + [
        FieldPanel('publish_as'),
        FieldPanel('allow_comments'),
    ]
    search_fields = [
        index.SearchField('body'),
        index.FilterField('live'),
        index.FilterField('show_in_menus'),
    ]

    @property
    def recents(self):
        return self.get_children().type(Publication).not_in_menu().live() \
                   .order_by('-publication__date')

    @property
    def comments(self):
        return Comment.objects.filter(
            publication = self,
            published = True,
        ).order_by('-date')

    def save(self, *args, **kwargs):
        if not self.date and self.first_published_at:
            self.date = self.first_published_at
        super().save(*args, **kwargs)

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
                request, context = context, related = self
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
            item = diff.page.all().first()
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
            self.date = self.diffusion.start
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
        self.date = self.start
        super().save(*args, **kwargs)


#
# Lists
#
class ListPage(Page):
    """
    Page for simple lists, query is done though request' GET fields.
    Look at get_queryset for more information.
    """
    body = RichTextField(
        _('body'),
        blank = True, null = True,
        help_text = _('add an extra description for this list')
    )

    class Meta:
        verbose_name = _('List')
        verbose_name_plural = _('List')

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        qs = ListBase.from_request(request, context=context)
        context['object_list'] = qs
        return context


class DatedListPage(DatedListBase,Page):
    body = RichTextField(
        _('body'),
        blank = True, null = True,
        help_text = _('add an extra description for this list')
    )

    class Meta:
        abstract = True

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('body'),
        ], heading=_('Content')),
    ] + DatedListBase.panels

    def get_queryset(self, request, context):
        """
        Must be implemented by the child
        """
        return []

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


class LogsPage(DatedListPage):
    template = 'cms/dated_list_page.html'

    station = models.ForeignKey(
        controllers.Station,
        verbose_name = _('station'),
        null = True,
        on_delete=models.SET_NULL,
        help_text = _('(required for logs) the station on which the logs '
                      'happened')
    )
    age_max = models.IntegerField(
        _('maximum age'),
        default=15,
        help_text = _('maximum days in the past allowed to be shown. '
                      '0 means no limit')
    )

    class Meta:
        verbose_name = _('Logs')
        verbose_name_plural = _('Logs')

    content_panels = DatedListBase.panels + [
        MultiFieldPanel([
            FieldPanel('station'),
            FieldPanel('age_max'),
        ], heading=_('Configuration')),
    ]

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

    def get_nav_dates(self, date):
        """
        Return a list of dates availables for the navigation
        """
        # there might be a bug if age_max < nav_days
        today = tz.now().date()
        first = min(date, today)
        first = max( first - tz.timedelta(days = self.nav_days-1),
                     today - tz.timedelta(days = self.age_max))
        return [ first + tz.timedelta(days=i)
                    for i in range(0, self.nav_days) ]

    def get_queryset(self, request, context):
        today = tz.now().date()
        if context['nav_dates']['next'] > today:
            context['nav_dates']['next'] = None
        if context['nav_dates']['prev'] < \
                today - tz.timedelta(days = self.age_max):
            context['nav_dates']['prev'] = None

        logs = []
        for date in context['nav_dates']['dates']:
            items = self.station.get_on_air(date)
            items = [ self.as_item(item) for item in items ]
            logs.append((date, items))
        return logs


class TimetablePage(DatedListPage):
    template = 'cms/dated_list_page.html'

    class Meta:
        verbose_name = _('Timetable')
        verbose_name_plural = _('Timetable')

    def get_queryset(self, request, context):
        diffs = []
        for date in context['nav_dates']['dates']:
            items = programs.Diffusion.objects.get_at(date).order_by('start')
            items = [ DiffusionPage.as_item(item) for item in items ]
            diffs.append((date, items))
        return diffs






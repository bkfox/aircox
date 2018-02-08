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

import aircox.models
import aircox_cms.settings as settings

from aircox_cms.models.lists import *
from aircox_cms.models.sections import *
from aircox_cms.template import TemplateMixin
from aircox_cms.utils import image_url


@register_setting
class WebsiteSettings(BaseSetting):
    station = models.OneToOneField(
        aircox.models.Station,
        verbose_name = _('aircox station'),
        related_name = 'website_settings',
        unique = True,
        blank = True, null = True,
        help_text = _(
            'refers to an Aircox\'s station; it is used to make the link '
            'between the website and Aircox'
        ),
    )

    # general website information
    favicon = models.ImageField(
        verbose_name = _('favicon'),
        null=True, blank=True,
        help_text = _('small logo for the website displayed in the browser'),
    )
    tags = models.CharField(
        _('tags'),
        max_length=256,
        null=True, blank=True,
        help_text = _('tags describing the website; used for referencing'),
    )
    description = models.CharField(
        _('public description'),
        max_length=256,
        null=True, blank=True,
        help_text = _('public description of the website; used for referencing'),
    )
    list_page = models.ForeignKey(
        'aircox_cms.DynamicListPage',
        verbose_name = _('page for lists'),
        help_text=_('page used to display the results of a search and other '
                    'lists'),
        related_name= 'list_page',
        blank = True, null = True,
    )
    # comments
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
        help_text = _(
            'message displayed when a comment has been successfully posted'
        ),
    )
    comment_wait_message = models.TextField(
        _('waiting message'),
        default = _('Your comment is awaiting for approval.'),
        help_text = _(
            'message displayed when a comment has been sent, but waits for '
            ' website administrators\' approval.'
        ),
    )
    comment_error_message = models.TextField(
        _('error message'),
        default = _('We could not save your message. Please correct the error(s) below.'),
        help_text = _(
            'message displayed when the form of the comment has been '
            ' submitted but there is an error, such as an incomplete field'
        ),
    )

    sync = models.BooleanField(
        _('synchronize with Aircox'),
        default = False,
        help_text = _(
            'create publication for each object added to an Aircox\'s '
            'station; for example when there is a new program, or '
            'when a diffusion has been added to the timetable. Note: '
            'it does not concern the Station themselves.'
            # /doc/ the page is saved but not pubished -- this must be
            # done manually, when the user edit it.
        )
    )
    default_programs_page = ParentalKey(
        Page,
        verbose_name = _('default programs page'),
        blank = True, null = True,
        help_text = _(
            'when a new program is saved and a publication is created, '
            'put this publication as a child of this page. If no page '
            'has been specified, try to put it as the child of the '
            'website\'s root page (otherwise, do not create the page).'
            # /doc/ (technicians, admin): if the page has not been created,
            # it still can be created using the `programs_to_cms` command.
        ),
        limit_choices_to = lambda: {
            'show_in_menus': True,
            'publication__isnull': False,
        },
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('favicon'),
            FieldPanel('tags'),
            FieldPanel('description'),
            FieldPanel('list_page'),
        ], heading=_('Promotion')),
        MultiFieldPanel([
            FieldPanel('allow_comments'),
            FieldPanel('accept_comments'),
            FieldPanel('comment_success_message'),
            FieldPanel('comment_wait_message'),
            FieldPanel('comment_error_message'),
        ], heading = _('Comments')),
        MultiFieldPanel([
            FieldPanel('sync'),
            FieldPanel('default_programs_page'),
        ], heading = _('Programs and controls')),
    ]

    class Meta:
        verbose_name = _('website settings')


@register_snippet
class Comment(models.Model):
    publication = models.ForeignKey(
        Page,
        verbose_name = _('page')
    )
    published = models.BooleanField(
        verbose_name = _('published'),
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

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    def __str__(self):
        # Translators: text shown in the comments list (in admin)
        return _('{date}, {author}: {content}...').format(
                author = self.author,
                date = self.date.strftime('%d %A %Y, %H:%M'),
                content = self.content[:128]
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


class BasePage(Page):
    body = RichTextField(
        _('body'),
        null = True, blank = True,
        help_text = _('the publication itself')
    )
    cover = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('cover'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text = _('image to use as cover of the publication'),
    )
    allow_comments = models.BooleanField(
        _('allow comments'),
        default = True,
        help_text = _('allow comments')
    )

    # panels
    content_panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            ImageChooserPanel('cover'),
            FieldPanel('body', classname='full'),
        ], heading=_('Content'))
    ]
    settings_panels = Page.settings_panels + [
        FieldPanel('allow_comments'),
    ]
    search_fields = [
        index.SearchField('title', partial_match=True),
        index.SearchField('body', partial_match=True),
        index.FilterField('live'),
        index.FilterField('show_in_menus'),
    ]

    # properties
    @property
    def url(self):
        if not self.live:
            parent = self.get_parent().specific
            return parent and parent.url
        return super().url

    @property
    def icon(self):
        return image_url(self.cover, 'fill-64x64')

    @property
    def small_icon(self):
        return image_url(self.cover, 'fill-32x32')

    @property
    def comments(self):
        return Comment.objects.filter(
            publication = self,
            published = True,
        ).order_by('-date')

    # methods
    def get_list_page(self):
        """
        Return the page that should be used for lists related to this
        page. If None is returned, use a default one.
        """
        return None

    def get_context(self, request, *args, **kwargs):
        from aircox_cms.forms import CommentForm

        context = super().get_context(request, *args, **kwargs)
        if self.allow_comments and \
                WebsiteSettings.for_site(request.site).allow_comments:
            context['comment_form'] = CommentForm()

        context['settings'] = {
            'debug': settings.DEBUG
        }
        return context

    def serve(self, request):
        from aircox_cms.forms import CommentForm
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

    class Meta:
        abstract = True


#
# Publications
#
class PublicationRelatedLink(RelatedLinkBase,Component):
    template = 'aircox_cms/snippets/link.html'
    parent = ParentalKey('Publication', related_name='links')

class PublicationTag(TaggedItemBase):
    content_object = ParentalKey('Publication', related_name='tagged_items')

class Publication(BasePage):
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

    headline = models.TextField(
        _('headline'),
        blank = True, null = True,
        help_text = _('headline of the publication, use it as an introduction'),
    )
    tags = ClusterTaggableManager(
        verbose_name = _('tags'),
        through=PublicationTag,
        blank=True
    )

    class Meta:
        verbose_name = _('Publication')
        verbose_name_plural = _('Publication')

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            ImageChooserPanel('cover'),
            FieldPanel('headline'),
            FieldPanel('body', classname='full'),
        ], heading=_('Content'))
    ]
    promote_panels = [
        MultiFieldPanel([
            FieldPanel('tags'),
            FieldPanel('focus'),
        ], heading=_('Content')),
    ] + Page.promote_panels
    settings_panels = Page.settings_panels + [
        FieldPanel('publish_as'),
        FieldPanel('allow_comments'),
    ]
    search_fields = BasePage.search_fields + [
        index.SearchField('headline', partial_match=True),
    ]


    @property
    def recents(self):
        return self.get_children().type(Publication).not_in_menu().live() \
                   .order_by('-publication__date')

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        view = request.GET.get('view')
        context.update({
            'view': view,
            'page': self,
        })
        if view == 'list':
            context.update(BaseList.from_request(request, related = self))
            context['list_url_args'] += '&view=list'
        return context

    def save(self, *args, **kwargs):
        if not self.date and self.first_published_at:
            self.date = self.first_published_at
        return super().save(*args, **kwargs)


class ProgramPage(Publication):
    program = models.OneToOneField(
        aircox.models.Program,
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
        # FieldPanel('program'),
    ] + Publication.content_panels

    settings_panels = Publication.settings_panels + [
        FieldPanel('email'),
        FieldPanel('email_is_public'),
    ]

    def diffs_to_page(self, diffs):
        for diff in diffs:
            if not diff.page:
                diff.page = ListItem(
                    title = '{}, {}'.format(
                        self.program.name, diff.date.strftime('%d %B %Y')
                    ),
                    cover = self.cover,
                    live = True,
                    date = diff.start,
                )
        return [
            diff.page for diff in diffs if diff.page.live
        ]

    @property
    def next(self):
        now = tz.now()
        diffs = aircox.models.Diffusion.objects \
                    .filter(end__gte = now, program = self.program) \
                    .order_by('start').prefetch_related('page')
        return self.diffs_to_page(diffs)

    @property
    def prev(self):
        now = tz.now()
        diffs = aircox.models.Diffusion.objects \
                    .filter(end__lte = now, program = self.program) \
                    .order_by('-start').prefetch_related('page')
        return self.diffs_to_page(diffs)

    def save(self, *args, **kwargs):
        # set publish_as
        if self.program and not self.pk:
            super().save()
            self.publish_as = self
        super().save(*args, **kwargs)


class Track(aircox.models.Track,Orderable):
    diffusion = ParentalKey(
        'DiffusionPage', related_name='tracks',
        null = True, blank = True,
        on_delete = models.SET_NULL
    )

    sort_order_field = 'position'
    panels = [
        FieldPanel('artist'),
        FieldPanel('title'),
        FieldPanel('tags'),
        FieldPanel('info'),
    ]

    def save(self, *args, **kwargs):
        if self.diffusion.diffusion:
            self.related = self.diffusion.diffusion
        self.in_seconds = False
        super().save(*args, **kwargs)


class DiffusionPage(Publication):
    diffusion = models.OneToOneField(
        aircox.models.Diffusion,
        verbose_name = _('diffusion'),
        related_name = 'page',
        null=True, blank = True,
        # not blank because we enforce the connection to a diffusion
        #   (still users always tend to break sth)
        on_delete=models.SET_NULL,
        limit_choices_to = {
            'initial__isnull': True,
        },
    )
    publish_archive = models.BooleanField(
        _('publish archive'),
        default = False,
        help_text = _('publish the podcast of the complete diffusion'),
    )

    class Meta:
        verbose_name = _('Diffusion')
        verbose_name_plural = _('Diffusions')

    content_panels = Publication.content_panels + [
        InlinePanel('tracks', label=_('Tracks')),
    ]
    promote_panels = [
        MultiFieldPanel([
            FieldPanel('publish_archive'),
            FieldPanel('tags'),
            FieldPanel('focus'),
        ], heading=_('Content')),
    ] + Page.promote_panels
    settings_panels = Publication.settings_panels + [
        FieldPanel('diffusion')
    ]

    @classmethod
    def from_diffusion(cl, diff, model = None, **kwargs):
        model = model or cl
        model_kwargs = {
            'diffusion': diff,
            'title': '{}, {}'.format(
                diff.program.name, tz.localtime(diff.date).strftime('%d %B %Y')
            ),
            'cover': (diff.program.page and \
                        diff.program.page.cover) or None,
            'date': diff.start,
        }
        model_kwargs.update(kwargs)
        r = model(**model_kwargs)
        return r

    @classmethod
    def as_item(cl, diff):
        """
        Return a DiffusionPage or ListItem from a Diffusion.
        """
        initial = diff.initial or diff

        if hasattr(initial, 'page'):
            item = initial.page
        else:
            item = cl.from_diffusion(diff, ListItem)
            item.live = True

        item.info = []
        # Translators: informations about a diffusion
        if diff.initial:
            item.info.append(_('Rerun of %(date)s') % {
                'date': diff.initial.start.strftime('%A %d')
            })
        if diff.type == diff.Type.canceled:
            item.info.append(_('Cancelled'))
        item.info = '; '.join(item.info)

        item.date = diff.start
        item.css_class = 'diffusion'

        now = tz.now()
        if diff.start <= now <= diff.end:
            item.css_class = ' now'
            item.now = True

        return item

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['podcasts'] = self.diffusion and SectionPlaylist(
            title=_('Podcasts'),
            page = self,
            sounds = self.diffusion.get_sounds(
                archive = self.publish_archive, excerpt = True
            )
        )
        return context

    def save(self, *args, **kwargs):
        if self.diffusion:
            # force to sort by diffusion date in wagtail explorer
            self.latest_revision_created_at = self.diffusion.start

            # set publish_as
            if not self.pk:
                self.publish_as = self.diffusion.program.page

            # sync date
            self.date = self.diffusion.start

            # update podcasts' attributes
            for podcast in self.diffusion.sound_set \
                    .exclude(type = aircox.models.Sound.Type.removed):
                publish = self.live and self.publish_archive \
                    if podcast.type == podcast.Type.archive else self.live

                if podcast.public != publish:
                    podcast.public = publish
                    podcast.save()

        super().save(*args, **kwargs)


#
# Others types of pages
#

class CategoryPage(BasePage, BaseList):
    # TODO: hide related in panels?
    content_panels = BasePage.content_panels + BaseList.panels

    def get_list_page(self):
        return self

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context.update(BaseList.get_context(self, request, paginate = True))
        context['view'] = 'list'
        return context

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we force related attribute
        if not self.related:
            self.related = self


class DynamicListPage(BasePage):
    """
    Displays a list of publications using query passed by the url.
    This can be used for search/tags page, and generally only one
    page is used per website.

    If a title is given, use it instead of the generated one.
    """
    # FIXME/TODO: title in template <title></title>
    # TODO: personnalized titles depending on request
    class Meta:
        verbose_name = _('Dynamic List Page')
        verbose_name_plural = _('Dynamic List Pages')

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context.update(BaseList.from_request(request))
        return context


class DatedListPage(DatedBaseList,BasePage):
    class Meta:
        abstract = True

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
        context['target'] = self
        return context


class LogsPage(DatedListPage):
    template = 'aircox_cms/dated_list_page.html'

    # TODO: make it a property that automatically select the station
    station = models.ForeignKey(
        aircox.models.Station,
        verbose_name = _('station'),
        null = True, blank = True,
        on_delete = models.SET_NULL,
        help_text = _('(required) related station')
    )
    max_age = models.IntegerField(
        _('maximum age'),
        default=15,
        help_text = _('maximum days in the past allowed to be shown. '
                      '0 means no limit')
    )
    reverse = models.BooleanField(
        _('reverse list'),
        default=False,
        help_text = _('print logs in ascending order by date'),
    )

    class Meta:
        verbose_name = _('Logs')
        verbose_name_plural = _('Logs')

    content_panels = DatedListPage.content_panels + [
        MultiFieldPanel([
            FieldPanel('station'),
            FieldPanel('max_age'),
            FieldPanel('reverse'),
        ], heading=_('Configuration')),
    ]

    def get_nav_dates(self, date):
        """
        Return a list of dates availables for the navigation
        """
        # there might be a bug if max_age < nav_days
        today = tz.now().date()
        first = min(date, today)
        first = first - tz.timedelta(days = self.nav_days-1)
        if self.max_age:
             first = max(first, today - tz.timedelta(days = self.max_age))
        return [ first + tz.timedelta(days=i)
                    for i in range(0, self.nav_days) ]

    def get_queryset(self, request, context):
        today = tz.now().date()
        if self.max_age and context['nav_dates']['next'] > today:
            context['nav_dates']['next'] = None
        if self.max_age and context['nav_dates']['prev'] < \
                today - tz.timedelta(days = self.max_age):
            context['nav_dates']['prev'] = None

        logs = []
        for date in context['nav_dates']['dates']:
            items = self.station.on_air(date = date) \
                        .select_related('track','diffusion')
            items = [ SectionLogsList.as_item(item) for item in items ]
            logs.append(
                (date, reversed(items) if self.reverse else items)
            )
        return logs


class TimetablePage(DatedListPage):
    template = 'aircox_cms/dated_list_page.html'
    station = models.ForeignKey(
        aircox.models.Station,
        verbose_name = _('station'),
        on_delete = models.SET_NULL,
        null = True, blank = True,
        help_text = _('(required) related station')
    )

    content_panels = DatedListPage.content_panels + [
        MultiFieldPanel([
            FieldPanel('station'),
        ], heading=_('Configuration')),
    ]

    class Meta:
        verbose_name = _('Timetable')
        verbose_name_plural = _('Timetable')

    def get_queryset(self, request, context):
        diffs = []
        for date in context['nav_dates']['dates']:
            items = aircox.models.Diffusion.objects.at(self.station, date)
            items = [ DiffusionPage.as_item(item) for item in items ]
            diffs.append((date, items))
        return diffs



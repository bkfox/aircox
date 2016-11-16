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

from aircox_cms.utils import image_url
from aircox_cms.sections import *


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


class PublicationRelatedLink(RelatedLinkBase):
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

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('body', classname='full'),
            FieldPanel('summary'),
        ], heading=_('Content'))
    ]
    promote_panels = [
        MultiFieldPanel([
            ImageChooserPanel('cover'),
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
        index.SearchField('title', partial_match=True),
        index.SearchField('body', partial_match=True),
        index.FilterField('live'),
        index.FilterField('show_in_menus'),
    ]

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
        from aircox_cms.forms import CommentForm
        context = super().get_context(request, *args, **kwargs)
        view = request.GET.get('view')
        page = request.GET.get('page')

        if self.allow_comments and \
                WebsiteSettings.for_site(request.site).allow_comments:
            context['comment_form'] = CommentForm()

        if view == 'list':
            context['object_list'] = ListBase.from_request(
                request, context = context, related = self
            )
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


class ProgramPage(Publication):
    program = models.ForeignKey(
        aircox.models.Program,
        verbose_name = _('program'),
        related_name = 'page',
        on_delete=models.SET_NULL,
        unique = True,
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


class Track(aircox.models.Track,Orderable):
    diffusion = ParentalKey('DiffusionPage',
                            related_name='tracks')

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
    order_field = 'diffusion__start'

    diffusion = models.ForeignKey(
        aircox.models.Diffusion,
        verbose_name = _('diffusion'),
        related_name = 'page',
        unique = True,
        null=True,
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
        # FieldPanel('diffusion'),
        FieldPanel('publish_archive'),
    ] + Publication.promote_panels

    @classmethod
    def from_diffusion(cl, diff, model = None, **kwargs):
        model = model or cl
        model_kwargs = {
            'diffusion': diff,
            'title': '{}, {}'.format(
                diff.program.name, tz.localtime(diff.date).strftime('%d %B %Y')
            ),
            'cover': (diff.program.page.count() and \
                        diff.program.page.first().cover) or None,
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

        if initial.page.all().count():
            item = initial.page.all().first()
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
        return item

    def get_archive(self):
        """
        Return the diffusion's archive as podcast
        """
        if not self.publish_archive or not self.diffusion:
            return

        sound = self.diffusion.get_archives() \
                    .filter(public = True).first()
        if sound:
            sound.detail_url = self.detail_url
        return sound

    def get_podcasts(self):
        """
        Return a list of podcasts, with archive as the first item of the
        list when available.
        """
        podcasts = []
        archive = self.get_archive()
        if archive:
            podcasts.append(archive)

        qs = self.diffusion.get_excerpts().filter(public = True)
        podcasts.extend(qs[:])
        for podcast in podcasts:
            podcast.detail_url = self.url
        return podcasts

    def save(self, *args, **kwargs):
        if self.diffusion:
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
class DynamicListPage(Page):
    """
    Displays a list of publications using query passed by the url.
    This can be used for search/tags page, and generally only one
    page is used per website.

    If a title is given, use it instead of the generated one.
    """
    # FIXME/TODO: title in template <title></title>
    body = RichTextField(
        _('body'),
        blank = True, null = True,
        help_text = _('add an extra description for this list')
    )

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('body'),
        ], heading=_('Content'))
    ]

    class Meta:
        verbose_name = _('Dynamic List Page')
        verbose_name_plural = _('Dynamic List Pages')

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
    template = 'aircox_cms/dated_list_page.html'

    # TODO: make it a property that automatically select the station
    station = models.ForeignKey(
        aircox.models.Station,
        verbose_name = _('station'),
        null = True,
        on_delete=models.SET_NULL,
        help_text = _('(required) the station on which the logs happened')
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
            items = [ SectionLogsList.as_item(item)
                        for item in self.station.on_air(date = date) ]
            logs.append((date, items))
        return logs


class TimetablePage(DatedListPage):
    template = 'aircox_cms/dated_list_page.html'

    class Meta:
        verbose_name = _('Timetable')
        verbose_name_plural = _('Timetable')

    def get_queryset(self, request, context):
        diffs = []
        for date in context['nav_dates']['dates']:
            items = aircox.models.Diffusion.objects.get_at(date).order_by('start')
            items = [ DiffusionPage.as_item(item) for item in items ]
            diffs.append((date, items))
        return diffs



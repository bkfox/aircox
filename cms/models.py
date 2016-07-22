
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
import aircox.cms.settings as settings


@register_setting
class WebsiteSettings(BaseSetting):
    logo = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name = _('logo'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
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


class RelatedLink(Orderable):
    parent = ParentalKey('Publication', related_name='related_links')
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

    panels = [
        FieldPanel('url'),
        FieldRowPanel([
            FieldPanel('title'),
            ImageChooserPanel('icon'),
        ]),
    ]


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

    @classmethod
    def get_queryset(cl, request, *args,
                     thread = None, context = {},
                     **kwargs):
        """
        Return a queryset from the request's GET parameters. Context
        can be used to update relative informations.

        Parameters:
        * type:     ['program','diffusion','event'] type of the publication
        * tag:      tag to search for
        * search:   query to search in the publications
        * thread:   children of the thread passed in arguments only
        * order:    ['asc','desc'] sort ordering
        * page:     page number

        Context's fields:
        * list_type:        type of the items in the list (as Page subclass)
        * tag_query:        tag searched for
        * search_query:     search terms
        * thread_query:     thread
        * paginator:        paginator object
        """
        if 'thread' in request.GET and thread:
            qs = self.get_children()
            context['thread_query'] = thread
        else:
            qs = cl.objects.all()
        qs = qs.not_in_menu().live()

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

        # ordering
        order = request.GET.get('order')
        if order not in ('asc','desc'):
            order = 'desc'
        qs = qs.order_by(
            ('-' if order == 'desc' else '') + 'first_published_at'
        )

        qs = self.get_queryset(request, *args, context, **kwargs)
        if qs:
            paginator = Paginator(qs, 30)
            try:
                qs = paginator.page('page')
            except PageNotAnInteger:
                qs = paginator.page(1)
            except EmptyPage:
                qs = parginator.page(paginator.num_pages)
            context['paginator'] = paginator
        return qs

    def get_context(self, request, *args, **kwargs):
        from aircox.cms.forms import CommentForm
        context = super().get_context(request, *args, **kwargs)
        view = request.GET.get('view')
        page = request.GET.get('page')

        if self.allow_comments and \
                WebsiteSettings.for_site(request.site).allow_comments:
            context['comment_form'] = CommentForm()

        if view == 'list':
            context['object_list'] = self.get_queryset(
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
                )
            diff.page_.date = diff.start
        return [
            diff.page_ for diff in diffs if diff.page_.live
        ]

    def next_diffs(self):
        now = tz.now()
        diffs = programs.Diffusion.objects \
                    .filter(end__gte = now, program = self.program) \
                    .order_by('start').prefetch_related('page')
        return self.diffs_to_page(diffs)

    def prev_diffs(self):
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




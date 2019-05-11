from enum import IntEnum

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.functional import cached_property
from django.urls import reverse

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import *
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.snippets.models import register_snippet

import aircox.models
from aircox_cms.models.lists import *
from aircox_cms.views.components import Component, ExposedData
from aircox_cms.utils import related_pages_filter


@register_snippet
class Region(ClusterableModel):
    """
    Region is a container of multiple items of different types
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
        on_delete=models.CASCADE,
        verbose_name = _('model'),
        blank = True, null = True,
        help_text=_('this section is displayed only when the current '
                    'page or publication is of this type'),
        limit_choices_to = related_pages_filter,
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
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
        # InlinePanel('items', label=_('Region Items')),
    ]

    @classmethod
    def get_sections_at (cl, position, page = None):
        """
        Return a queryset of sections that are at the given position.
        Filter out Region that are not for the given page.
        """
        qs = Region.objects.filter(position = position)
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
class Section(Component, models.Model):
    """
    Section is a widget configurable by user that can be rendered inside
    Regions.
    """
    template_name = 'aircox_cms/sections/section.html'
    section = ParentalKey(Region, related_name='items')
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

    template_name = 'aircox_cms/sections/item.html'

    panels = [
        MultiFieldPanel([
            FieldPanel('section'),
            FieldPanel('title'),
            FieldPanel('show_title'),
            FieldPanel('order'),
            FieldPanel('css_class'),
        ], heading=_('General')),
    ]

    # TODO make it reusable
    @cached_property
    def specific(self):
        """
        Return a downcasted version of the model if it is from another
        model, or itself
        """
        if not self.real_type or type(self) != Section:
            return self
        return getattr(self, self.real_type)

    def save(self, *args, **kwargs):
        if type(self) != Section and not self.real_type:
            self.real_type = type(self).__name__.lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return '{}: {}'.format(
            (self.real_type or 'section item').replace('section','section '),
            self.title or self.pk
        )

class SectionRelativeItem(Section):
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

    panels = Section.panels.copy()
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
class SectionText(Section):
    template_name = 'aircox_cms/sections/text.html'
    body = RichTextField()
    panels = Section.panels + [
        FieldPanel('body'),
    ]

    def get_context(self, request, page):
        from wagtail.core.rich_text import expand_db_html
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
        on_delete=models.CASCADE,
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

    panels = Section.panels + [
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
        from wagtail.images.views.serve import generate_signature
        context = super().get_context(request, page)

        image = self.related_attr(page, 'cover') or self.image
        if not image:
            return context

        context['content'] = self.ensure_cache(image)
        return context


@register_snippet
class SectionLinkList(ClusterableModel, Section):
    template_name = 'aircox_cms/sections/link_list.html'
    panels = Section.panels + [
        InlinePanel('links', label=_('Links')),
    ]


@register_snippet
class SectionLink(RelatedLinkBase, Component):
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
    template_name = 'aircox_cms/sections/list.html'
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
            self.hide = True
            return {}

        context.update(SectionRelativeItem.get_context(self, request, page))
        if self.url_text:
            self.related = self.related and self.related.specific
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
class SectionLogsList(Section):
    template_name = 'aircox_cms/sections/logs_list.html'
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

    panels = Section.panels + [
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
class SectionTimetable(Section,DatedBaseList):
    template_name = 'aircox_cms/sections/timetable.html'
    class Meta:
        verbose_name = _('Section: Timetable')
        verbose_name_plural = _('Sections: Timetable')

    station = models.ForeignKey(
        aircox.models.Station,
        on_delete=models.CASCADE,
        verbose_name = _('station'),
        help_text = _('(required) related station')
    )
    target = models.ForeignKey(
        'aircox_cms.TimetablePage',
        on_delete=models.CASCADE,
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
    panels = Section.panels + DatedBaseList.panels + [
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
            items = [
                DiffusionPage.as_item(item)
                for item in aircox.models.Diffusion.objects \
                                  .station(self.station).at(date)
            ]
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
class SectionPublicationInfo(Section):
    template_name = 'aircox_cms/sections/publication_info.html'
    class Meta:
        verbose_name = _('Section: publication\'s info')
        verbose_name_plural = _('Sections: publication\'s info')

@register_snippet
class SectionSearchField(Section):
    template_name = 'aircox_cms/sections/search_field.html'
    default_text = models.CharField(
        _('default text'),
        max_length=32,
        default=_('search'),
        help_text=_('text to display when the search field is empty'),
    )

    class Meta:
        verbose_name = _('Section: search field')
        verbose_name_plural = _('Sections: search field')

    panels = Section.panels + [
        FieldPanel('default_text'),
    ]



@register_snippet
class SectionPlaylist(Section):
    """
    User playlist. Can be used to add sounds in it -- there should
    only be one for the moment.
    """
    class Track(ExposedData):
        """
        Class exposed to Javascript playlist manager as Track.
        """
        fields = {
            'name': 'name',
            'embed': 'embed',
            'duration': lambda e, o:
                o.duration.hour * 3600 + o.duration.minute * 60 +
                o.duration.second
            ,
            'duration_str': lambda e, o:
                (str(o.duration.hour) + '"' if o.duration.hour else '') +
                str(o.duration.minute) + "'" + str(o.duration.second)
            ,
            'sources': lambda e, o: [ o.url() ],
            'detail_url':
                lambda e, o: o.diffusion and hasattr(o.diffusion, 'page') \
                                and o.diffusion.page.url
                ,
            'cover':
                lambda e, o: o.diffusion and hasattr(o.diffusion, 'page') \
                                and o.diffusion.page.icon
                ,
        }

    user_playlist = models.BooleanField(
        _('user playlist'),
        default = False,
        help_text = _(
            'this is a user playlist, it can be edited and saved by the '
            'users (the modifications will NOT be registered on the server)'
        )
    )
    read_all = models.BooleanField(
        _('read all'),
        default = True,
        help_text = _(
            'by default at the end of the sound play the next one'
        )
    )

    tracks = None

    template_name = 'aircox_cms/sections/playlist.html'
    panels = Section.panels + [
        FieldPanel('user_playlist'),
        FieldPanel('read_all'),
    ]

    def __init__(self, *args, sounds = None, tracks = None, page = None, **kwargs):
        """
        Init playlist section. If ``sounds`` is given initialize playlist
        tracks with it. If ``page`` is given use it for Track infos
        related to a page (cover, detail_url, ...)
        """
        self.tracks = (tracks or []) + [
            self.Track(object = sound, detail_url = page and page.url,
                       cover = page and page.icon)
            for sound in sounds or []
        ]
        super().__init__(*args, **kwargs)

    def get_context(self, request, page):
        context = super().get_context(request, page)
        context.update({
            'is_default': self.user_playlist,
            'modifiable': self.user_playlist,
            'storage_key': self.user_playlist and str(self.pk),
            'read_all': self.read_all,
            'tracks': self.tracks
        })
        if not self.user_playlist and not self.tracks:
            self.hide = True
        return context


@register_snippet
class SectionPlayer(Section):
    """
    Radio stream player.
    """
    template_name = 'aircox_cms/sections/playlist.html'
    live_title = models.CharField(
        _('live title'),
        max_length = 32,
        help_text = _('text to display when it plays live'),
    )
    streams = models.TextField(
        _('audio streams'),
        help_text = _('one audio stream per line'),
    )
    icon = models.ImageField(
        _('icon'),
        blank = True, null = True,
        help_text = _('icon to display in the player')
    )

    class Meta:
        verbose_name = _('Section: Player')

    panels = Section.panels + [
        FieldPanel('live_title'),
        FieldPanel('icon'),
        FieldPanel('streams'),
    ]

    def get_context(self, request, page):
        context = super().get_context(request, page)
        context['tracks'] = [SectionPlaylist.Track(
            name = self.live_title,
            sources = self.streams.split('\r\n'),
            data_url = reverse('aircox.on_air'),
            interval = 10,
            run = True,
        )]
        return context



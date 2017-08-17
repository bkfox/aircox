import json

from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.forms import SelectMultiple, TextInput
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem, Menu, SubmenuMenuItem
from wagtail.wagtailcore.models import PageRevision
from wagtail.contrib.modeladmin.options import \
    ModelAdmin, ModelAdminGroup, modeladmin_register
from wagtail.wagtailadmin.edit_handlers import FieldPanel, FieldRowPanel, \
        MultiFieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel


import aircox.models
import aircox_cms.models as models


class RelatedListWidget(SelectMultiple):
    def __init__(self, *args, **kwargs):
        self.readonly = True
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        self.choices.queryset = self.choices.queryset.filter(pk__in = value)
        return super().get_context(name, value, attrs)

#
# ModelAdmin items
#
class ProgramAdmin(ModelAdmin):
    model = aircox.models.Program
    menu_label = _('Programs')
    menu_icon = 'pick'
    menu_order = 200
    list_display = ('name', 'active', 'station')
    search_fields = ('name',)

aircox.models.Program.panels = [
    MultiFieldPanel([
        FieldPanel('name'),
        FieldPanel('active'),
        FieldPanel('sync'),
    ], heading=_('Program')),
]


class DiffusionAdmin(ModelAdmin):
    model = aircox.models.Diffusion
    menu_label = _('Diffusions')
    menu_icon = 'date'
    menu_order = 200
    list_display = ('program', 'start', 'end', 'type', 'initial')
    list_filter = ('program', 'start', 'type')
    readonly_fields = ('conflicts',)
    search_fields = ('program__name', 'start')

aircox.models.Diffusion.panels = [
    MultiFieldPanel([
        FieldPanel('program'),
        FieldPanel('type'),
        FieldRowPanel([
            FieldPanel('start'),
            FieldPanel('end'),
        ]),
        FieldPanel('initial'),
        FieldPanel(
            'conflicts',
            widget = RelatedListWidget(
                attrs = {
                    'disabled': True,
                }
            )
        ),
    ], heading=_('Diffusion')),
]


class ScheduleAdmin(ModelAdmin):
    model = aircox.models.Schedule
    menu_label = _('Schedules')
    menu_icon = 'time'
    menu_order = 200
    list_display = ('program', 'frequency', 'duration', 'initial')
    list_filter = ('frequency', 'date', 'duration', 'program')

aircox.models.Schedule.panels = [
    MultiFieldPanel([
        FieldPanel('program'),
        FieldPanel('frequency'),
        FieldRowPanel([
            FieldPanel('date'),
            FieldPanel('duration'),
        ]),
        FieldPanel('initial'),
    ], heading=_('Schedule')),
]


class StreamAdmin(ModelAdmin):
    model = aircox.models.Stream
    menu_label = _('Streams')
    menu_icon = 'time'
    menu_order = 200
    list_display = ('program', 'delay', 'begin', 'end')
    list_filter = ('program', 'delay', 'begin', 'end')

aircox.models.Stream.panels = [
    MultiFieldPanel([
        FieldPanel('program'),
        FieldPanel('delay'),
        FieldRowPanel([
            FieldPanel('begin'),
            FieldPanel('end'),
        ]),
    ], heading=_('Stream')),
]


class LogAdmin(ModelAdmin):
    model = aircox.models.Log
    menu_label = _('Logs')
    menu_icon = 'time'
    menu_order = 300
    list_display = ['id', 'date', 'station', 'source', 'type', 'comment', 'diffusion', 'sound', 'track']
    list_filter = ['date', 'source', 'diffusion', 'sound', 'track']

aircox.models.Log.panels = [
    MultiFieldPanel([
        FieldPanel('date'),
        FieldRowPanel([
            FieldPanel('station'),
            FieldPanel('source'),
        ]),
        FieldPanel('type'),
        FieldPanel('comment'),
    ], heading = _('Log')),
    MultiFieldPanel([
        FieldPanel('diffusion'),
        FieldPanel('sound'),
        FieldPanel('track'),
    ], heading = _('Related objects')),
]


# Missing: Port, Station, Track

class AdvancedAdminGroup(ModelAdminGroup):
    menu_label = _("Advanced")
    menu_icon = 'plus-inverse'
    items = (ProgramAdmin, DiffusionAdmin, ScheduleAdmin, StreamAdmin, LogAdmin)

modeladmin_register(AdvancedAdminGroup)


class CommentAdmin(ModelAdmin):
    model = models.Comment
    menu_label = _('Comments')
    menu_icon = 'pick'
    menu_order = 300
    list_display = ('published', 'publication', 'author', 'date', 'content')
    list_filter = ('date', 'published')
    search_fields = ('author', 'content', 'publication__title')

modeladmin_register(CommentAdmin)

class SoundAdmin(ModelAdmin):
    model = aircox.models.Sound
    menu_label = _('Sounds')
    menu_icon = 'media'
    menu_order = 350
    list_display = ('name', 'program', 'type', 'duration', 'path', 'good_quality', 'public')
    list_filter = ('program', 'type', 'good_quality', 'public')
    search_fields = ('name', 'path')

modeladmin_register(SoundAdmin)


#
# Menus with sub-menus
#
class GenericMenu(Menu):
    page_model = models.Publication
    """
    Model of the page for the items
    """
    explore = False
    """
    If True, show page explorer instead of page editor.
    """
    request = None
    """
    Current request
    """
    station = None
    """
    Current station
    """

    def __init__(self):
        super().__init__('')

    def get_queryset(self):
        """
        Return a queryset of items used to display menu
        """
        pass

    def make_item(self, item):
        """
        Return the instance of MenuItem for the given item in the queryset
        """
        pass

    def get_parent(self, item):
        """
        Return id of the parent page for the given item of the queryset
        """
        pass

    @staticmethod
    def page_of(item):
        return hasattr(item, 'page') and item.page

    def page_url(self, item):
        page = self.page_of(item)
        if page:
            name =  'wagtailadmin_explore' \
                    if self.explore else 'wagtailadmin_pages:edit'
            return reverse(name, args=[page.id])

        parent_page = self.get_parent(item)
        if not parent_page:
            return ''

        return reverse(
            'wagtailadmin_pages:add', args= [
                self.page_model._meta.app_label,
                self.page_model._meta.model_name,
                parent_page.id
            ]
        )

    @property
    def registered_menu_items(self):
        now = tz.now()
        last_max = now - tz.timedelta(minutes = 10)

        qs = self.get_queryset()
        return [
            self.make_item(item) for item in qs
        ]

    def render_html(self, request):
        self.request = request
        self.station = self.request and self.request.aircox.station
        return super().render_html(request)


class GroupMenuItem(MenuItem):
    """
    Display a list of items based on given list of items
    """
    def __init__(self, label, *args, **kwargs):
        super().__init__(label, None, *args, **kwargs)

    def get_queryset(self):
        pass

    def make_item(self, item):
        pass

    def render_html(self, request):
        self.request = request
        self.station = self.request and self.request.aircox.station

        title = '</ul><h2>{}</h2><ul>'.format(self.label)
        qs = [
            self.make_item(item).render_html(request)
                for item in self.get_queryset()
        ]
        return title + '\n'.join(qs)


#
# Today's diffusions menu
#
class TodayMenu(GenericMenu):
    """
    Menu to display today's diffusions
    """
    page_model = models.DiffusionPage

    def get_queryset(self):
        qs = aircox.models.Diffusion.objects
        if self.station:
            qs = qs.filter(program__station = self.station)

        return qs.filter(
            type = aircox.models.Diffusion.Type.normal,
            start__contains = tz.now().date(),
            initial__isnull = True,
        ).order_by('start')

    def make_item(self, item):
        label = mark_safe(
            '<i class="info">{}</i> {}'.format(
                tz.localtime(item.start).strftime('%H:%M'),
                item.program.name
            )
        )

        attrs = {}

        qs = hasattr(item, 'page') and \
                PageRevision.objects.filter(page = item.page)
        if qs and qs.count():
            headline = qs.latest('created_at').content_json
            headline = json.loads(headline).get('headline')
            attrs['title'] = headline
        else:
            headline = ''

        return MenuItem(label, self.page_url(item), attrs = attrs)

    def get_parent(self, item):
        return item.program.page


@hooks.register('register_admin_menu_item')
def register_programs_menu_item():
    return SubmenuMenuItem(
        _('Today\'s Diffusions'), TodayMenu(),
        classnames='icon icon-folder-open-inverse', order=101
    )


#
# Programs menu
#
class ProgramsMenu(GenericMenu):
    """
    Display all active programs
    """
    page_model = models.DiffusionPage
    explore = True

    def get_queryset(self):
        qs = aircox.models.Program.objects
        if self.station:
            qs = qs.filter(station = self.station)

        return qs.filter(active = True, page__isnull = False) \
                 .filter(stream__isnull = True) \
                 .order_by('name')

    def make_item(self, item):
        return MenuItem(item.name, self.page_url(item))

    def get_parent(self, item):
        # TODO: #Station / get current site
        from aircox_cms.models import WebsiteSettings
        settings = WebsiteSettings.objects.first()
        if not settings:
            return
        return settings.default_program_parent_page


@hooks.register('register_admin_menu_item')
def register_programs_menu_item():
    return SubmenuMenuItem(
        _('Programs'), ProgramsMenu(),
        classnames='icon icon-folder-open-inverse', order=102
    )


#
# Select station
#
# Submenu hides themselves if there are no children
#
#
class SelectStationMenuItem(GroupMenuItem):
    """
    Menu to display today's diffusions
    """
    def get_queryset(self):
        return aircox.models.Station.objects.all()

    def make_item(self, station):
        return MenuItem(
            station.name,
            reverse('wagtailadmin_home') + '?aircox.station=' + str(station.pk),
            classnames = 'icon ' + ('icon-success menu-active'
                if station == self.station else
                    'icon-cross'
                if not station.active else
                    ''
            )
        )

@hooks.register('register_settings_menu_item')
def register_select_station_menu_item():
    return SelectStationMenuItem(
        _('Current Station'), order=10000
    )




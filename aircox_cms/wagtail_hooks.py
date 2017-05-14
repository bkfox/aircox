from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import format_html

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem, Menu, SubmenuMenuItem

from wagtail.contrib.modeladmin.options import \
    ModelAdmin, ModelAdminGroup, modeladmin_register


import aircox.models
import aircox_cms.models as models

class ProgramAdmin(ModelAdmin):
    model = aircox.models.Program
    menu_label = _('Programs')
    menu_icon = 'pick'
    menu_order = 200
    list_display = ('name', 'active')
    search_fields = ('name',)

class DiffusionAdmin(ModelAdmin):
    model = aircox.models.Diffusion
    menu_label = _('Diffusions')
    menu_icon = 'date'
    menu_order = 200
    list_display = ('program', 'start', 'end', 'type', 'initial')
    list_filter = ('program', 'start', 'type')
    readonly_fields = ('conflicts',)
    search_fields = ('program__name', 'start')

class ScheduleAdmin(ModelAdmin):
    model = aircox.models.Schedule
    menu_label = _('Schedules')
    menu_icon = 'time'
    menu_order = 200
    list_display = ('program', 'frequency', 'duration', 'initial')
    list_filter = ('frequency', 'date', 'duration', 'program')

class StreamAdmin(ModelAdmin):
    model = aircox.models.Stream
    menu_label = _('Streams')
    menu_icon = 'time'
    menu_order = 200
    list_display = ('program', 'delay', 'begin', 'end')
    list_filter = ('program', 'delay', 'begin', 'end')

class AdvancedAdminGroup(ModelAdminGroup):
    menu_label = _("Advanced")
    menu_icon = 'plus-inverse'
    items = (ProgramAdmin, DiffusionAdmin, ScheduleAdmin, StreamAdmin)

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


## Hooks

@hooks.register('insert_editor_css')
def editor_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static('aircox_cms/css/cms.css')
    )


class GenericMenu(Menu):
    page_model = models.Publication
    explore = False
    """
    If True, show page explorer instead of page editor.
    """

    def __init__(self):
        super().__init__('')

    def get_queryset(self):
        """
        Return a queryset of items used to display menu
        """
        pass

    def get_title(self, item):
        """
        Return the title of a menu-item for the given item
        """
        pass

    def get_parent(self, item):
        """
        Return id of the parent page for the given item
        """
        pass

    def get_page_url(self, page_model, item):
        if item.page.count():
            name =  'wagtailadmin_explore' \
                    if self.explore else 'wagtailadmin_pages:edit'
            return reverse(name, args=[item.page.first().id])

        parent_page = self.get_parent(item)
        if not parent_page:
            return ''

        return reverse(
            'wagtailadmin_pages:add', args= [
                page_model._meta.app_label, page_model._meta.model_name,
                parent_page.id
            ]
        )

    @property
    def registered_menu_items(self):
        now = tz.now()
        last_max = now - tz.timedelta(minutes = 10)

        qs = self.get_queryset()
        return [
            MenuItem(self.get_title(x), self.get_page_url(self.page_model, x))
            for x in qs
        ]


class DiffusionsMenu(GenericMenu):
    """
    Menu to display diffusions of today
    """
    page_model = models.DiffusionPage

    def get_queryset(self):
        return aircox.models.Diffusion.objects.filter(
            type = aircox.models.Diffusion.Type.normal,
            start__contains = tz.now().date(),
            initial__isnull = True,
        ).order_by('start')

    def get_title(self, item):
        from django.utils.safestring import mark_safe
        from django.utils.timezone import localtime
        title = '<i class="info">{}</i> {}'.format(
            localtime(item.start).strftime('%H:%M'),
            item.program.name
        )
        return mark_safe(title)

    def get_parent(self, item):
        return item.program.page.first()


@hooks.register('register_admin_menu_item')
def register_programs_menu_item():
    return SubmenuMenuItem(
        _('Today\'s Diffusions'), DiffusionsMenu(),
        classnames='icon icon-folder-open-inverse', order=101
    )


class ProgramsMenu(GenericMenu):
    """
    Menu to display all active programs
    """
    page_model = models.DiffusionPage
    explore = True

    def get_queryset(self):
        return aircox.models.Program.objects \
                    .filter(active = True, page__isnull = False) \
                    .filter(stream__isnull = True) \
                    .order_by('name')

    def get_title(self, item):
        return item.name

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



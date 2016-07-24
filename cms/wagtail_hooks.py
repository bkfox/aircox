from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem, Menu, SubmenuMenuItem

import aircox.programs.models as programs

class GenericMenu(Menu):
    last_time = None

    def __init__(self):
        super().__init__('')

    def get_queryset(self):
        pass

    def get_title(self, item):
        pass

    def get_parent_page(self, item):
        pass

    def get_page_url(self, item):
        if item.page.count():
            return reverse('wagtailadmin_pages:edit', args=[item.page.first().id])
        parent_page = self.get_parent_page(item)
        if not parent_page:
            return ''
        return reverse('wagtailadmin_pages:add_subpage', args=[parent_page.id])

    @property
    def registered_menu_items(self):
        now = tz.now()
        last_max = now - tz.timedelta(minutes = 10)

        if self._registered_menu_items is None or self.last_time < last_max:
            qs = self.get_queryset()
            self._registered_menu_items =  [
                MenuItem(self.get_title(x), self.get_page_url(x))
                for x in qs
            ]
            self.last_time = now
        return self._registered_menu_items


class ProgramsMenu(GenericMenu):
    """
    Menu to display all active programs.
    """
    def get_queryset(self):
        return programs.Program.objects \
                    .filter(active = True, page__isnull = False) \
                    .filter(stream__isnull = True) \
                    .order_by('name')

    def get_title(self, item):
        return item.name

    def get_parent(self, item):
        # TODO: #Station / get current site
        from aircox.cms.models import WebsiteSettings
        settings = WebsiteSettings.objects.first()
        if not settings:
            return
        return settings.default_program_parent_page


class DiffusionsMenu(GenericMenu):
    """
    Menu to display diffusions of today
    """
    def get_queryset(self):
        return programs.Diffusion.objects.filter(
            type = programs.Diffusion.Type.normal,
            start__contains = tz.now().date() + tz.timedelta(days=2),
        ).order_by('start')

    def get_title(self, item):
        return item.program.name

    def get_parent(self, item):
        return item.program.page.first()


@hooks.register('register_admin_menu_item')
def register_programs_menu_item():
    return SubmenuMenuItem(
        _('Programs'), ProgramsMenu(),
        classnames='icon icon-folder-open-inverse', order=100
    )


@hooks.register('register_admin_menu_item')
def register_programs_menu_item():
    return SubmenuMenuItem(
        _('Today\'s Diffusions'), DiffusionsMenu(),
        classnames='icon icon-folder-open-inverse', order=100
    )




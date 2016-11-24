from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailcore.models import Page, Site

import aircox.models as aircox
import aircox_cms.models as models
import aircox_cms.sections as sections
import aircox_cms.utils as utils

# on a new diffusion

@receiver(post_save, sender=aircox.Station)
def station_post_saved(sender, instance, created, *args, **kwargs):
    """
    Create the basis for the website: set up settings and pages
    that are common.
    """
    if not created:
        return

    root_page = Page.objects.get(id=1)

    homepage = models.Publication(
        title = instance.name,
        slug = instance.slug,
        body = _(
            'If you see this page, then Aircox is running for the station '
            '{station.name}. You might want to change it to a better one. '
        ).format(station = instance),
    )
    root_page.add_child(instance=homepage)

    site = Site(
        # /doc/ when a Station is created, a wagtail Site is generated with
        #       default options. User must set the correct localhost afterwards
        hostname = instance.slug + ".local",
        port = 80,
        site_name = instance.name.capitalize(),
        root_page = homepage,
    )
    site.save()

    # settings
    website_settings = models.WebsiteSettings(
        site = site,
        station = instance,
        description = _("The website of the {name} radio").format(
            name = instance.name
        ),
        # Translators: tags set by default in <meta> description of the website
        tags = _('radio,{station.name}').format(station = instance)
    )

    # timetable
    timetable = models.TimetablePage(
        title = _('Timetable'),
    )
    homepage.add_child(instance = timetable)

    # list page (search, terms)
    list_page = models.DynamicListPage(
        # title is dynamic: no need to specify
        title = _('Search'),
    )
    homepage.add_child(instance = list_page)
    website_settings.list_page = list_page

    # programs' page: list of programs in a section
    programs = models.Publication(
        title = _('Programs'),
    )
    homepage.add_child(instance = programs)

    section = sections.Section(
        name = _('Programs'),
        position = 'post_content',
        page = programs,
    )
    section.save();
    section.add_item(sections.SectionList(
        count = 15,
        title = _('Programs'),
        url_text = _('All programs'),
        model = ContentType.objects.get_for_model(models.ProgramPage),
        related = programs,
    ))

    website_settings.default_programs_page = programs
    website_settings.sync = True

    # logs (because it is a cool feature)
    logs = models.LogsPage(
        title = _('Previously on air'),
        station = instance,
    )
    homepage.add_child(instance = logs)

    # save
    site.save()
    website_settings.save()


@receiver(post_save, sender=aircox.Program)
def program_post_saved(sender, instance, created, *args, **kwargs):
    if not created or instance.page.count():
        return

    settings = utils.get_station_settings(instance.station)
    if not settings or not settings.sync:
        return

    parent = settings.default_programs_page or \
             settings.site.root_page
    if not parent:
        return

    page = models.ProgramPage(
        program = instance,
        title = instance.name,
        live = False,
        # Translators: default content of a page for program
        body = _('{program.name} is a program on {station.name}.').format(
            program = instance,
            station = instance.station
        )
    )
    parent.add_child(instance = page)


@receiver(pre_delete, sender=aircox.Program)
def program_post_deleted(sender, instance, *args, **kwargs):
    for page in instance.page.all():
        if page.specific.body or Page.objects.descendant_of(page).count():
            continue
        page.delete()


@receiver(post_save, sender=aircox.Diffusion)
def diffusion_post_saved(sender, instance, created, *args, **kwargs):
    if not created or instance.page.count():
        return

    page = models.DiffusionPage.from_diffusion(
        instance, live = False
    )
    instance.program.page.first().add_child(
        instance = page
    )

@receiver(pre_delete, sender=aircox.Program)
def diffusion_post_deleted(sender, instance, *args, **kwargs):
    for page in instance.page.all():
        if page.specific.body or Page.objects.descendant_of(page).count():
            continue
        page.delete()


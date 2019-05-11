import inspect

from django.urls import reverse
from wagtail.core.models import Page

def image_url(image, filter_spec):
    """
    Return an url for the given image -- shortcut function for
    wagtailimages' serve.
    """
    from wagtail.images.views.serve import generate_signature
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    url += image.file.name[len('original_images/'):]
    return url

def get_station_settings(station):
    """
    Get WebsiteSettings for the given station.
    """
    import aircox_cms.models as models
    return models.WebsiteSettings.objects \
                 .filter(station = station).first()

def get_station_site(station):
    """
    Get the site of the given station.
    """
    settings = get_station_settings(station)
    return settings and settings.site

def related_pages_filter(reset_cache=False):
    """
    Return a dict that can be used to filter foreignkey to pages'
    subtype declared in aircox_cms.models.

    This value is stored in cache, but it is possible to reset the
    cache using the `reset_cache` parameter.
    """
    import aircox_cms.models as cms

    if not reset_cache and hasattr(related_pages_filter, 'cache'):
        return related_pages_filter.cache
    related_pages_filter.cache = {
        'model__in': list(name.lower() for name, member in
            inspect.getmembers(cms,
                lambda x: inspect.isclass(x) and issubclass(x, Page)
            )
            if member != Page
        ),
    }
    return related_pages_filter.cache




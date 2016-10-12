
from django.core.urlresolvers import reverse
from wagtail.wagtailimages.utils import generate_signature


def image_url(image, filter_spec):
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    url += image.file.name[len('original_images/'):]
    return url

def get_station_settings(station):
    import aircox_cms.models as models
    return models.WebsiteSettings.objects \
                 .filter(station = station).first()

def get_station_site(station):
    settings = get_station_settings(station)
    return settings and settings.site



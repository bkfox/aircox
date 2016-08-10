
from django.core.urlresolvers import reverse
from wagtail.wagtailimages.utils import generate_signature

def image_url(image, filter_spec):
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    url += image.file.name[len('original_images/'):]
    return url


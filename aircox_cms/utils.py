from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse


def get_url (website, route, model, kwargs):
    name = website.name_of_model(model)
    if not name:
        return
    name = route.get_view_name(name)
    return reverse(name, kwargs = kwargs)


def filter_thread (qs, object):
    model_type = ContentType.objects.get_for_model(object.__class__)
    return qs.filter(
        thread_pk = object.pk,
        thread_type__pk = model_type.pk
    )




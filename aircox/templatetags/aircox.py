import random

from django import template

from aircox.models import Page, Diffusion, Log

random.seed()
register = template.Library()


@register.filter(name='verbose_name')
def do_verbose_name(obj, plural=False):
    """ Return model's verbose name (singular or plural) """
    return obj._meta.verbose_name_plural if plural else \
           obj._meta.verbose_name

@register.simple_tag(name='update_query')
def do_update_query(obj, **kwargs):
    """ Replace provided querydict's values with **kwargs. """
    for k, v in kwargs.items():
        if v is not None:
            obj[k] = list(v) if hasattr(v, '__iter__') else [v]
        elif k in obj:
            obj.pop(k)
    return obj


@register.filter(name='is_diffusion')
def do_is_diffusion(obj):
    return isinstance(obj, Diffusion)


@register.filter(name='get_tracks')
def do_get_tracks(obj):
    """ Get a list of track for the provided log, diffusion, or episode """
    if isinstance(obj, Log):
        return (obj.track,)

    if isinstance(obj, Diffusion):
        obj = obj.episode
    return obj.track_set.all()


@register.simple_tag(name='nav_items', takes_context=True)
def do_nav_items(context, menu, **kwargs):
    station, request = context['station'], context['request']
    return [(item, item.render(request, **kwargs))
            for item in station.navitem_set.filter(menu=menu)]


# FIXME: used?
@register.simple_tag(name='unique_id')
def do_unique_id(prefix=''):
    value = str(random.random()).replace('.', '')
    return prefix + '_' + value if prefix else value





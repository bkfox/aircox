import random

from django import template

from aircox.models import Page, Diffusion

random.seed()
register = template.Library()


@register.simple_tag(name='unique_id')
def do_unique_id(prefix=''):
    value = str(random.random()).replace('.', '')
    return prefix + '_' + value if prefix else value


@register.filter(name='is_diffusion')
def do_is_diffusion(obj):
    return isinstance(obj, Diffusion)


@register.simple_tag(name='nav_items', takes_context=True)
def do_nav_items(context, menu, **kwargs):
    station, request = context['station'], context['request']
    return [(item, item.render(request, **kwargs))
            for item in station.navitem_set.filter(menu=menu)]



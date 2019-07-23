import random

from django import template

from aircox import models as aircox
from aircox_web.models import Page

random.seed()
register = template.Library()


@register.simple_tag(name='diffusion_page')
def do_diffusion_page(diffusion):
    """ Return page for diffusion. """
    diff = diffusion.initial if diffusion.initial is not None else diffusion
    for obj in (diff, diffusion.program):
        page = getattr(obj, 'page', None)
        if page is not None and page.status == Page.STATUS.published:
            return page


@register.simple_tag(name='unique_id')
def do_unique_id(prefix=''):
    value = str(random.random()).replace('.', '')
    return prefix + '_' + value if prefix else value


@register.filter(name='is_diffusion')
def do_is_diffusion(obj):
    return isinstance(obj, aircox.Diffusion)



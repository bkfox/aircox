import random

from django import template

from aircox.models import Page, 
from aircox_web.models import Page

random.seed()
register = template.Library()


@register.simple_tag(name='diffusion_page')
def do_diffusion_page(diffusion):
    """ Return page for diffusion. """
    episode = diffusion.episode
    if episode.is_publihed:
        return diff.episode
    program = episode.program
    return program if program.is_published else None


@register.simple_tag(name='unique_id')
def do_unique_id(prefix=''):
    value = str(random.random()).replace('.', '')
    return prefix + '_' + value if prefix else value


@register.filter(name='is_diffusion')
def do_is_diffusion(obj):
    return isinstance(obj, aircox.Diffusion)



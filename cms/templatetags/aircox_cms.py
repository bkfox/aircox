from django import template
from django.db.models import Q

import aircox.cms.sections as sections

register = template.Library()

@register.filter
def around(page_num, n):
    """
    Return a range of value around a given number.
    """
    return range(page_num-n, page_num+n+1)

@register.simple_tag(takes_context=True)
def render_section(position = None, section = None, context = None):
    """
    If section is not given, render all sections at the given
    position (filter out base on page models' too, cf. Section.model).
    """
    request = context.get('request')
    page = context.get('page')

    if section:
        return section.render(request, page=page)

    sections = Section.objects \
        .filter( Q(model__isnull = True) | Q(model = type(page)) ) \
        .filter(position = position)
    return '\n'.join(
        section.render(request, page=page) for section in sections
    )


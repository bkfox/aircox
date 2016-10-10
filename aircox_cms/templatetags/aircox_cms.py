from django import template
from django.utils.safestring import mark_safe

from aircox_cms.sections import Section

register = template.Library()

@register.filter
def around(page_num, n):
    """
    Return a range of value around a given number.
    """
    return range(page_num-n, page_num+n+1)

@register.simple_tag(takes_context=True)
def render_sections(context, position = None):
    """
    Render all sections at the given position (filter out base on page
    models' too, cf. Section.model).
    """
    request = context.get('request')
    page = context.get('page')
    return mark_safe(''.join(
        section.render(request, page=page, context = {
            'settings': context.get('settings')
        })
        for section in Section.get_sections_at(position, page)
    ))


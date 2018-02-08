import random

from django import template
from django.utils.safestring import mark_safe

from aircox_cms.models.sections import Region

register = template.Library()


@register.filter
def gen_id(prefix, sep = "-"):
    """
    Generate a random element id
    """
    return sep.join([
        prefix,
        str(random.random())[2:],
        str(random.random())[2:],
    ])

@register.filter
def concat(a,b):
    """
    Concat two strings together
    """
    return str(a) + str(b)

@register.filter
def around(page_num, n):
    """
    Return a range of value around a given number.
    """
    return range(page_num-n, page_num+n+1)


@register.simple_tag(takes_context=True)
def render_section(context, section, **kwargs):
    """
    Render a section from the current page. By default retrieve required
    information from the context
    """
    return mark_safe(section.render(
        context = context.flatten(),
        request = context['request'],
        page = context['page'],
        **kwargs
    ))

@register.simple_tag(takes_context=True)
def render_sections(context, position = None):
    """
    Render all sections at the given position (filter out base on page
    models' too, cf. Region.model).
    """
    request = context.get('request')
    page = context.get('page')
    return mark_safe(''.join(
        section.render(request, page=page, context = {
            'settings': context.get('settings')
        })
        for section in Region.get_sections_at(position, page)
    ))

@register.simple_tag(takes_context=True)
def render_template_mixin(context, mixin):
    """
    Render correctly a template mixin, e.g SectionLink
    """
    request = context.get('request')
    page = context.get('page')
    return mark_safe(mixin.render(request, page=page, context = {
        'settings': context.get('settings')
    }))



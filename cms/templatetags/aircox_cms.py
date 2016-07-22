from django import template
register = template.Library()

@register.filter(name='around')
def around(page_num, n):
    """
    Return a range of value around a given number.
    """
    return range(page_num-n, page_num+n+1)



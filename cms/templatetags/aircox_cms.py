from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.filter(name='threads')
def threads(post, sep = '/'):
    """
    print a list of all parents, from top to bottom
    """
    posts = [post]
    while posts[0].thread:
        post = posts[0].thread
        if post not in posts:
            posts.insert(0, post)

    return sep.join([
        '<a href="{}">{}</a>'.format(post.detail_url(), post.title)
        for post in posts if post.published
    ])

@register.filter(name='around')
def around(page_num, n):
    return range(page_num-n, page_num+n+1)



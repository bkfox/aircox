from django import template
from django.core.urlresolvers import reverse

import aircox.cms.utils as utils

register = template.Library()

@register.filter(name='downcast')
def downcast(post):
    """
    Downcast an object if it has a downcast function, or just return the
    post.
    """
    if hasattr(post, 'downcast') and callable(post.downcast):
        return post.downcast
    return post


@register.filter(name='post_tags')
def post_tags(post, sep = ' - '):
    """
    return the result of post.tags_url
    """
    return utils.tags_to_html(type(post), post.tags.all(), sep)


@register.filter(name='threads')
def threads(post, sep = '/'):
    """
    print the list of all the parents of the given post, from top to bottom
    """
    posts = [post]
    while posts[0].thread:
        post = posts[0].thread
        if post not in posts:
            posts.insert(0, post)

    return sep.join([
        '<a href="{}">{}</a>'.format(post.url(), post.title)
        for post in posts[:-1] if post.published
    ])

@register.filter(name='around')
def around(page_num, n):
    return range(page_num-n, page_num+n+1)



from django import template
from django.core.urlresolvers import reverse

import aircox.cms.routes as routes


register = template.Library()

@register.filter(name='post_tags')
def post_tags(post, sep = '-'):
    """
    print the list of all the tags of the given post, with url if available
    """
    tags = post.tags.all()
    r = []
    for tag in tags:
        try:
            r.append('<a href="{url}">{name}</a>'.format(
                url = post.route_url(routes.TagsRoute, tags = tag),
                name = tag,
            ))
        except:
            r.push(tag)
    return sep.join(r)


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
        for post in posts if post.published
    ])

@register.filter(name='around')
def around(page_num, n):
    return range(page_num-n, page_num+n+1)



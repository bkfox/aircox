import aircox.cms.routes as routes

def tags_to_html(model, tags, sep = ', '):
    """
    Render tags as string of HTML urls. `self` can be a class, but in
    this case, it `tags` must be provided.

    tags must be an iterator on taggit's Tag models (or similar)

    """
    website = model._website
    r = []
    for tag in tags:
        url = website.reverse(model, routes.TagsRoute, tags = tag.slug)
        if url:
            r.append('<a href="{url}">{name}</a>'.format(
                url = url, name = tag.name)
            )
        else:
            r.append(tag.name)
    return sep.join(r)


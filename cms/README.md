# Aircox.CMS
Simple CMS generator used in Aircox. Main features includes:
- website configuration and templating
- articles and static pages
- sections: embeddable views used to display related elements of an object
- posts related to external models:
    - attributes binding, automatically updated
    - personalization of view rendering, using templates or sections
    - integrated admin interface if desired
- list and detail views + routing
- positioned menus using views
- comment

We aims here to automatize most common tasks and to ease website
configuration.

# Architecture
A **Website** holds all required informations to run the server instance. It
is used to register all kind of posts, routes to the views, menus, etc.

Basically, for each type of publication, the user declare the corresponding
model, the routes, the sections used for rendering, and register them using
website.register.

## Posts
**Post** is the base model for a publication. **Article** is the provided model
for articles and static pages.

**RelatedPost** is used to generate posts related to a model, the corresponding
bindings and so on. The idea is that you declare your own models using it as
parent, and give informations for bindings and so on. This is as simple as:

```python
class MyModelPost(RelatedPost):
    class Relation:
        model = MyModel
        bindings = {
            'thread': 'parent_field_name',
            'title': 'name'
        }
```

## Routes
Routes are used to generate the URLs of the website. We provide some of the
common routes: for the detail view of course, but also to select all posts or
by thread, date, search, tags.

It is of course possible to create your own routes.

Routes are registered to a router (FIXME: it might be possible that we remove
this later)


## Sections
Sections are used to render part of a publication, for example to render a
playlist related to the diffusion of a program.

If the rendering of a publication can vary depending the related element, in
most of the cases when we render elements, we can find the same patterns: a
picture, a text, a list of URLs/related posts/other items.

In order to avoid to much code writing and the multiplication of template
files (e.g. one for each type of publication), we prefer to declare these
sections and configure them. This reduce the work, keep design coherent,
and reduce the risk of bugs and so on.


## Website
This class is used to create the website itself and regroup all the needed
informations to make it beautiful. There are different steps to create the
website, using instance of the Website class:

1. Create the Website instance with all basic information: name, tags,
    description, menus and so on.
2. For each type of publication, register it using a Post model, a list of
    used sections, routes, and optional parameters. The given name is used
    for routing.
3. Register website's URLs to Django.
4. Change templates and css styles if needed.



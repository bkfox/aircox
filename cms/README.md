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

# Dependencies
* `django-taggit`: publications' tags;
* `easy_thumbnails`: publications' images and previews;
* `django-honeypot`: comments anti-spam

Note: this application can be used outside aircox if needed.

# Architecture
A **Website** holds all required informations to run the server instance. It
is used to register all kind of posts, routes to the views, menus, etc.

Basically, for each type of publication, the user declare the corresponding
model, the routes, the views used to render it, using `website.register`.


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

Note: it is possible to assign a function as a bounded value; in such case, the
function will be called using arguments **(post, related_object)**.

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

It also offers various facilities, such as comments view registering.


# Rendering
## Views
They are three kind of views, among which two are used to render related content (`PostListView`, `PostDetailView`), and one is used to set arbitrary content at given url pattern (`PageView`).

The `PostDetailView` and `PageView` use a list of sections to render their content. While `PostDetailView` is related to a model instance, `PageView` just render its sections.

`PostListView` uses the route that have been matched in order to render the list. Internally, it uses `sections.List` to render the list, if no section is given by the user. The context used to render the page is initialized using the list's rendering context.

## Sections
A Section behave similar to a view with few differences:
* it renders its content to a string, using the function `render`;
* the method `as_view` return an instance of the section rather than a function, in order to keep possible to access section's data;

## Menus
`Menu` is a section containing others sections, and are used to render the website's menus. By default they are the ones of the parent website, but it is also possible to change the menus per view.

It is possible to render only the content of a view without any menu, by adding the parameter `embed` in the request's url. This has been done in order to allow XMLHttpRequests proper.

## Lists
Lists in `PostListView` and as a section in another view always uses the **list.html** template. It extends another template, that is configurable using `base_template` template argument; this has been used to render the list either in a section or as a page.

It is also possible to specify a list of fields that are rendered in the list, at the list initialisation or using request parameter `fields` (in this case it must be a subset of the list.fields).


# Rendered content
## Templates
There are two base template that are extended by the others:
* **section.html**: used to render a single section;
* **website.html**: website page layout;

These both define the following blocks, with their related container (declared *inside* the block):
* *title*: the optional title in a `<h1>` tag;
* *header*: the optional header in a `<header>` tag;
* *content*: the content itself; for *section* there is not related container, for *website* container is declared *outside* as an element of class `.content`;
* *footer*: the footer in a `<footer>` tag;

The other templates Aircox.cms uses are:
* **details.html**: used to render post details (extends *website.html*);
* **list.html**: used to render lists, extends the given template `base_template` (*section.html* or *website.html*);
* **comments.html**: used to render comments including a form (*list.html*)


# CSS classes
* **.meta**: metadata of any item (author, date, info, tags...)
* **.info**: used to render extra information, usually in lists

The following classes are used for sections (on the section container) and page-wide views (on the <main> tag):
* **.section**: associated to all sections
* **.section_*class***: associated to all section, where name is the name of the classe used to generate the section;
* **.list**: for lists (sections and general list)
* **.detail**: for the detail page view



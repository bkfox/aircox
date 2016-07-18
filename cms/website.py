from collections import namedtuple

from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.conf.urls import include, url

import aircox.cms.routes as routes
import aircox.cms.routes as routes_
import aircox.cms.views as views
import aircox.cms.models as models
import aircox.cms.sections as sections
import aircox.cms.sections as sections_


class Website:
    """
    Describe a website and all its settings that are used for its rendering.
    """
    ## metadata
    name = ''
    domain = ''
    description = 'An aircox website'
    tags = 'aircox,radio,music'

    ## rendering
    styles = ''
    """extra css style file"""
    menus = None
    """dict of default menus used to render website pages"""

    ## user interaction
    allow_comments = True
    """allow comments on the website"""
    auto_publish_comments = False
    """publish comment without human approval"""
    comments_routes = True
    """register list routes for the Comment model"""

    ## components
    Registration = namedtuple('Registration',
        'name model routes default'
    )

    urls = []
    """list of urls generated thourgh registrations"""
    exposures = []
    """list of registered exposures (done through sections registration)"""
    registry = {}
    """dict of registered models by their name"""

    def __init__(self, menus = None, **kwargs):
        """
        * menus: a list of menus to add to the website
        """
        self.registry = {}
        self.exposures = []
        self.urls = [ url(r'^exps/', include(self.exposures)) ]
        self.menus = {}
        self.__dict__.update(kwargs)

        if menus:
            for menu in menus:
                self.set_menu(menu)

        if self.comments_routes:
            self.register_comments()

    def register_model(self, name, model, default):
        """
        Register a model and update model's fields with few data:
        - _website: back ref to self
        - _registration: ref to the registration object

        Raise a ValueError if another model is yet associated under this name.
        """
        if name in self.registry:
            reg = self.registry[name]
            if reg.model is model:
                return reg
            raise ValueError('A model has yet been registered under "{}"'
                             .format(reg.model, name))

        reg = self.Registration(name, model, [], default)
        self.registry[name] = reg
        model._registration = reg
        model._website = self
        return reg

    def register_exposures(self, sections):
        """
        Register exposures that are used in the given sections.
        """
        if not hasattr(sections, '__iter__'):
            sections = [sections]

        for section in sections:
            if not hasattr(section, '_exposure'):
                continue
            self.exposures += section._exposure.gather(section, website = self)
            section.website = self

    def __route_to_url(self, name, route, view, sections, kwargs):
        # route can be a tuple
        if type(route) in (tuple,list):
            route, view = route
            view = view.as_view(
                website = self, **kwargs
            )

        # route can be a route or a string
        if type(route) == type and issubclass(route, routes_.Route):
            return route.as_url(name, view)

        return url(
            slugify(name) if not route else str(route),
            view = view, name = name, kwargs = kwargs
        )

    def add_page(self, name, routes = [], view = views.PageView,
                 sections = None, default = False, **kwargs):
        """
        Add a view and declare it on the given routes.

        * routes: list of routes or patterns, or tuple (route/pattern, view)
            to force a view to be used;
        * view: view to use by default to render the page;
        * sections: sections to display on the view;
        * default: use this as a default view;
        * kwargs: extra kwargs to pass to the view;

        If view is a section, generate a PageView with this section as
        child. Note: the kwargs are passed to the PageView constructor.
        """
        if view and issubclass(type(view), sections_.Section):
            sections, view = view, views.PageView

        if not kwargs.get('menus'):
            kwargs['menus'] = self.menus
        if sections:
            self.register_exposures(sections)

        view = view.as_view(website = self, sections = sections, **kwargs)

        if not hasattr(routes, '__iter__'):
            routes = [routes]

        self.urls += [
            self.__route_to_url(name, route, view, sections, kwargs)
            for route in routes
        ]

    def add_model(self, name, model, sections = None, routes = None,
                  default = False,
                  list_view = views.PostListView,
                  detail_view = views.PostDetailView,
                  **kwargs):
        """
        Add a model to the Website, register it and declare its routes.

        * model: model to register
        * sections: sections to display in the *detail* view;
        * routes: routes to use for the *list* view -- cf. add_page.routes;
        * default: use as default route;
        * list_view: use it as view for lists;
        * detail_view: use it as view for details;
        * kwargs: extra kwargs arguments to pass to the view;
        """
        # register the model and the routes
        reg = self.register_model(name, model, default)
        reg.routes.extend([
            route[0] if type(route) in (list,tuple) else route
            for route in routes
        ])
        reg.routes.append(routes_.DetailRoute)

        kwargs['model'] = model
        if sections:
            self.add_page(name, view = detail_view, sections = sections,
                          routes = routes_.DetailRoute, default = default,
                          **kwargs)
        if routes:
            self.add_page(name, view = list_view, routes = routes,
                          default = default, **kwargs)

    def register_comments(self):
        """
        Register routes for comments, for the moment, only
        ThreadRoute.

        Just a wrapper around `register`.
        """
        self.add_model(
            'comment',
            model = models.Comment,
            routes = [routes.ThreadRoute],
            css_class = 'comments',
            list = sections.Comments
        )

    def set_menu(self, menu):
        """
        Set a menu, and remove any previous menu at the same position.
        Also update the menu's tag depending on its position, in order
        to have a semantic HTML5 on the web 2.0 (lol).
        """
        if menu.position in ('footer','header'):
            menu.tag = menu.position
        elif menu.position in ('left', 'right'):
            menu.tag = 'side'
        self.menus[menu.position] = menu
        self.register_exposures(menu.sections)

    def find_default(self, route):
        """
        Return a registration that can be used as default for the
        given route.
        """
        for r in self.registry.values():
            if r.default and route in r.routes:
                return r

    def reverse(self, model, route, use_default = True, **kwargs):
        """
        Reverse a url using the given model and route. If the reverse does
        not function and use_default is True, use a model that have been
        registered as a default view and that have the given road.

        If no model is given reverse with default.
        """
        if model and route in model._registration.routes:
            try:
                name = route.make_view_name(model._registration.name)
                return reverse(name, kwargs = kwargs)
            except:
                pass

        if model and not use_default:
            return ''

        for r in self.registry.values():
            if r.default and route in r.routes:
                try:
                    name = route.make_view_name(r.name)
                    return reverse(name, kwargs = kwargs)
                except:
                    pass
        return ''



from collections import namedtuple

from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.conf.urls import include, url

import aircox.cms.routes as routes
import aircox.cms.routes as routes_
import aircox.cms.views as views
import aircox.cms.models as models
import aircox.cms.sections as sections


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
        'name model routes as_default'
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

    def register_model(self, name, model, as_default):
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
                             .format(name))

        reg = self.Registration(name, model, [], as_default)
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
            self.exposures += section._exposure.gather(section)

    def register(self, name, routes = [], view = views.PageView,
                 model = None, sections = None,
                 as_default = False, **view_kwargs):
        """
        Register a view using given name and routes. If model is given,
        register the views for it.

        * name is used to register the routes as urls and the model if given
        * routes: can be a path or a route used to generate urls for the view.
            Can be a one item or a list of items.
        * view: route that is registered for the given routes
        * model: model being registrated. If given, register it in the website
            under the given name, and make it available to the view.
        * as_default: make the view available as a default view.
        """
        if type(routes) not in (tuple, list):
            routes = [ routes ]

        # model registration
        if model:
            reg = self.register_model(name, model, as_default)
            reg.routes.extend(routes)
            view_kwargs['model'] = model

        # init view
        if not view_kwargs.get('menus'):
            view_kwargs['menus'] = self.menus

        if sections:
            self.register_exposures(sections)
            view_kwargs['sections'] = sections

        view = view.as_view(
            website = self,
            **view_kwargs
        )

        # url gen
        self.urls += [
            route.as_url(name, view)
                if type(route) == type and issubclass(route, routes_.Route)
                else url(slugify(name) if not route else route,
                         view = view, name = name)
            for route in routes
        ]

    def register_dl(self, name, model, sections = None, routes = None,
                    list_view = views.PostListView,
                    detail_view = views.PostDetailView,
                    list_kwargs = {}, detail_kwargs = {},
                    as_default = False):
        """
        Register a detail and list view for a given model, using
        routes.

        Just a wrapper around `register`.
        """
        if sections:
            self.register(name, [ routes_.DetailRoute ], view = detail_view,
                          model = model, sections = sections,
                          as_default = as_default,
                          **detail_kwargs)
        if routes:
            self.register(name, routes, view = list_view,
                          model = model, as_default = as_default,
                          **list_kwargs)

    def register_comments(self):
        """
        Register routes for comments, for the moment, only
        ThreadRoute.

        Just a wrapper around `register`.
        """
        self.register(
            'comment',
            view = views.PostListView,
            routes = [routes.ThreadRoute],
            model = models.Comment,
            css_class = 'comments',
            list = sections.Comments(
                truncate = 30,
                fields = ['content','author','date','time'],
            )
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
            if r.as_default and route in r.routes:
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
            if r.as_default and route in r.routes:
                try:
                    name = route.make_view_name(r.name)
                    return reverse(name, kwargs = kwargs)
                except:
                    pass
        return ''



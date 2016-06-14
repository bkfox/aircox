from django.utils.text import slugify
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
    urls = []
    """list of urls generated thourgh registrations"""
    parts = []
    """list of registered parts (done through sections registration)"""
    registry = {}
    """dict of registered models by their name"""

    def __init__(self, menus = None, **kwargs):
        """
        * menus: a list of menus to add to the website
        """
        self.registry = {}
        self.parts = []
        self.urls = [ url(r'^parts/', include(self.parts)) ]
        self.menus = {}
        self.__dict__.update(kwargs)

        if menus:
            for menu in menus:
                self.set_menu(menu)

        if self.comments_routes:
            self.register_comments()

    def name_of_model(self, model):
        """
        Return the registered name for a given model if found.
        """
        for name, _model in self.registry.items():
            if model is _model:
                return name

    def register_comments(self):
        """
        Register routes for comments, for the moment, only
        ThreadRoute
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

    def __register_model(self, name, model):
        """
        Register a model and return the name under which it is registered.
        Raise a ValueError if another model is yet associated under this name.
        """
        if name in self.registry:
            if self.registry[name] is model:
                return name
            raise ValueError('A model has yet been registered under "{}"'
                             .format(name))
        self.registry[name] = model
        model._website = self
        return name

    def register_parts(self, sections):
        """
        Register parts that are used in the given sections.
        """
        if not hasattr(sections, '__iter__'):
            sections = [sections]

        for section in sections:
            if not hasattr(section, '_parts'):
                continue
            self.parts += [
                url for url in section._parts
                if url not in self.urls
            ]

    def register(self, name, routes = [], view = views.PageView,
                 model = None, sections = None, **view_kwargs):
        """
        Register a view using given name and routes. If model is given,
        register the views for it.

        * name is used to register the routes as urls and the model if given
        * routes: can be a path or a route used to generate urls for the view.
            Can be a one item or a list of items.
        """
        if model:
            name = self.__register_model(name, model)
            view_kwargs['model'] = model

        if not view_kwargs.get('menus'):
            view_kwargs['menus'] = self.menus

        if sections:
            self.register_parts(sections)
            view_kwargs['sections'] = sections

        view = view.as_view(
            website = self,
            **view_kwargs
        )

        if type(routes) not in (tuple, list):
            routes = [ routes ]

        self.urls += [
            route.as_url(name, view)
                if type(route) == type and issubclass(route, routes_.Route)
                else url(slugify(name) if not route else route,
                         view = view, name = name)
            for route in routes
        ]

    def register_post(self, name, model, sections = None, routes = None,
                      list_view = views.PostListView,
                      detail_view = views.PostDetailView,
                      list_kwargs = {}, detail_kwargs = {}):
        """
        Register a detail and list view for a given model, using
        routes. Just a wrapper around register.
        """
        if sections:
            self.register(name, [ routes_.DetailRoute ], view = detail_view,
                          model = model, sections = sections, **detail_kwargs)
        if routes:
            self.register(name, routes, view = list_view,
                          model = model, **list_kwargs)

    def set_menu(self, menu):
        """
        Set a menu, and remove any previous menu at the same position
        """
        if menu.position in ('footer','header'):
            menu.tag = menu.position
        elif menu.position in ('left', 'right'):
            menu.tag = 'side'
        self.menus[menu.position] = menu
        self.register_parts(menu.sections)

    def get_menu(self, position):
        """
        Get an enabled menu by its position
        """
        return self.menus.get(position)



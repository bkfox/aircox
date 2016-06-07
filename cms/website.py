from django.utils.text import slugify
from django.conf.urls import url

import aircox.cms.routes as routes
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
    registry = {}
    """dict of registered models by their name"""

    def __init__(self, menus = None, **kwargs):
        """
        * menus: a list of menus to add to the website
        """
        self.registry = {}
        self.urls = []
        self.menus = {}
        self.__dict__.update(kwargs)

        if menus:
            for menu in menus:
                self.set_menu(menu)

        if self.comments_routes:
            self.register_comments_routes()


    def name_of_model(self, model):
        """
        Return the registered name for a given model if found.
        """
        for name, _model in self.registry.items():
            if model is _model:
                return name

    def register_comments_routes(self):
        """
        Register routes for comments, for the moment, only
        ThreadRoute
        """
        self.register_list(
            'comment', models.Comment,
            routes = [routes.ThreadRoute],
            css_class = 'comments',
            list = sections.Comments(
                truncate = 30,
                fields = ['content','author','date','time'],
            )
        )

    def register_model(self, name, model):
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

    def register_detail(self, name, model, view = views.PostDetailView,
                         **view_kwargs):
        """
        Register a model and the detail view
        """
        name = self.register_model(name, model)
        if not view_kwargs.get('menus'):
            view_kwargs['menus'] = self.menus

        view = view.as_view(
            website = self,
            model = model,
            **view_kwargs
        )

        self.urls.append(routes.DetailRoute.as_url(name, view))
        self.registry[name] = model

    def register_list(self, name, model, view = views.PostListView,
                       routes = [], **view_kwargs):
        """
        Register a model and the given list view using the given routes
        """
        name = self.register_model(name, model)
        if not 'menus' in view_kwargs:
            view_kwargs['menus'] = self.menus

        view = view.as_view(
            website = self,
            model = model,
            **view_kwargs
        )

        self.urls += [ route.as_url(name, view) for route in routes ]
        self.registry[name] = model

    def register_page(self, name, view = views.PageView, path = None,
                      **view_kwargs):
        """
        Register a page that is accessible to the given path. If path is None,
        use a slug of the name.
        """
        if not 'menus' in view_kwargs:
            view_kwargs['menus'] = self.menus

        view = view.as_view(
            website = self,
            **view_kwargs
        )
        self.urls.append(url(
            slugify(name) if path is None else path,
            view = view,
            name = name,
        ))

    def register(self, name, model, sections = None, routes = None,
                  list_view = views.PostListView,
                  detail_view = views.PostDetailView,
                  list_kwargs = {}, detail_kwargs = {}):
        """
        Register a detail and list view for a given model, using
        routes. Just a wrapper around register_detail and
        register_list.
        """
        if sections:
            self.register_detail(
                name, model,
                sections = sections,
                **detail_kwargs
            )
        if routes:
            self.register_list(
                name, model,
                routes = routes,
                **list_kwargs
            )

    def set_menu(self, menu):
        """
        Set a menu, and remove any previous menu at the same position
        """
        if menu.position in ('footer','header'):
            menu.tag = menu.position
        elif menu.position in ('left', 'right'):
            menu.tag = 'side'
        self.menus[menu.position] = menu

    def get_menu(self, position):
        """
        Get an enabled menu by its position
        """
        return self.menus.get(position)



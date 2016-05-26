import aircox.cms.routes as routes
import aircox.cms.views as views

class Website:
    """
    Describe a website and all its settings that are used for its rendering.
    """
    # metadata
    name = ''
    domain = ''
    description = 'An aircox website'
    tags = 'aircox,radio,music'

    # rendering
    styles = ''
    menus = None

    # user interaction
    allow_comments = True
    auto_publish_comments = False

    # components
    urls = []
    registry = {}

    def __init__ (self, menus = None, **kwargs):
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


    def name_of_model (self, model):
        for name, _model in self.registry.items():
            if model is _model:
                return name

    def register_model (self, name, model):
        """
        Register a model and return the name under which it is registered.
        Raise a ValueError if another model is yet associated under this name.
        """
        if name in self.registry and self.registry[name] is not model:
            raise ValueError('A model has yet been registered under "{}"'
                             .format(name))
        self.registry[name] = model
        model._website = self
        return name

    def register_detail (self, name, model, view = views.PostDetailView,
                         **view_kwargs):
        """
        Register a model and the detail view
        """
        name = self.register_model(name, model)
        view = view.as_view(
            website = self,
            model = model,
            **view_kwargs
        )
        self.urls.append(routes.DetailRoute.as_url(name, view))
        self.registry[name] = model

    def register_list (self, name, model, view = views.PostListView,
                       routes = [], **view_kwargs):
        """
        Register a model and the given list view using the given routes
        """
        name = self.register_model(name, model)
        view = view.as_view(
            website = self,
            model = model,
            **view_kwargs
        )
        self.urls += [ route.as_url(name, view) for route in routes ]
        self.registry[name] = model

    def register (self, name, model, sections = None, routes = None,
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

    def set_menu (self, menu):
        """
        Set a menu, and remove any previous menu at the same position
        """
        if menu.position in ('footer','header'):
            menu.tag = menu.position
        elif menu.position in ('left', 'right'):
            menu.tag = 'side'
        self.menus[menu.position] = menu

    def get_menu (self, position):
        """
        Get an enabled menu by its position
        """
        return self.menus.get(position)



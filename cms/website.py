import aircox.cms.routes as routes
import aircox.cms.views as views

class Website:
    name = ''
    domain = ''
    description = 'An aircox website'   # public description (used in meta info)
    tags = 'aircox,radio,music'         # public keywords (used in meta info)

    styles = ''                         # relative url to stylesheet file
    menus = None                        # list of menus
    menu_layouts = ['top', 'left',      # available positions
                    'right', 'bottom',
                    'header', 'footer']
    router = None
    urls = []
    registry = {}

    def __init__ (self, **kwargs):
        self.registry = {}
        self.urls = []
        self.__dict__.update(kwargs)

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
            **view_kwargs,
        )
        self.urls.append(routes.DetailRoute.as_url(name, model, view))
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
        self.urls += [ route.as_url(name, model, view) for route in routes ]
        self.registry[name] = model

    def register (self, name, model, sections = None, routes = None,
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

    def get_menu (self, position):
        """
        Get an enabled menu by its position
        """
        for menu in self.menus:
            if menu.enabled and menu.position == position:
                self.check_menu_tag(menu)
                return menu

    def check_menu_tag (self, menu):
        """
        Update menu tag if it is a footer or a header
        """
        if menu.position in ('footer','header'):
            menu.tag = menu.position
        if menu.position in ('left', 'right'):
            menu.tag = 'side'



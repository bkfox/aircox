import aircox_cms.routes as routes

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

    @property
    def urls (self):
        return self.router.get_urlpatterns()

    def __init__ (self, **kwargs):
        self.__dict__.update(kwargs)
        if not self.router:
            self.router = routes.Router()

    def register_set (self, view_set):
        """
        Register a ViewSet (or subclass) to the router,
        and connect it to self.
        """
        view_set = view_set(website = self)
        self.router.register_set(view_set)

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



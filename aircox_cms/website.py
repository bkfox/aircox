import aircox_cms.routes as routes

class Website:
    name = ''
    domain = ''
    description = 'An aircox website'   # public description (used in meta info)
    tags = 'aircox,radio,music'         # public keywords (used in meta info)

    logo = None
    menus = None
    router = None

    def __init__ (self, **kwargs):
        self.__dict__.update(kwargs)
        if not self.router:
            self.router = routes.Router()

    def register_set (self, view_set):
        view_set = view_set(website = self)
        self.router.register_set(view_set)

    def get_menu (self, position):
        for menu in self.menus:
            if menu.enabled and menu.position == position:
                return menu

    def get_top_menu (self):
        return self.get_menu('top')

    def get_left_menu (self):
        return self.get_menu('left')

    def get_bottom_menu (self):
        return self.get_menu('bottom')

    def get_right_menu (self):
        return self.get_menu('right')

    @property
    def urls (self):
        return self.router.get_urlpatterns()



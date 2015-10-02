import cms.routes as routes

class Website:
    name = ''
    logo = None
    menus = None
    router = None

    def __init__ (self, **kwargs):
        self.__dict__.update(kwargs)
        if not self.router:
            self.router = routes.Router()
        if not self.sets:
            self.sets = []

    def register_set (self, view_set):
        view_set = view_set(website = self)
        self.router.register_set(view_set)

    @property
    def urls (self):
        return self.router.get_urlpatterns()



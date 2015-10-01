from django.conf.urls import url
from django.utils import timezone

from website.models import *
from website.views import *

class Router:
    registry = []

    def register (self, route):
        if not route in self.registry:
            self.registry.append(route)

    def register_set (self, view_set):
        for route in view_set.routes:
            self.register(route)

    def unregister (self, route):
        self.registry.remove(route)

    def get_urlpatterns (self):
        return [ route.get_url() for route in self.registry ]


class Route:
    """
    Base class for routing. Given a model, we generate url specific for each
    route type. The generated url takes this form:
        base_name + '/' + route_name + '/' + '/'.join(route_url_args)

    Where base_name by default is the given model's verbose_name (uses plural if
    Route is for a list).

    The given view is considered as a django class view, and has view_
    """
    model = None        # model routed here
    view = None         # view class to call
    view_kwargs  = None   # arguments passed to view at creation of the urls

    class Meta:
        name = None         # route name
        is_list = False     # route is for a list
        url_args = []       # arguments passed from the url [ (name : regex),... ]

    def __init__ (self, model, view, view_kwargs = None):
        self.model = model
        self.view = view
        self.view_kwargs = view_kwargs
        self.embed = False

        _meta = {}
        _meta.update(Route.Meta.__dict__)
        _meta.update(self.Meta.__dict__)
        self._meta = _meta

        self.base_name = model._meta.verbose_name_plural.lower()

    def get_queryset (self, request, **kwargs):
        """
        Called by the view to get the queryset when it is needed
        """
        pass

    def get (self, request, **kwargs):
        """
        Called by the view to get the object when it is needed
        """
        pass

    def get_url (self):
        pattern = '^{}/{}'.format(self.base_name, self.Meta.name)
        if self._meta['url_args']:
            url_args = '/'.join([
                '(?P<{}>{}){}'.format(
                    arg, expr,
                    (optional and optional[0] and '?') or ''
                )
                for arg, expr, *optional in self._meta['url_args']
            ])
            pattern += '/' + url_args
        pattern += '/?$'

        kwargs = {
            'route': self,
        }
        if self.view_kwargs:
            kwargs.update(self.view_kwargs)

        return url(pattern, self.view, kwargs = kwargs,
                   name = self.base_name + '_' + self.Meta.name)


class DetailRoute (Route):
    class Meta:
        name = 'detail'
        is_list = False
        url_args = [
            ('pk', '[0-9]+'),
            ('slug', '(\w|-|_)+', True),
        ]

    def get (self, request, **kwargs):
        return self.model.objects.get(pk = int(kwargs['pk']))


class AllRoute (Route):
    class Meta:
        name = 'all'
        is_list = True

    def get_queryset (self, request, **kwargs):
        return self.model.objects.all()


class ThreadRoute (Route):
    class Meta:
        name = 'thread'
        is_list = True
        url_args = [
            ('pk', '[0-9]+'),
        ]

    def get_queryset (self, request, **kwargs):
        return self.model.objects.filter(thread__pk = int(kwargs['pk']))


class DateRoute (Route):
    class Meta:
        name = 'date'
        is_list = True
        url_args = [
            ('year', '[0-9]{4}'),
            ('month', '[0-9]{2}'),
            ('day', '[0-9]{1,2}'),
        ]

    def get_queryset (self, request, **kwargs):
        return self.model.objects.filter(
            date__year = int(kwargs['year']),
            date__month = int(kwargs['month']),
            date__day = int(kwargs['day']),
        )


class SearchRoute (Route):
    class Meta:
        name = 'search'
        is_list = True

    def get_queryset (self, request, **kwargs):
        q = request.GET.get('q') or ''
        qs = self.model.objects
        for search_field in model.search_fields or []:
            r = self.model.objects.filter(**{ search_field + '__icontains': q })
            if qs: qs = qs | r
            else: qs = r

        qs.distinct()
        return qs




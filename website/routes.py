from django.conf.urls import url
from django.utils import timezone

from website.models import *

class Routes:
    registry = []

    def register (self, route):
        if not route in self.registry:
            self.registry.append(route)

    def unregister (self, route):
        self.registry.remove(route)

    def get_urlpatterns (self):
        patterns = []
        for route in self.registry:
            patterns += route.get_urlpatterns() or []
        return patterns


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

    def __init__ (self, model, view, view_kwargs = None,
                  base_name = None):
        self.model = model
        self.view = view
        self.view_kwargs = view_kwargs
        self.embed = False

        _meta = {}
        _meta.update(Route.Meta.__dict__)
        _meta.update(self.Meta.__dict__)
        self._meta = _meta

        if not base_name:
            base_name = model._meta.verbose_name_plural if _meta['is_list'] \
                    else model._meta.verbose_name
            base_name = base_name.title().lower()
        self.base_name = base_name

    def get_queryset (self, request, **kwargs):
        """
        Called by the view to get the queryset when it is needed
        """

    def get_urlpatterns (self):
        view_kwargs = self.view_kwargs or {}

        pattern = '^{}/{}'.format(self.base_name, self.Meta.name)

        if self.view.Meta.formats:
            pattern += '(/(?P<format>{}))?'.format('|'.join(self.view.Meta.formats))

        if self._meta['url_args']:
            url_args = '/'.join([ '(?P<{}>{})'.format(arg, expr) \
                                    for arg, expr in self._meta['url_args']
                                ])
            pattern += '/' + url_args
        pattern += '/?$'

        return [ url(
            pattern,
            self.view and self.view.as_view(
                route = self,
                model = self.model,
                **view_kwargs
            ),
            name = '{}'
        ) ]


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


class ThreadRoute (Route):
    class Meta:
        name = 'thread'
        is_list = True
        url_args = [
            ('pk', '[0-9]+')
        ]

    def get_queryset (self, request, **kwargs):
        return self.model.objects.filter(thread__id = int(kwargs['pk']))


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




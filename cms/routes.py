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
        for url in view_set.urls:
            self.register(url)

    def unregister (self, route):
        self.registry.remove(route)

    def get_urlpatterns (self):
        return [ url for url in self.registry ]


class Route:
    """
    Base class for routing. Given a model, we generate url specific for each
    route type. The generated url takes this form:
        base_name + '/' + route_name + '/' + '/'.join(route_url_args)

    Where base_name by default is the given model's verbose_name (uses plural if
    Route is for a list).

    The given view is considered as a django class view, and has view_
    """
    name = None         # route name
    url_args = []       # arguments passed from the url [ (name : regex),... ]

    @classmethod
    def get_queryset (cl, model, request, **kwargs):
        """
        Called by the view to get the queryset when it is needed
        """
        pass

    @classmethod
    def get_object (cl, model, request, **kwargs):
        """
        Called by the view to get the object when it is needed
        """
        pass


    @classmethod
    def get_title (cl, model, request, **kwargs):
        return ''


    @classmethod
    def as_url (cl, model, view, view_kwargs = None):
        base_name = model._meta.verbose_name_plural.lower()

        pattern = '^{}/{}'.format(base_name, cl.name)
        if cl.url_args:
            url_args = '/'.join([
                '(?P<{}>{}){}'.format(
                    arg, expr,
                    (optional and optional[0] and '?') or ''
                )
                for arg, expr, *optional in cl.url_args
            ])
            pattern += '/' + url_args
        pattern += '/?$'

        kwargs = {
            'route': cl,
        }
        if view_kwargs:
            kwargs.update(view_kwargs)

        return url(pattern, view, kwargs = kwargs,
                   name = base_name + '_' + cl.name)


class DetailRoute (Route):
    name = 'detail'
    url_args = [
        ('pk', '[0-9]+'),
        ('slug', '(\w|-|_)+', True),
    ]


    @classmethod
    def get_object (cl, model, request, pk, **kwargs):
        return model.objects.get(pk = int(pk))


class AllRoute (Route):
    name = 'all'

    @classmethod
    def get_queryset (cl, model, request, **kwargs):
        return model.objects.all()


class ThreadRoute (Route):
    name = 'thread'
    url_args = [
        ('pk', '[0-9]+'),
    ]

    @classmethod
    def get_queryset (cl, model, request, pk, **kwargs):
        return model.objects.filter(thread__pk = int(pk))


class DateRoute (Route):
    name = 'date'
    url_args = [
        ('year', '[0-9]{4}'),
        ('month', '[0-9]{2}'),
        ('day', '[0-9]{1,2}'),
    ]

    @classmethod
    def get_queryset (cl, model, request, year, month, day, **kwargs):
        return model.objects.filter(
            date__year = int(year),
            date__month = int(month),
            date__day = int(day),
        )


class SearchRoute (Route):
    name = 'search'

    @classmethod
    def get_queryset (cl, model, request, **kwargs):
        q = request.GET.get('q') or ''
        qs = model.objects
        for search_field in model.search_fields or []:
            r = model.objects.filter(**{ search_field + '__icontains': q })
            if qs: qs = qs | r
            else: qs = r

        qs.distinct()
        return qs




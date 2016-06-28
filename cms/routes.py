from django.db import models
from django.utils import timezone as tz
from django.conf.urls import url
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.cms.qcombine as qcombine


class Route:
    """
    Base class for routing. Given a model, we generate url specific for each
    type of route.

    The generated url takes this form:
        name + '/' + route_name + '/' + '/'.join(route_url_args)

    And their name (to use for reverse:
        name + '_' + route_name

    By default name is the verbose name of the model. It is always in
    singular form.
    """
    name = None         # route name
    url_args = []       # arguments passed from the url [ (name : regex),... ]

    @classmethod
    def get_queryset(cl, model, request, **kwargs):
        """
        Called by the view to get the queryset when it is needed
        """
        pass

    @classmethod
    def get_object(cl, model, request, **kwargs):
        """
        Called by the view to get the object when it is needed
        """
        pass

    @classmethod
    def get_title(cl, model, request, **kwargs):
        return ''

    @classmethod
    def make_view_name(cl, name):
        return name + '.' + cl.name

    @classmethod
    def as_url(cl, name, view, view_kwargs = None):
        pattern = '^{}/{}'.format(name, cl.name)
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
                   name = cl.make_view_name(name))


class DetailRoute(Route):
    name = 'detail'
    url_args = [
        ('pk', '[0-9]+'),
        ('slug', '(\w|-|_)+', True),
    ]

    @classmethod
    def get_object(cl, model, request, pk, **kwargs):
        return model.objects.get(pk = int(pk))


class AllRoute(Route):
    name = 'all'

    @classmethod
    def get_queryset(cl, model, request, **kwargs):
        return model.objects.all()

    @classmethod
    def get_title(cl, model, request, **kwargs):
        return _('All %(model)s') % {
            'model': model._meta.verbose_name_plural
        }


class ThreadRoute(Route):
    """
    Select posts using by their assigned thread.

    - "thread_model" can be a string with the name of a registered item on
    website or a model.
    - "pk" is the pk of the thread item.
    """
    name = 'thread'
    url_args = [
        ('thread_model', '(\w|_|-)+'),
        ('pk', '[0-9]+'),
    ]

    @classmethod
    def get_thread(cl, model, thread_model, pk=None):
        """
        Return a model if not pk, otherwise the model element of given id
        """
        if type(thread_model) is str:
            thread_model = model._website.registry.get(thread_model)
        if not thread_model or not pk:
            return thread_model
        return thread_model.objects.get(pk=pk)


    @classmethod
    def get_queryset(cl, model, request, thread_model, pk, **kwargs):
        thread = cl.get_thread(model, thread_model, pk)
        return model.get_siblings(thread_model = thread, thread_id = pk)

    @classmethod
    def get_title(cl, model, request, thread_model, pk, **kwargs):
        thread = cl.get_thread(model, thread_model, pk)
        return '<a href="{url}">{title}</a>'.format(
            url = thread.url(),
            title = _('%(name)s: %(model)s') % {
                'model': model._meta.verbose_name_plural,
                'name': thread.title,
            }
        )


class DateRoute(Route):
    """
    Select posts using a date with format yyyy/mm/dd;
    """
    name = 'date'
    url_args = [
        ('year', '[0-9]{4}'),
        ('month', '[0-1]?[0-9]'),
        ('day', '[0-3]?[0-9]'),
    ]

    @classmethod
    def get_queryset(cl, model, request, year, month, day, **kwargs):
        return model.objects.filter(
            date__year = int(year),
            date__month = int(month),
            date__day = int(day),
        )

    @classmethod
    def get_title(cl, model, request, year, month, day, **kwargs):
        date = tz.datetime(year = int(year), month = int(month), day = int(day))
        return _('%(model)s of %(date)s') % {
            'model': model._meta.verbose_name_plural,
            'date': date.strftime('%A %d %B %Y'),
        }


class SearchRoute(Route):
    """
    Search post using request.GET['q']. It searches in fields designated by
    model.search_fields
    """
    # TODO: q argument in url_args -> need to allow optional url_args
    name = 'search'

    @classmethod
    def __search(cl, model, q):
        qs = None
        for search_field in model.search_fields or []:
            r = models.Q(**{ search_field + '__icontains': q })
            if qs: qs = qs | r
            else: qs = r
        return model.objects.filter(qs).distinct()


    @classmethod
    def get_queryset(cl, model, request, **kwargs):
        q = request.GET.get('q') or ''
        if issubclass(model, qcombine.GenericModel):
            models = model.models
            return qcombine.QCombine(
                *(cl.__search(model, q) for model in models)
            )
        return cl.__search(model, q)

    @classmethod
    def get_title(cl, model, request, **kwargs):
        return _('Search <i>%(search)s</i> in %(model)s') % {
            'model': model._meta.verbose_name_plural,
            'search': request.GET.get('q') or '',
        }


class TagsRoute(Route):
    """
    Select posts that contains the given tags. The tags are separated
    by a '+'.
    """
    name = 'tags'
    url_args = [
        ('tags', '(\w|-|_|\+)+')
    ]

    @classmethod
    def get_queryset(cl, model, request, tags, **kwargs):
        tags = tags.split('+')
        return model.objects.filter(tags__slug__in=tags).distinct()

    @classmethod
    def get_title(cl, model, request, tags, **kwargs):
        # FIXME: get tag name instead of tag slug
        return _('%(model)s tagged with %(tags)s') % {
            'model': model._meta.verbose_name_plural,
            'tags': model.tags_to_html(model, tags = tags.split('+'))
                    if '+' in tags else tags
        }


import datetime

from django.db import models
from django.utils import timezone as tz
from django.conf.urls import url
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _, ugettext_lazy

from taggit.models import Tag


class Route:
    """
    Base class for routing. Given a model, we generate url specific for each
    type of route.

    The generated url takes this form:
        name + '/' + route_name + '/' + '/'.join(params)

    And their name (to use for reverse:
        name + '_' + route_name

    By default name is the verbose name of the model. It is always in
    singular form.
    """
    name = None
    """
    Regular name of the route
    """
    params = []
    """
    Arguments passed by the url, it is a list of tupple with values:
    - name: (required) name of the argument
    - regex: (required) regular expression to append to the url
    - optional: (not required) if true, argument is optional
    """

    @classmethod
    def get_queryset(cl, website, request, **kwargs):
        """
        Called by the view to get the queryset when it is needed
        """
        pass

    @classmethod
    def get_object(cl, website, request, **kwargs):
        """
        Called by the view to get the object when it is needed
        """
        pass

    @classmethod
    def get_title(cl, website, request, **kwargs):
        return ''

    @classmethod
    def make_view_name(cl, name):
        return name + '.' + cl.name

    @classmethod
    def make_pattern(cl, prefix = ''):
        """
        Make a url pattern using prefix as prefix and cl.params as
        parameters.
        """
        pattern = prefix
        if cl.params:
            pattern += ''.join([
                '{pre}/(?P<{name}>{regexp}){post}'.format(
                    name = name, regexp = regexp,
                    pre = (optional and optional[0] and '(?:') or '',
                    post = (optional and optional[0] and ')?') or '',
                )
                for name, regexp, *optional in cl.params
            ])
        pattern += '/?$'
        return pattern

    @classmethod
    def as_url(cl, name, view, kwargs = None):
        pattern = cl.make_pattern('^{}/{}'.format(name, cl.name))
        kwargs = kwargs.copy() if kwargs else {}
        kwargs['route'] = cl
        return url(pattern, view, kwargs = kwargs,
                   name = cl.make_view_name(name))


class DetailRoute(Route):
    name = 'detail'
    params = [
        ('pk', '[0-9]+'),
        ('slug', '(\w|-|_)+', True),
    ]

    @classmethod
    def get_object(cl, model, request, pk, **kwargs):
        """
        * request: optional
        """
        return model.objects.get(pk = int(pk))


class AllRoute(Route):
    """
    Retrieve all element of the given model.
    """
    name = 'all'

    @classmethod
    def get_queryset(cl, model, request, **kwargs):
        """
        * request: optional
        """
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
    params = [
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
        """
        * request: optional
        """
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
    params = [
        ('year', '[0-9]{4}'),
        ('month', '[0-1]?[0-9]'),
        ('day', '[0-3]?[0-9]'),
    ]

    @classmethod
    def get_queryset(cl, model, request, year, month, day, **kwargs):
        """
        * request: optional
        * attr: name of the attribute to check the date against
        """
        date = datetime.date(int(year), int(month), int(day))
        return model.objects.filter(date__contains = date)

    @classmethod
    def get_title(cl, model, request, year, month, day, **kwargs):
        date = tz.datetime(year = int(year), month = int(month), day = int(day))
        return _('%(model)s of %(date)s') % {
            'model': model._meta.verbose_name_plural,
            'date': date.strftime('%A %d %B %Y'),
        }


class SearchRoute(Route):
    """
    Search post using request.GET['q'] or q optional argument. It searches in
    fields designated by model.search_fields
    """
    name = 'search'
    params = [
        ( 'q', '[^/]+', True)
    ]

    @classmethod
    def get_queryset(cl, model, request, q = None, **kwargs):
        """
        * request: required if q is None
        """
        q = request.GET.get('q') or q or ''
        qs = None
        for search_field in model.search_fields or []:
            r = models.Q(**{ search_field + '__icontains': q })
            if qs: qs = qs | r
            else: qs = r
        return model.objects.filter(qs).distinct()

    @classmethod
    def get_title(cl, model, request, q = None, **kwargs):
        return _('Search <i>%(search)s</i> in %(model)s') % {
            'model': model._meta.verbose_name_plural,
            'search': request.GET.get('q') or q or '',
        }


class TagsRoute(Route):
    """
    Select posts that contains the given tags. The tags are separated
    by a '+'.
    """
    name = 'tags'
    params = [
        ('tags', '(\w|-|_|\+)+')
    ]

    @classmethod
    def get_queryset(cl, model, request, tags, **kwargs):
        tags = tags.split('+')
        return model.objects.filter(tags__slug__in=tags).distinct()

    @classmethod
    def get_title(cl, model, request, tags, **kwargs):
        import aircox.cms.utils as utils
        tags = Tag.objects.filter(slug__in = tags.split('+'))

        # FIXME: get tag name instead of tag slug
        return _('%(model)s tagged with %(tags)s') % {
            'model': model._meta.verbose_name_plural,
            'tags': utils.tags_to_html(model, tags = tags)
        }


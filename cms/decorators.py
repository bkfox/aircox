from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.text import slugify


def template(name):
    """
    the decorated function returns a context that is used to
    render a template value.

    * template_name: name of the template to use
    * hide_empty: an empty context returns an empty string
    """
    def template_(func):
        def wrapper(request, *args, **kwargs):
            if kwargs.get('cl'):
                context = func(kwargs.pop('cl'), request, *args, **kwargs)
            else:
                context = func(request, *args, **kwargs)
            if not context:
                return ''
            context['embed'] = True
            return render_to_string(name, context, request=request)
        return wrapper
    return template_


class Exposure:
    """
    Define an exposure. Look at @expose decorator.
    """
    name = None
    """generated view name"""
    pattern = None
    """url pattern"""
    items = None
    """for classes: list of url objects for exposed methods"""
    template_name = None
    """
    for methods: exposed method return a context to be use with
    the given template. The view will be wrapped in @template
    """
    item = None
    """
    exposed item
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def url(self, *args, **kwargs):
        """
        reverse url for this exposure
        """
        return reverse(self.name, *args, **kwargs)

    def prefix(self, parent):
        """
        prefix exposure with the given parent
        """
        self.name = parent.name + '.' + self.name
        self.pattern = parent.pattern + '/' + self.pattern


def expose(item):
    """
    Expose a class and its methods as views. This allows data to be
    retrieved dynamiccaly from client (e.g. with javascript).

    To expose a method of a class, you must expose the class, then the
    method.

    The exposed method has the following signature:

        `func(cl, request, parent, *args, **kwargs) -> str`

    Data related to the exposure are put in the `_exposure` attribute,
    as instance of Exposure.

    To add extra parameter, such as template_name, just update the correct
    field in func._exposure, that will be taken in account at the class
    decoration.

    The exposed method will be prefix'ed with it's parent class exposure.

    When adding views to a website, the exposure of their sections are
    added to the list of url.
    """
    def get_attr(attr, default):
        v = (hasattr(item, attr) and getattr(item, attr)) or default
        return slugify(v.lower())

    name = get_attr('name', item.__name__)
    pattern = get_attr('pattern', item.__name__)

    exp = Exposure(name = name, pattern = pattern, item = item)

    # expose a class container: set _exposure attribute
    if type(item) == type:
        exp.name = 'exp.' + exp.name
        exp.items = []

        for func in item.__dict__.values():
            if not hasattr(func, '_exposure'):
                continue

            sub = func._exposure
            sub.prefix(exp)

            # FIXME: template warping lose args
            if sub.template_name:
                sub.item = template(sub.template_name)(sub.item)

            func = url(sub.pattern, name = sub.name,
                       view = func, kwargs = {'cl': item})
            exp.items.append(func)

        item._exposure = exp;
        return item
    # expose a method: wrap it
    else:
        if hasattr(item, '_exposure'):
            del item._exposure

        def wrapper(request, as_str = False, *args, **kwargs):
            v = exp.item(request, *args, **kwargs)
            if as_str:
                return v
            return HttpResponse(v)
        wrapper._exposure = exp;
        return wrapper



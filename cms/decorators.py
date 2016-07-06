import inspect

from django.template.loader import render_to_string
from django.http import HttpResponse, Http404
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.text import slugify


class Exposure:
    """
    Define an exposure. Look at @expose decorator.
    """
    name = None
    """generated view name"""
    pattern = None
    """url pattern"""
    template_name = None
    """
    for methods: exposed method return a context to be use with
    the given template. The view will be wrapped in @template
    """
    item = None
    """
    Back ref to the exposed item, can be used to detect inheritance of
    exposed classes.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def gather(cl):
        """
        Prepare all exposure declared in self.cl, create urls and return
        them. This is done at this place in order to allow sub-classing
        of exposed classes.
        """
        def view(request, key, *args, fn = None, **kwargs):
            if not fn:
                if not hasattr(cl, key):
                    raise Http404()

                fn = getattr(cl, key)
                if not hasattr(fn, '_exposure'):
                    raise Http404()

            exp = fn._exposure
            res = fn(request, *args, **kwargs)
            if res and exp.template_name:
                ctx = res or {}
                ctx.update({
                    'embed': True,
                    'exp': cl._exposure,
                })
                res = render_to_string(exp.template_name,
                                       ctx, request = request)
            return HttpResponse(res or '')

        # id = str(uuid.uuid1())
        exp = cl._exposure
        exp.pattern = '{name}/{id}'.format(name = exp.name, id = id(cl))
        exp.name = 'exps.{name}.{id}'.format(name = exp.name, id = id(cl))

        urls = []

        for name, fn in inspect.getmembers(cl):
            if name.startswith('__') or not hasattr(fn, '_exposure'):
                continue
            fn_exp = fn._exposure
            if not fn_exp.pattern:
                continue

            name = fn_exp.name or name
            pattern = exp.pattern + '/(?P<key>{name})/{pattern}'.format(
                name = name, pattern = fn_exp.pattern
            )

            urls.append(url(
                pattern, name = exp.name, view = view,
                kwargs = { 'fn': fn }
            ))

        urls.append(url(
            exp.pattern + '(?P<key>\w+)', name = exp.name, view = view
        ))
        return urls


def expose(item):
    """
    Expose a class and its methods as views. This allows data to be
    retrieved dynamiccaly from client (e.g. with javascript).

    To expose a method of a class, you must expose the class, then the
    method.

    The exposed method has the following signature:

        `func(cl, request, *args, **kwargs) -> str`

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
    item._exposure = exp;
    return item


from django.template.loader import render_to_string
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.text import slugify


def __part_normalize(value, default):
    value = value if value else default
    return slugify(value.lower())


def parts(cls, name = None, pattern = None):
    """
    the decorated class is a parts class, and contains part
    functions. Look `part` decorator doc for more info.
    """
    name = __part_normalize(name, cls.__name__)
    pattern = __part_normalize(pattern, cls.__name__)

    cls._parts = []
    for part in cls.__dict__.values():
        if not hasattr(part, 'is_part'):
            continue

        part.name = name + '_' + part.name
        part.pattern = pattern + '/' + part.pattern
        part = url(part.pattern, name = part.name,
                   view = part, kwargs = {'cl': cls})
        cls._parts.append(part)
    return cls


def part(view, name = None, pattern = None):
    """
    A part function is a view that is used to retrieve data dynamically,
    e.g. from Javascript with XMLHttpRequest. A part function is a classmethod
    that returns a string and has the following signature:

        `part(cl, request, parent, *args, **kwargs)`

    When a section with parts is added to the website, the parts' urls
    are added to the website's one and make them available.

    A part function can have the following parameters:
    * name: part.name or part.__name__
    * pattern: part.pattern or part.__name__

    An extra method `url` is added to the part function to return the adequate
    url.

    Theses are combined with the containing parts class params such as:
    * name: parts.name + '_' + part.name
    * pattern: parts.pattern + '/' + part.pattern

    The parts class will have an attribute '_parts' as list of generated
    urls.
    """
    if hasattr(view, 'is_part'):
        return view

    def view_(request, as_str = False, cl = None, *args, **kwargs):
        v = view(cl, request, *args, **kwargs)
        if as_str:
            return v
        return HttpResponse(v)

    def url(*args, **kwargs):
        return reverse(view_.name, *args, **kwargs)

    view_.name = __part_normalize(name, view.__name__)
    view_.pattern = __part_normalize(pattern, view.__name__)
    view_.is_part = True
    view_.url = url
    return view_

def template(template_name):
    """
    the decorated function returns a context that is used to
    render a template value.

    * template_name: name of the template to use
    * hide_empty: an empty context returns an empty string
    """
    def wrapper(func):
        def view_(cl, request, *args, **kwargs):
            context = func(cl, request, *args, **kwargs)
            if not context and hide_empty:
                return ''
            context['embed'] = True
            return render_to_string(template_name, context, request=request)
        view_.__name__ = func.__name__
        return view_
    return wrapper




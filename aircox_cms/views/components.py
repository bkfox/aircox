import json

from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.core.utils import camelcase_to_underscore


class Component:
    """
    A Component is a small part of a rendered web page. It can be used
    to create elements configurable by users.
    """
    template_name = ""
    """
    [class] Template file path
    """
    hide = False
    """
    The component can be hidden because there is no reason to display it
    (e.g. empty list)
    """

    @classmethod
    def snake_name(cl):
        if not hasattr(cl, '_snake_name'):
            cl._snake_name = camelcase_to_underscore(cl.__name__)
        return cl._snake_name

    def get_context(self, request, page):
        """
        Context attributes:
        * self: section being rendered
        * page: current page being rendered
        * request: request used to render the current page

        Other context attributes usable in the default section template:
        * content: **safe string** set as content of the section
        * hide: DO NOT render the section, render only an empty string
        """
        return {
            'self': self,
            'page': page,
            'request': request,
        }

    def render(self, request, page, context, *args, **kwargs):
        """
        Render the component. ``Page`` is the current page being
        rendered.
        """
        # use a different object
        context_ = self.get_context(request, *args, page=page, **kwargs)
        if self.hide:
            return ''

        if context:
            context_.update({
                k: v for k, v in context.items()
                if k not in context_
            })

        context_['page'] = page
        return render_to_string(self.template_name, context_)


class ExposedData:
    """
    Data object that aims to be exposed to Javascript. This provides
    various utilities.
    """
    model = None
    """
    [class attribute] Related model/class object that is to be exposed
    """
    fields = {}
    """
    [class attribute] Fields of the model to be exposed, as a dict of
        ``{ exposed_field: model_field }``

    ``model_field`` can either be a function(exposed, object) or a field
    name.
    """
    data = None
    """
    Exposed data of the instance
    """

    def __init__(self, object = None, **kwargs):
        self.data = {}
        if object:
            self.from_object(object)
        self.data.update(kwargs)

    def from_object(self, object):
        fields = type(self).fields
        for k,v in fields.items():
            if self.data.get(k) != None:
                continue
            v = v(self, object) if callable(v) else \
                getattr(object, v) if hasattr(object, v) else \
                None
            self.data[k] = v

    def to_json(self):
        """
        Return a json string of encoded data.
        """
        return mark_safe(json.dumps(self.data))


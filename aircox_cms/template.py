from django.db import models
from django.template.loader import render_to_string
from wagtail.wagtailcore.utils import camelcase_to_underscore


class TemplateMixin(models.Model):
    class Meta:
        abstract = True

    template_name = None
    """
    Template to use for the mixin. If not given, use
    "app_label/sections/section_class.html"
    """
    snake_name = None
    """
    Used in template as class
    """

    @classmethod
    def get_template_name(cl):
        if not cl.template_name:
            cl.snake_name = camelcase_to_underscore(cl.__name__)
            cl.template_name = '{}/sections/{}.html'.format(
                cl._meta.app_label, cl.snake_name
            )

            if cl.snake_name != 'section_item':
                from django.template import TemplateDoesNotExist
                try:
                    from django.template.loader import get_template
                    get_template(cl.template_name)
                except TemplateDoesNotExist:
                    cl.template = 'aircox_cms/sections/section_item.html'
        return cl.template_name

    def get_context(self, request, page):
        """
        Default context attributes:
        * self: section being rendered
        * page: current page being rendered
        * request: request used to render the current page

        Other context attributes usable in the default template:
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
        Render the section. Page is the current publication being rendered.

        Rendering is similar to pages, using 'template' attribute set
        by default to the app_label/sections/model_name_snake_case.html

        If the default template is not found, use SectionItem's one,
        that can have a context attribute 'content' that is used to render
        content.
        """
        context_ = self.get_context(request, *args, page=page, **kwargs)
        if context:
            context_.update(context)

        if context_.get('hide'):
            return ''
        return render_to_string(self.get_template_name(), context_)



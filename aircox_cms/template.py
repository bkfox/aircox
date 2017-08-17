from django.db import models
from django.template.loader import render_to_string
from wagtail.wagtailcore.utils import camelcase_to_underscore


class TemplateMixinMeta(models.base.ModelBase):
    """
    Metaclass for SectionItem, assigning needed values such as `template`.

    It needs to load the item's template if the section uses the default
    one, and throw error if there is an error in the template.
    """
    def __new__(cls, name, bases, attrs):
        from django.template import TemplateDoesNotExist

        cl = super().__new__(cls, name, bases, attrs)
        if not hasattr(cl, '_meta'):
            return cl

        if not 'template' in attrs:
            cl.snake_name = camelcase_to_underscore(name)
            cl.template = '{}/sections/{}.html'.format(
                cl._meta.app_label,
                cl.snake_name,
            )
            if name != 'SectionItem':
                try:
                    from django.template.loader import get_template
                    get_template(cl.template)
                except (TemplateDoesNotExist, InvalidTemplateLirary) as e:
                    cl.template = 'aircox_cms/sections/section_item.html'
                    print('TemplateMixin error:', e)
        return cl


class TemplateMixin(models.Model,metaclass=TemplateMixinMeta):
    class Meta:
        abstract = True

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
        return render_to_string(self.template, context_)



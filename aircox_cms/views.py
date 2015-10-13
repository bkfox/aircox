import re

from django.templatetags.static import static
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from django.views.generic.base import View, TemplateResponseMixin
from django.core.paginator import Paginator
from django.core import serializers
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.html import escape

import aircox_cms.routes as routes
import aircox_cms.utils as utils


class PostBaseView:
    website = None  # corresponding website
    title = ''      # title of the page
    embed = False   # page is embed (if True, only post content is printed
    classes = ''    # extra classes for the content

    def get_base_context (self, **kwargs):
        """
        Return a context with all attributes of this classe plus 'view' set
        to self.
        """
        context = {
            k: getattr(self, k)
            for k, v in PostBaseView.__dict__.items()
                if not k.startswith('__')
        }

        if not self.embed:
            context['menus'] = {
                k: v.get(self.request, website = self.website, **kwargs)
                for k, v in {
                    k: self.website.get_menu(k)
                    for k in self.website.menu_layouts
                }.items() if v
            }

        context['view'] = self
        return context


class PostListView (PostBaseView, ListView):
    """
    List view for posts and children
    """
    class Query:
        """
        Request availables parameters
        """
        embed = False
        exclude = None
        order = 'desc'
        reverse = False
        fields = None
        page = 1

        def __init__ (self, query):
            if query:
                self.update(query)

        def update (self, query):
            my_class = self.__class__
            if type(query) is my_class:
                self.__dict__.update(query.__dict__)
                return
            self.__dict__.update(query)

    template_name = 'aircox_cms/list.html'
    allow_empty = True
    paginate_by = 50
    model = None

    route = None
    query = None
    fields = [ 'date', 'time', 'image', 'title', 'content' ]
    icon_size = '64x64'

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = PostListView.Query(self.query)

    def dispatch (self, request, *args, **kwargs):
        self.route = self.kwargs.get('route') or self.route
        return super().dispatch(request, *args, **kwargs)

    def get_queryset (self):
        if self.route:
            qs = self.route.get_queryset(self.website, self.model, self.request,
                                         **self.kwargs)
        else:
            qs = self.queryset or self.model.objects.all()
        query = self.query

        query.update(self.request.GET)
        if query.exclude:
            qs = qs.exclude(id = int(exclude))

        if query.embed:
            self.embed = True

        if query.order == 'asc':
            qs.order_by('date', 'id')
        else:
            qs.order_by('-date', '-id')

        if query.fields:
            self.fields = [
                field for field in query.fields
                if field in self.__class__.fields
            ]

        return qs

    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context())
        context.update({
            'title': self.get_title(),
        })
        return context

    def get_title (self):
        if self.title:
            return self.title

        title = self.route and self.route.get_title(self.model, self.request,
                                                    **self.kwargs)
        return title

    def get_url (self):
        if self.route:
            return utils.get_urls(self.website, self.route,
                                  self.model, self.kwargs)
        return ''


class PostDetailView (DetailView, PostBaseView):
    """
    Detail view for posts and children
    """
    template_name = 'aircox_cms/detail.html'

    sections = []

    def __init__ (self, sections = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = sections or []

    def get_queryset (self):
        if self.request.GET.get('embed'):
            self.embed = True

        if self.model:
            return super().get_queryset().filter(published = True)
        return []

    def get_object (self, **kwargs):
        if self.model:
            object = super().get_object(**kwargs)
            if object.published:
                return object
        return None

    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context())
        context.update({
            'sections': [
                section.get(self.request, website = self.website, **kwargs)
                    for section in self.sections
            ]
        })
        return context


class Menu (View):
    template_name = 'aircox_cms/menu.html'

    name = ''
    tag = 'nav'
    enabled = True
    classes = ''
    position = ''   # top, left, bottom, right, header, footer, page_top, page_bottom
    sections = None

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = self.name or ('menu_' + self.position)

    def get_context_data (self, **kwargs):
        return {
            'name': self.name,
            'tag': self.tag,
            'classes': self.classes,
            'position': self.position,
            'sections': [
                section.get(self.request, website = self.website,
                            object = None, **kwargs)
                    for section in self.sections
            ]
        }

    def get (self, request, website, **kwargs):
        self.request = request
        self.website = website
        context = self.get_context_data(**kwargs)
        return render_to_string(self.template_name, context)



class BaseSection (View):
    """
    Base class for sections. Sections are view that can be used in detail view
    in order to have extra content about a post, or in menus.
    """
    template_name = 'aircox_cms/base_section.html'
    kwargs = None   # kwargs argument passed to get
    tag = 'div'     # container tags
    classes = ''    # container classes
    attrs = ''      # container extra attributes
    content = ''    # content
    visible = True  # if false renders an empty string


    def get_context_data (self):
        return {
            'view': self,
            'tag': self.tag,
            'classes': self.classes,
            'attrs': self.attrs,
            'visible': self.visible,
            'content': self.content,
        }

    def get (self, request, website, **kwargs):
        self.request = request
        self.website = website
        self.kwargs = kwargs

        context = self.get_context_data()
        # get_context_data may call extra function that can change visibility
        if self.visible:
            return render_to_string(self.template_name, context)
        return ''


class Section (BaseSection):
    """
    A Section that can be related to an object.
    """
    template_name = 'aircox_cms/section.html'
    object = None
    object_required = False
    title = ''
    header = ''
    footer = ''

    def get_context_data (self):
        context = super().get_context_data()
        context.update({
            'title': self.title,
            'header': self.header,
            'footer': self.footer,
        })
        return context

    def get (self, request, object = None, **kwargs):
        self.object = object or self.object
        if self.object_required and not self.object:
            raise ValueError('object is required by this Section but not given')

        return super().get(request, **kwargs)


class Sections:
    class Image (BaseSection):
        """
        Render an image with the given relative url.
        """
        url = None

        @property
        def content (self):
            return '<img src="{}">'.format(
                        static(self.url),
                    )

    class PostContent (Section):
        """
        Render the content of the Post (format the text a bit and escape HTML
        tags).
        """
        @property
        def content (self):
            content = escape(self.object.content)
            content = re.sub(r'(^|\n\n)((\n?[^\n])+)', r'<p>\2</p>', content)
            content = re.sub(r'\n', r'<br>', content)
            return content

    class PostImage (Section):
        """
        Render the image of the Post
        """
        @property
        def content (self):
            return '<img src="{}" class="post_image">'.format(
                        self.object.image.url
                    )

    class List (Section):
        """
        Section to render list. The context item 'object_list' is used as list of
        items to render.
        """
        class Item:
            icon = None
            title = None
            text = None
            url = None

            def __init__ (self, icon, title = None, text = None, url = None):
                self.icon = icon
                self.title = title
                self.text = text

        hide_empty = False      # hides the section if the list is empty
        use_icons = True        # print icons
        paginate_by = 0         # number of items
        icon_size = '32x32'     # icons size
        template_name = 'aircox_cms/section_list.html'

        def get_object_list (self):
            return []

        def get_context_data (self, **kwargs):
            object_list = self.get_object_list()
            self.visibility = True
            if not object_list and hide_empty:
                self.visibility = False

            context = super().get_context_data(**kwargs)
            context.update({
                'classes': context.get('classes') + ' section_list',
                'icon_size': self.icon_size,
                'object_list': object_list,
                'paginate_by': self.paginate_by,
            })
            return context

    class Urls (List):
        """
        Render a list of urls of targets that are Posts
        """
        classes = 'section_urls'
        targets = None

        def get_object_list (self):
            return [
                List.Item(
                    target.image or None,
                    target.title,
                    url = target.detail_url(),
                )
                for target in self.targets
            ]

    class Posts (PostBaseView, Section):
        """
        Render a list using PostListView's template.
        """
        embed = True
        paginate_by = 5
        icon_size = '64x64'
        fields = [ 'date', 'time', 'image', 'title', 'content' ]

        def get_url (self):
            return ''

        def get_object_list (self):
            return []

        def render_list (self):
            self.embed = True
            context = self.get_base_context(**self.kwargs)
            context.update({
                'object_list': self.get_object_list(),
                'embed': True,
                'paginate_by': self.paginate_by,
            })
            return render_to_string(PostListView.template_name, context)

        def get_context_data (self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['content'] = self.render_list()
            return context



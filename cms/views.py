from django.templatetags.static import static
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from django.views.generic.base import View, TemplateView
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib import messages
from django.http import Http404

import aircox.cms.sections as sections


class PostBaseView:
    """
    Base class for views.

    # Request GET params:
    * embed: view is embedded, render only the content of the view
    """
    website = None
    """website that uses the view"""
    menus = None
    """menus used to render the view page"""
    title = ''
    """title of the page (used in <title> tags and page <h1>)"""
    attrs = ''      # attr for the HTML element of the content
    """attributes to set in the HTML element containing the view"""
    css_class = ''  # css classes for the HTML element of the content
    """css classes used for the HTML element containing the view"""

    def add_css_class(self, css_class):
        """
        Add the given class to the current class list if not yet present.
        """
        if self.css_class:
            if css_class not in self.css_class.split(' '):
                self.css_class += ' ' + css_class
        else:
            self.css_class = css_class

    def get_base_context(self, **kwargs):
        """
        Return a context with all attributes of this classe plus 'view' set
        to self.
        """
        context = {
            key: getattr(self, key)
            for key in PostBaseView.__dict__.keys()
                if not key.startswith('__')
        }

        if 'embed' not in self.request.GET:
            object = self.object if hasattr(self, 'object') else None
            if self.menus:
                context['menus'] = {
                    k: v.render(self.request, object = object, **kwargs)
                    for k, v in self.menus.items()
                }
            context['embed'] = False
        else:
            context['embed'] = True
        context['view'] = self
        return context


class PostListView(PostBaseView, ListView):
    """
    List view for posts and children.

    If list is given:
    - use list's template and css_class
    - use list's context as base context

    Note that we never use list.get_object_list, but instead use
    route.get_queryset or self.model.objects.all()

    Request.GET params:
    * exclude: exclude item of the given id
    * order: 'desc' or 'asc'
    * page: page number
    """
    template_name = 'aircox/cms/list.html'
    allow_empty = True
    paginate_by = 30
    model = None

    route = None
    """route used to render this list"""
    list = None
    """list section to use to render the list and get base context.
    By default it is sections.List"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.route = self.kwargs.get('route') or self.route
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.route:
            qs = self.route.get_queryset(self.model, self.request,
                                         **self.kwargs)
        else:
            qs = self.queryset or self.model.objects.all()
        qs = qs.filter(published = True)

        query = self.request.GET
        if query.get('exclude'):
            qs = qs.exclude(id = int(query['exclude']))
        if query.get('order') == 'desc':
            qs = qs.order_by('-date', '-id')
        else:
            qs = qs.order_by('date', 'id')

        return qs

    def init_list(self):
        if not self.list:
           self.list = sections.List(
               truncate = 32,
               paginate_by = 0,
               fields = ['date', 'time', 'image', 'title', 'content'],
           )
        else:
            self.list = self.list(paginate_by = 0)
            self.template_name = self.list.template_name
            self.css_class = self.list.css_class

        if self.request.GET.get('fields'):
            self.list.fields = [
                field for field in self.request.GET.getlist('fields')
                if field in self.list.fields
            ]

    def get_context_data(self, **kwargs):
        self.init_list()
        self.add_css_class('list')

        context = self.list.get_context_data(self.request, **self.kwargs) or {}
        context.update(super().get_context_data(**kwargs))
        context.update(self.get_base_context(**kwargs))

        if self.title:
            title = self.title
        elif self.route:
            title = self.route.get_title(self.model, self.request,
                                         **self.kwargs)

        context.update({
            'title': title,
            'base_template': 'aircox/cms/website.html',
            'css_class': self.css_class,
            'list': self.list,
        })
        return context


class PostDetailView(DetailView, PostBaseView):
    """
    Detail view for posts and children
    """
    template_name = 'aircox/cms/detail.html'

    sections = []
    comments = None

    def __init__(self, sections = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('detail')
        self.sections = [ section() for section in (sections or []) ]

    def get_queryset(self):
        if self.model:
            return super().get_queryset().filter(published = True)
        return []

    def get_object(self, **kwargs):
        if self.model:
            object = super().get_object(**kwargs)
            if object.published:
                return object
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context())

        kwargs['object'] = self.object
        context.update({
            'title': self.title or self.object.title,
            'content': ''.join([
                section.render(request = self.request, **kwargs)
                for section in self.sections
            ]),
            'css_class': self.css_class,
        })
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle new comments
        """
        if not self.comments:
            for section in self.sections:
                if issubclass(type(section), sections.Comments):
                    self.comments = section

        self.object = self.get_object()
        self.comments.post(self, request, self.object)
        return self.get(request, *args, **kwargs)


class PageView(TemplateView, PostBaseView):
    """
    A simple page view. Used to render pages that have arbitrary content
    without linked post object.
    """
    template_name = 'aircox/cms/detail.html'

    sections = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = sections.Sections(self.sections)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context())
        context.update({
            'title': self.title,
            'content': self.sections.render(request=self.request,**kwargs)
        })
        return context




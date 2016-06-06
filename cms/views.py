from django.templatetags.static import static
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView
from django.views.generic.base import View, TemplateView
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib import messages
from django.http import Http404

import aircox.cms.sections as sections


class PostBaseView:
    website = None  # corresponding website
    title = ''      # title of the page
    embed = False   # page is embed (if True, only post content is printed
    attrs = ''      # attr for the HTML element of the content
    css_class = ''  # css classes for the HTML element of the content

    def add_css_class(self, css_class):
        if self.css_class:
            self.css_class += ' ' + css_class
        else:
            self.css_class = css_class

    def get_base_context(self, **kwargs):
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
            object = self.object if hasattr(self, 'object') else None
            context['menus'] = {
                k: v.get(self.request, object = object, **kwargs)
                for k, v in self.website.menus.items()
            }
        context['view'] = self
        return context


class PostListView(PostBaseView, ListView):
    """
    List view for posts and children.

    Request.GET params:
    * embed: view is embedded, render only the list
    * exclude: exclude item of the given id
    * order: 'desc' or 'asc'
    * page: page number
    """
    template_name = 'aircox/cms/list.html'
    allow_empty = True
    paginate_by = 30
    model = None

    route = None
    list = None
    css_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('list')

        if not self.list:
            self.list = sections.List(
                truncate = 32,
                fields = [ 'date', 'time', 'image', 'title', 'content' ],
            )
        self.template_name = self.list.template_name

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

        if query.get('embed'):
            self.embed = True

        if query.get('order') == 'asc':
            qs.order_by('date', 'id')
        else:
            qs.order_by('-date', '-id')

        if query.get('fields'):
            self.fields = [
                field for field in query.get('fields')
                if field in self.__class__.fields
            ]
        return qs

    def get_context_data(self, **kwargs):
        context = self.list.get_context(request = self.request, **self.kwargs)
        context.update(super().get_context_data(**kwargs))
        context.update(self.get_base_context(**kwargs))

        if self.title:
            title = self.title
        else:
            title = self.route and \
                    self.route.get_title(self.model, self.request,
                                         **self.kwargs)

        context.update({
            'title': title,
            'base_template': 'aircox/cms/website.html',
            'css_class': self.css_class + ' ' + context.get('css_class')
                         if self.css_class else context.get('css_class'),
            'list': self.list,
        })
        # FIXME: list.url = if self.route: self.model(self.route, self.kwargs) else ''
        return context

    def get_url(self):
        return ''


class PostDetailView(DetailView, PostBaseView):
    """
    Detail view for posts and children

    Request.GET params:
    * embed: view is embedded, only render the content
    """
    template_name = 'aircox/cms/detail.html'

    sections = []
    comments = None

    def __init__(self, sections = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('detail')
        self.sections = sections or []

    def get_queryset(self):
        if self.request.GET.get('embed'):
            self.embed = True
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
            'title': self.object.title,
            'content': ''.join([
                section.get(request = self.request, **kwargs)
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
    css_class = 'page'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_css_class('page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_base_context())

        context.update({
            'title': self.title,
            'content': ''.join([
                section.get(request = self.request, **kwargs)
                for section in self.sections
            ]),
        })
        return context




from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import ListView
from django.views.generic import DetailView
from django.core import serializers
from django.utils.translation import ugettext as _, ugettext_lazy

import cms.routes as routes


class PostListView (ListView):
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

        def __init__ (self, query):
            my_class = self.__class__
            if type(query) is my_class:
                self.__dict__.update(query.__dict__)
                return

            if type(query) is not dict:
                query = query.__dict__

            self.__dict__ = { k: v for k,v in query.items() }

    template_name = 'cms/list.html'
    allow_empty = True

    model = None
    query = None
    classes = ''
    title = ''
    embed = False
    fields = [ 'date', 'time', 'image', 'title', 'content' ]

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.query:
            self.query = Query(self.query)

    def dispatch (self, request, *args, **kwargs):
        self.route = self.kwargs.get('route')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset (self):
        qs = self.route.get_queryset(self.model, self.request, **self.kwargs)
        qs = qs.filter(public = True)

        query = self.query or PostListView.Query(self.request.GET)
        if query.exclude:
            qs = qs.exclude(id = int(exclude))

        if query.embed:
            self.embed = True

        if query.order == 'asc':
            qs.order_by('date', 'id')
        else:
            qs.order_by('-date', '-id')
        return qs

    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'list': self,
            'title': self.get_title(),
            'classes': self.classes,
        })

        return context

    def get_title (self):
        if self.title:
            return self.title

        title = self.route and self.route.get_title(self.model, self.request,
                                                    **self.kwargs)
        return title


class PostDetailView (DetailView):
    """
    Detail view for posts and children
    """
    template_name = 'cms/detail.html'
    sections = []

    def __init__ (self, sections = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = sections or []

    def get_queryset (self, **kwargs):
        if self.model:
            return super().get_queryset(**kwargs).filter(public = True)
        return []

    def get_object (self, **kwargs):
        if self.model:
            object = super().get_object(**kwargs)
            if object.public:
                return object
        return None

    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'sections': [
                section.get(self.request, object = self.object)
                    for section in self.sections
            ]
        })
        return context


class ViewSet:
    """
    A ViewSet is a class helper that groups detail and list views that can be
    used to generate views and routes given a model and a name used for the
    routing.
    """
    model = None
    list_view = PostListView
    list_routes = []

    detail_view = PostDetailView
    detail_sections = []

    def __init__ (self):
        self.detail_sections = [
            section()
                for section in self.detail_sections
        ]
        self.detail_view = self.detail_view.as_view(
            model = self.model,
            sections = self.detail_sections
        )
        self.list_view = self.list_view.as_view(
            model = self.model
        )

        self.urls = [ route.as_url(self.model, self.list_view)
                            for route in self.list_routes ] + \
                      [ routes.DetailRoute.as_url(self.model, self.detail_view ) ]



class Section (DetailView):
    """
    Base class for sections. Sections are view that can be used in detail view
    in order to have extra content about a post.
    """
    template_name = 'cms/section.html'
    classes = ''
    title = ''
    content = ''
    header = ''
    bottom = ''

    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            'header': self.header,
            'content': self.content,
            'bottom': self.bottom,
            'classes': self.classes,
        })
        return context

    def get (self, request, **kwargs):
        self.object = kwargs.get('object')
        context = self.get_context_data(**kwargs)
        return render_to_string(self.template_name, context)


class ListSection (Section):
    """
    Section to render list. The context item 'object_list' is used as list of
    items to render.
    """
    class Item:
        icon = None
        title = None
        text = None

        def __init__ (self, icon, title = None, text = None):
            self.icon = icon
            self.title = title
            self.text = text

    template_name = 'cms/section_list.html'

    def get_object_list (self):
        return []

    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] += ' section_list'
        context['object_list'] = self.get_object_list()
        return context


class PostListSection (PostListView):
    route = None
    model = None
    embed = True

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_kwargs (self, request, **kwargs):
        return kwargs

    def dispatch (self, request, *args, **kwargs):
        kwargs = self.get_kwargs(kwargs)
        # TODO: to_string
        return super().dispatch(request, *args, **kwargs)

# TODO:
# - get_title: pass object / queryset



from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import ListView
from django.views.generic import DetailView
from django.core import serializers
from django.utils.translation import ugettext as _, ugettext_lazy

from website.models import *
from website.routes import *


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

    template_name = 'website/list.html'
    allow_empty = True

    model = None
    query = None
    fields = [ 'date', 'time', 'image', 'title', 'content' ]

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.query:
            self.query = Query(self.query)

    def get_queryset (self):
        route = self.kwargs['route']
        qs = route.get_queryset(self.request, **self.kwargs)
        qs = qs.filter(public = True)

        query = self.query or PostListView.Query(self.request.GET)
        if query.exclude:
            qs = qs.exclude(id = int(exclude))

        if query.order == 'asc':
            qs.order_by('date', 'id')
        else:
            qs.order_by('-date', '-id')
        return qs


    def get_context_data (self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'list': self
        })

        return context


class PostDetailView (DetailView):
    """
    Detail view for posts and children
    """
    template_name = 'website/detail.html'
    sections = None

    def __init__ (self, sections = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                section.get(self, self.request, object = self.object)
                    for section in self.sections
            ]
        })
        return context


class Section (DetailView):
    """
    Base class for sections. Sections are view that can be used in detail view
    in order to have extra content about a post.
    """
    model = None
    template_name = 'website/section.html'
    classes = ''
    title = ''
    header = ''
    bottom = ''

    def get_context_data (self, **kwargs):
        context = super().get_context_date(**kwargs)
        context.update({
            'title': self.title,
            'header': self.header,
            'bottom': self.bottom,
            'classes': self.classes,
        })

    def get (self, request, **kwargs):
        self.object = kwargs.get('object')
        context = self.get_context_data(**kwargs)
        return render_to_string(self.template_name, context)


class ViewSet:
    """
    A ViewSet is a class helper that groups detail and list views that can be
    used to generate views and routes given a model and a name used for the
    routing.
    """
    model = None
    name = ''

    list_view = PostListView
    list_routes = []

    detail_view = PostDetailView
    detail_sections = []

    def __init__ (self):
        if not self.name:
            self.name = self.model._meta.verbose_name_plural

        self.detail_sections = [
            section.as_view(model = self.model)
                for section in self.detail_sections
        ]
        self.detail_view = self.detail_view.as_view(
            model = self.model,
            sections = self.detail_sections
        )
        self.list_view = self.list_view.as_view(
            model = self.model
        )

        self.routes = [ route(self.model, self.list_view, base_name = self.name)
                            for route in self.list_routes ] + \
                      [ DetailRoute(self.model, self.detail_view,
                                    base_name = self.name) ]



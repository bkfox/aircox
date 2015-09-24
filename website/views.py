from django.shortcuts import render
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import DetailView
from django.core import serializers
from django.utils.translation import ugettext as _, ugettext_lazy

from website.models import *


class PostListView (ListView):
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

    query = None
    fields = [ 'date', 'time', 'image', 'title', 'content' ]

    route = None
    model = None

    def __init__ (self, *args, **kwargs):
        super(PostListView, self).__init__(*args, **kwargs)
        if self.query:
            self.query = Query(self.query)

    def get_queryset (self):
        qs = self.route.get_queryset(self.request, **self.kwargs)
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
        context = super(PostListView, self).get_context_data(**kwargs)
        context.update({
            'list': self
        })

        return context




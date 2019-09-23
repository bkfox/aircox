
from django.http import Http404
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from django.urls import reverse

from ..models import Page
from ..utils import Redirect


__all__ = ['BaseView']


class BaseView(TemplateResponseMixin, ContextMixin):
    title = None
    """ Page title """
    cover = None
    """ Page cover """

    has_sidebar = True
    """ Show side navigation """
    has_filters = False
    """ Show filters nav """
    list_count = 5
    """ Item count for small lists displayed on page. """

    @property
    def station(self):
        return self.request.station

    # def get_queryset(self):
    #    return super().get_queryset().station(self.station)

    def get_sidebar_queryset(self):
        """ Return a queryset of items to render on the side nav. """
        return Page.objects.select_subclasses().published() \
                           .order_by('-pub_date')

    def get_sidebar_url(self):
        return reverse('page-list')

    def get_context_data(self, **kwargs):
        kwargs.setdefault('station', self.station)
        kwargs.setdefault('cover', self.cover)
        kwargs.setdefault('has_filters', self.has_filters)

        has_sidebar = kwargs.setdefault('has_sidebar', self.has_sidebar)
        if has_sidebar and 'sidebar_object_list' not in kwargs:
            sidebar_object_list = self.get_sidebar_queryset()
            if sidebar_object_list is not None:
                kwargs['sidebar_object_list'] = sidebar_object_list[:self.list_count]
                kwargs['sidebar_list_url'] = self.get_sidebar_url()

        if 'audio_streams' not in kwargs:
            streams = self.station.audio_streams
            streams = streams and streams.split('\n')
            kwargs['audio_streams'] = streams

        return super().get_context_data(**kwargs)


class BaseAPIView:
    @property
    def station(self):
        return self.request.station

    def get_queryset(self):
        return super().get_queryset().station(self.station)




from django.http import Http404
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin, ContextMixin

from ..utils import Redirect


__all__ = ['BaseView']


class BaseView(TemplateResponseMixin, ContextMixin):
    title = None
    """ Page title """
    cover = None
    """ Page cover """

    show_side_nav = False
    """ Show side navigation """
    list_count = 5
    """ Item count for small lists displayed on page. """

    @property
    def station(self):
        return self.request.station

    def get_queryset(self):
        return super().get_queryset().station(self.station)

    def get_side_queryset(self):
        """ Return a queryset of items to render on the side nav. """
        return None

    def get_context_data(self, side_items=None, **kwargs):
        kwargs.setdefault('station', self.station)
        kwargs.setdefault('cover', self.cover)

        show_side_nav = kwargs.setdefault('show_side_nav', self.show_side_nav)
        if show_side_nav and side_items is None:
            side_items = self.get_side_queryset()
            side_items = None if side_items is None else \
                side_items[:self.list_count]

        if not 'audio_streams' in kwargs:
            streams = self.station.audio_streams
            streams = streams and streams.split('\n')
            kwargs['audio_streams'] = streams

        return super().get_context_data(side_items=side_items, **kwargs)



from django.http import Http404
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin, ContextMixin

from ..utils import Redirect


__all__ = ['BaseView', 'PageView']


class BaseView(TemplateResponseMixin, ContextMixin):
    show_side_nav = False
    """ Show side navigation """
    title = None
    """ Page title """
    cover = None
    """ Page cover """

    @property
    def station(self):
        return self.request.station

    def get_queryset(self):
        return super().get_queryset().station(self.station)

    def get_context_data(self, **kwargs):
        kwargs.setdefault('station', self.station)
        kwargs.setdefault('cover', self.cover)
        kwargs.setdefault('show_side_nav', self.show_side_nav)

        if not 'audio_streams' in kwargs:
            streams = self.station.audio_streams
            streams = streams and streams.split('\n')
            kwargs['audio_streams'] = streams
        return super().get_context_data(**kwargs)


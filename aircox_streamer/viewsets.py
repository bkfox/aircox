from django.http import Http404
from django.utils import timezone as tz

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from aircox import controllers
from aircox.models import Station
from .serializers import *


__all__ = ['Streamers', 'BaseControllerAPIView',
           'RequestViewSet', 'StreamerViewSet', 'SourceViewSet',
           'PlaylistSourceViewSet', 'QueueSourceViewSet']


class Streamers:
    date = None
    """ next update datetime """
    streamers = None
    """ stations by station id """
    timeout = None
    """ timedelta to next update """

    def __init__(self, timeout=None):
        self.timeout = timeout or tz.timedelta(seconds=2)

    def load(self, force=False):
        # FIXME: cf. TODO in aircox.controllers about model updates
        stations = Station.objects.active()
        if self.streamers is None or force:
            self.streamers = {station.pk: controllers.Streamer(station)
                              for station in stations}
            return

        streamers = self.streamers
        self.streamers = {station.pk: controllers.Streamer(station)
                          if station.pk in streamers else streamers[station.pk]
                          for station in stations}

    def fetch(self):
        if self.streamers is None:
            self.load()

        now = tz.now()
        if self.date is not None and now < self.date:
            return

        for streamer in self.streamers.values():
            streamer.fetch()
        self.date = now + self.timeout

    def get(self, key, default=None):
        self.fetch()
        return self.streamers.get(key, default)

    def values(self):
        self.fetch()
        return self.streamers.values()

    def __getitem__(self, key):
        return self.streamers[key]


streamers = Streamers()


class BaseControllerAPIView(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    serializer = None
    streamer = None

    def get_streamer(self, pk=None):
        streamer = streamers.get(self.request.pk if pk is None else pk)
        if not streamer:
            raise Http404('station not found')
        return streamer

    def get_serializer(self, obj, **kwargs):
        return self.serializer(obj, **kwargs)

    def serialize(self, obj, **kwargs):
        serializer = self.get_serializer(obj, **kwargs)
        return serializer.data

    def dispatch(self, request, *args, **kwargs):
        self.streamer = self.get_streamer(request.station.pk)
        return super().dispatch(request, *args, **kwargs)


class RequestViewSet(BaseControllerAPIView):
    serializer = RequestSerializer


class StreamerViewSet(BaseControllerAPIView):
    serializer = StreamerSerializer

    def retrieve(self, request, pk=None):
        return self.serialize(self.streamer)

    def list(self, request):
        return self.serialize(streamers.values(), many=True)


class SourceViewSet(BaseControllerAPIView):
    serializer = SourceSerializer
    model = controllers.Source

    def get_sources(self):
        return (s for s in self.streamer.souces if isinstance(s, self.model))

    def get_source(self, pk):
        source = next((source for source in self.get_sources()
                      if source.pk == pk), None)
        if source is None:
            raise Http404('source `%s` not found' % pk)
        return source

    def retrieve(self, request, pk=None):
        source = self.get_source(pk)
        return self.serialize(source)

    def list(self, request):
        return self.serialize(self.get_sources(), many=True)

    @action(detail=True, methods=['POST'])
    def sync(self, request, pk):
        self.get_source(pk).sync()

    @action(detail=True, methods=['POST'])
    def skip(self, request, pk):
        self.get_source(pk).skip()

    @action(detail=True, methods=['POST'])
    def restart(self, request, pk):
        self.get_source(pk).restart()

    @action(detail=True, methods=['POST'])
    def seek(self, request, pk):
        count = request.POST['seek']
        self.get_source(pk).seek(count)


class PlaylistSourceViewSet(SourceViewSet):
    serializer = PlaylistSerializer
    model = controllers.PlaylistSource


class QueueSourceViewSet(SourceViewSet):
    serializer = QueueSourceSerializer
    model = controllers.QueueSource

    @action(detail=True, methods=['POST'])
    def push(self, request, pk):
        self.get_source(pk).push()



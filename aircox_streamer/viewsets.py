from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone as tz

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from aircox.models import Sound, Station
from aircox.serializers import SoundSerializer
from . import controllers
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
        return self.streamers.get(key, default)

    def values(self):
        return self.streamers.values()

    def __getitem__(self, key):
        return self.streamers[key]

    def __contains__(self, key):
        return key in self.streamers


streamers = Streamers()


class BaseControllerAPIView(viewsets.ViewSet):
    permission_classes = (IsAdminUser,)
    serializer = None
    streamer = None
    object = None

    def get_streamer(self, request, station_pk=None, **kwargs):
        streamers.fetch()
        id = int(request.station.pk if station_pk is None else station_pk)
        if id not in streamers:
            raise Http404('station not found')
        return streamers[id]

    def get_serializer(self, **kwargs):
        return self.serializer(self.object, **kwargs)

    def serialize(self, obj, **kwargs):
        self.object = obj
        serializer = self.get_serializer(**kwargs)
        return serializer.data

    def dispatch(self, request, *args, station_pk=None, **kwargs):
        self.streamer = self.get_streamer(request, station_pk, **kwargs)
        return super().dispatch(request, *args, **kwargs)


class RequestViewSet(BaseControllerAPIView):
    serializer = RequestSerializer


class StreamerViewSet(BaseControllerAPIView):
    serializer = StreamerSerializer

    def retrieve(self, request, pk=None):
        return Response(self.serialize(self.streamer))

    def list(self, request, pk=None):
        return Response({
            'results': self.serialize(streamers.values(), many=True)
        })

    def dispatch(self, request, *args, pk=None, **kwargs):
        if pk is not None:
            kwargs.setdefault('station_pk', pk)
        self.streamer = self.get_streamer(request, **kwargs)
        self.object = self.streamer
        return super().dispatch(request, *args, **kwargs)


class SourceViewSet(BaseControllerAPIView):
    serializer = SourceSerializer
    model = controllers.Source

    def get_sources(self):
        return (s for s in self.streamer.sources if isinstance(s, self.model))

    def get_source(self, pk):
        source = next((source for source in self.get_sources()
                      if source.id == pk), None)
        if source is None:
            raise Http404('source `%s` not found' % pk)
        return source

    def retrieve(self, request, pk=None):
        self.object = self.get_source(pk)
        return Response(self.serialize())

    def list(self, request):
        return Response({
            'results': self.serialize(self.get_sources(), many=True)
        })

    def _run(self, pk, action):
        source = self.object = self.get_source(pk)
        action(source)
        source.fetch()
        return Response(self.serialize(source))

    @action(detail=True, methods=['POST'])
    def sync(self, request, pk):
        return self._run(pk, lambda s: s.sync())

    @action(detail=True, methods=['POST'])
    def skip(self, request, pk):
        return self._run(pk, lambda s: s.skip())

    @action(detail=True, methods=['POST'])
    def restart(self, request, pk):
        return self._run(pk, lambda s: s.restart())

    @action(detail=True, methods=['POST'])
    def seek(self, request, pk):
        count = request.POST['seek']
        return self._run(pk, lambda s: s.seek(count))


class PlaylistSourceViewSet(SourceViewSet):
    serializer = PlaylistSerializer
    model = controllers.PlaylistSource


class QueueSourceViewSet(SourceViewSet):
    serializer = QueueSourceSerializer
    model = controllers.QueueSource

    def get_sound_queryset(self):
        return Sound.objects.station(self.request.station).archive()

    @action(detail=False, url_path='autocomplete/push',
            url_name='autocomplete-push')
    def autcomplete_push(self, request):
        query = request.GET.get('q')
        qs = self.get_sound_queryset().search(query)
        serializer = SoundSerializer(qs, many=True, context={
            'request': self.request
        })
        return Response({'results': serializer.data})

    @action(detail=True, methods=['POST'])
    def push(self, request, pk):
        if not request.data.get('sound_id'):
            raise ValidationError('missing "sound_id" POST data')

        sound = get_object_or_404(self.get_sound_queryset(),
                                  pk=request.data['sound_id'])
        return self._run(
            pk, lambda s: s.push(sound.path) if sound.path else None)


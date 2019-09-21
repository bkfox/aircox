from django.urls import reverse

from rest_framework import serializers

from .controllers import QueueSource, PlaylistSource


__all__ = ['RequestSerializer', 'StreamerSerializer', 'SourceSerializer',
           'PlaylistSerializer', 'QueueSourceSerializer']
# TODO: use models' serializers


class BaseSerializer(serializers.Serializer):
    url_ = serializers.SerializerMethodField('get_url')
    url_name = None

    def get_url(self, obj, **kwargs):
        if not obj or not self.url_name:
            return
        kwargs.setdefault('pk', getattr(obj, 'id', None))
        return reverse(self.url_name, kwargs=kwargs)


class BaseMetadataSerializer(BaseSerializer):
    rid = serializers.IntegerField()
    air_time = serializers.DateTimeField()
    uri = serializers.CharField()


class RequestSerializer(BaseMetadataSerializer):
    title = serializers.CharField(required=False)
    artist = serializers.CharField(required=False)


class SourceSerializer(BaseMetadataSerializer):
    id = serializers.CharField()
    uri = serializers.CharField()
    rid = serializers.IntegerField()
    air_time = serializers.DateTimeField()
    status = serializers.CharField()
    remaining = serializers.FloatField()

    def get_url(self, obj, **kwargs):
        kwargs['station_pk'] = obj.station.pk
        return super().get_url(obj, **kwargs)


class PlaylistSerializer(SourceSerializer):
    program = serializers.CharField(source='program.title')

    url_name = 'admin:api:streamer-playlist-detail'

class QueueSourceSerializer(SourceSerializer):
    queue = serializers.ListField(child=RequestSerializer(), source='requests')

    url_name = 'admin:api:streamer-queue-detail'


class StreamerSerializer(BaseSerializer):
    id = serializers.IntegerField(source='station.pk')
    name = serializers.CharField(source='station.name')
    source = serializers.CharField(source='source.id', required=False)
    playlists = serializers.ListField(child=PlaylistSerializer())
    queues = serializers.ListField(child=QueueSourceSerializer())

    url_name = 'admin:api:streamer-detail'

    def get_url(self, obj, **kwargs):
        kwargs['pk'] = obj.station.pk
        return super().get_url(obj, **kwargs)


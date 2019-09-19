from rest_framework import serializers


__all__ = ['RequestSerializer', 'StreamerSerializer', 'SourceSerializer',
           'PlaylistSerializer', 'QueueSourceSerializer']
# TODO: use models' serializers


class BaseMetadataSerializer(serializers.Serializer):
    rid = serializers.IntegerField()
    air_time = serializers.DateTimeField()
    uri = serializers.CharField()


class RequestSerializer(serializers.Serializer):
    title = serializers.CharField()
    artist = serializers.CharField()


class StreamerSerializer(serializers.Serializer):
    station = serializers.CharField(source='station.title')


class SourceSerializer(BaseMetadataSerializer):
    id = serializers.CharField()
    uri = serializers.CharField()
    rid = serializers.IntegerField()
    air_time = serializers.DateTimeField()
    status = serializers.CharField()


class PlaylistSerializer(SourceSerializer):
    program = serializers.CharField(source='program.title')
    playlist = serializers.ListField(child=serializers.CharField())


class QueueSourceSerializer(SourceSerializer):
    queue = serializers.ListField(child=RequestSerializer())



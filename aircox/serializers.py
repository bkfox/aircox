from rest_framework import serializers

from .models import Diffusion, Log


__all__ = ['LogInfo', 'LogInfoSerializer']


class LogInfo:
    obj = None
    start, end = None, None
    title, artist = '', ''
    url, cover = None, None
    info = None

    def __init__(self, obj):
        self.obj = obj
        if isinstance(obj, Diffusion):
            self.from_diffusion(obj)
        elif isinstance(obj, Log):
            self.from_log(obj)
        else:
            raise ValueError('`obj` must be a Diffusion or a track Log.')

    @property
    def type(self):
        return 'track' if isinstance(self.obj, Log) else 'diffusion'

    def from_diffusion(self, obj):
        episode = obj.episode
        self.start, self.end = obj.start, obj.end
        self.title, self.url = episode.title, episode.get_absolute_url()
        self.cover = episode.cover.icons['64']
        self.info = episode.category.title
        self.obj = obj

    def from_log(self, obj):
        track = obj.track
        self.start = obj.date
        self.title, self.artist = track.title, track.artist
        self.info = track.info
        self.obj = obj


class LogInfoSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=10)
    start = serializers.DateTimeField()
    end = serializers.DateTimeField(required=False)
    title = serializers.CharField(max_length=200)
    artist = serializers.CharField(max_length=200, required=False)
    info = serializers.CharField(max_length=200, required=False)
    url = serializers.URLField(required=False)
    cover = serializers.URLField(required=False)



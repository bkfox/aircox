from django.db.models import Q

from rest_framework import viewsets
from django_filters import rest_framework as filters

from .models import Sound
from .serializers import SoundSerializer
from .views import BaseAPIView


class SoundFilter(filters.FilterSet):
    station = filters.NumberFilter(field_name='program__station__id')
    program = filters.NumberFilter(field_name='program_id')
    episode = filters.NumberFilter(field_name='episode_id')
    search = filters.CharFilter(field_name='search', method='search_filter')

    def search_filter(self, queryset, name, value):
        return queryset.search(value)


class SoundViewSet(BaseAPIView, viewsets.ModelViewSet):
    serializer_class = SoundSerializer
    queryset = Sound.objects.available().order_by('-pk')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SoundFilter


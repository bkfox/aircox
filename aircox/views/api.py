import datetime

from django.utils import timezone as tz

from rest_framework.generics import ListAPIView

from ..models import Log
from ..serializers import LogInfo, LogInfoSerializer
from .log import BaseLogListView


class BaseAPIView:
    @property
    def station(self):
        return self.request.station

    def get_queryset(self):
        return super().get_queryset().station(self.station)


class LiveAPIView(BaseLogListView, BaseAPIView, ListAPIView):
    model = Log
    serializer_class = LogInfoSerializer
    min_date = None
    queryset = Log.objects.all()

    def get(self, *args, **kwargs):
        self.min_date = tz.now() - tz.timedelta(minutes=5)
        return super().get(*args, **kwargs)

    def get_serializer(self, queryset, *args, **kwargs):
        queryset = Log.merge_diffusions(self.get_queryset(),
                                        self.get_diffusions_queryset())
        queryset = [LogInfo(obj) for obj in queryset]
        return super().get_serializer(queryset, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().after(self.min_date)

    def get_diffusions_queryset(self):
        return super().get_diffusions_queryset().after(self.min_date)


# Monitoring



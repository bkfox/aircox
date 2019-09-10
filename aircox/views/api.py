import datetime

from django.utils import timezone as tz

from rest_framework.generics import ListAPIView

from ..models import Log
from ..serializers import LogInfo, LogInfoSerializer
from .log import LogListMixin


class BaseAPIView:
    @property
    def station(self):
        return self.request.station

    def get_queryset(self):
        return super().get_queryset().station(self.station)


class LogListAPIView(LogListMixin, BaseAPIView, ListAPIView):
    """
    Return logs list, including diffusions. By default return logs of
    the last 30 minutes.

    Available GET parameters:
    - "date": return logs for a specified date (
    - "full": (staff user only) don't merge diffusion and logs
    """
    serializer_class = LogInfoSerializer
    queryset = Log.objects.all()

    def get(self, *args, **kwargs):
        self.date = self.get_date()
        if self.date is None:
            self.min_date = tz.now() - tz.timedelta(minutes=30)
        return super().get(*args, **kwargs)

    def get_object_list(self, logs, full):
        return [LogInfo(obj) for obj in super().get_object_list(logs, full)]

    def get_serializer(self, queryset, *args, **kwargs):
        full = bool(self.request.GET.get('full'))
        return super().get_serializer(self.get_object_list(queryset, full),
                                      *args, **kwargs)



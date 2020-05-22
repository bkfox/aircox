from collections import deque
import datetime

from django.views.generic import ListView
from django.utils import timezone as tz

from rest_framework.generics import ListAPIView
from rest_framework import viewsets
from rest_framework.decorators import action

from ..models import Diffusion, Log
from ..serializers import LogInfo, LogInfoSerializer
from .base import BaseView, BaseAPIView
from .mixins import GetDateMixin


__all__ = ['LogListMixin', 'LogListView']


class LogListMixin(GetDateMixin):
    model = Log
    min_date = None

    def get_date(self):
        date = super().get_date()
        if date is not None and not self.request.user.is_staff:
            return min(date, datetime.date.today())
        return date

    def get_queryset(self):
        # only get logs for tracks: log for diffusion will be retrieved
        # by the diffusions' queryset.
        qs = super().get_queryset().on_air().filter(track__isnull=False) \
                                   .filter(date__lte=tz.now())
        return qs.date(self.date) if self.date is not None else \
            qs.after(self.min_date) if self.min_date is not None else qs

    def get_diffusions_queryset(self):
        qs = Diffusion.objects.station(self.station).on_air() \
                      .filter(start__lte=tz.now())
        return qs.date(self.date) if self.date is not None else \
            qs.after(self.min_date) if self.min_date is not None else qs

    def get_object_list(self, logs, full=False):
        """
        Return diffusions merged to the provided logs queryset. If
        `full`, sort items by date without merging.
        """
        diffs = self.get_diffusions_queryset()
        if self.request.user.is_staff and full:
            return sorted(list(logs) + list(diffs), key=lambda obj: obj.start)
        return Log.merge_diffusions(logs, diffs)


class LogListView(BaseView, LogListMixin, ListView):
    """
    Return list of logs for the provided date (from `kwargs` or
    `request.GET`, defaults to today).
    """
    redirect_date_url = 'log-list'
    has_filters = True

    def get_date(self):
        date = super().get_date()
        return datetime.date.today() if date is None else date

    def get_context_data(self, **kwargs):
        today = datetime.date.today()
        kwargs = super().get_context_data(**kwargs)
        print('objects:', self.date, self.get_queryset(), kwargs['object_list'])
        kwargs.update({
            'date': self.date,
            'dates': (today - datetime.timedelta(days=i) for i in range(0, 7)),
            'object_list': self.get_object_list(self.object_list),
        })
        return kwargs


# Logs are accessible through API only with this list view
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

    def get_date(self):
        date = super().get_date()
        if date is None:
            self.min_date = tz.now() - tz.timedelta(minutes=30)
        return date

    def get_object_list(self, logs, full):
        return [LogInfo(obj) for obj in super().get_object_list(logs, full)]

    def get_serializer(self, queryset, *args, **kwargs):
        full = bool(self.request.GET.get('full'))
        return super().get_serializer(self.get_object_list(queryset, full),
                                      *args, **kwargs)


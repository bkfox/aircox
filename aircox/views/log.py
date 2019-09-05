from collections import deque
import datetime

from django.views.generic import ListView

from ..models import Diffusion, Log
from .base import BaseView


__all__ = ['BaseLogListView', 'LogListView']


class BaseLogListView:
    model = Log
    date = None

    def get_queryset(self):
        # only get logs for tracks: log for diffusion will be retrieved
        # by the diffusions' queryset.
        return super().get_queryset().on_air().filter(track__isnull=False)

    def get_diffusions_queryset(self):
        return Diffusion.objects.station(self.station).on_air()


class LogListView(BaseView, BaseLogListView, ListView):
    date = None
    max_age = 10
    min_date = None

    def get(self, request, *args, **kwargs):
        today = datetime.date.today()
        self.min_date = today - datetime.timedelta(days=self.max_age)
        self.date = min(max(self.min_date, self.kwargs['date']), today) \
            if 'date' in self.kwargs else today
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().today(self.date)

    def get_diffusions_queryset(self):
        return super().get_diffusions_queryset().today(self.date)

    def get_context_data(self, **kwargs):
        today = datetime.date.today()
        max_date = min(max(self.date + datetime.timedelta(days=3),
                           self.min_date + datetime.timedelta(days=6)), today)

        return super().get_context_data(
            date=self.date,
            min_date=self.min_date,
            dates=(date for date in (
                max_date - datetime.timedelta(days=i)
                for i in range(0, 7)) if date >= self.min_date),
            object_list=Log.merge_diffusions(self.object_list,
                                             self.get_diffusions_queryset()),
            **kwargs
        )



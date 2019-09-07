from collections import deque
import datetime

from django.views.generic import ListView

from ..models import Diffusion, Log
from .base import BaseView
from .mixins import GetDateMixin


__all__ = ['LogListMixin', 'LogListView']


class LogListMixin(GetDateMixin):
    model = Log

    def get_date(self):
        date, today = super().get_date(), datetime.date.today()
        if date is not None and not self.request.user.is_staff:
            return min(date, today)
        return date

    def get_queryset(self):
        # only get logs for tracks: log for diffusion will be retrieved
        # by the diffusions' queryset.
        qs = super().get_queryset().on_air().filter(track__isnull=False)
        return qs.today(self.date) if self.date is not None else \
            qs.after(self.min_date) if self.min_date is not None else qs

    def get_diffusions_queryset(self):
        qs = Diffusion.objects.station(self.station).on_air()
        return qs.today(self.date) if self.date is not None else \
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
    def get_date(self):
        date, today = super().get_date(), datetime.date.today()
        return today if date is None else min(date, today)

    def get_context_data(self, **kwargs):
        today = datetime.date.today()
        kwargs.update({
            'date': self.date,
            'dates': ((today - datetime.timedelta(days=i), None)
                      for i in range(0, 7)),
            'object_list': self.get_object_list(self.object_list),
        })
        return super().get_context_data(**kwargs)



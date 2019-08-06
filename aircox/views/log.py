from collections import deque
import datetime

from django.views.generic import ListView

from ..models import Diffusion, Log
from .base import BaseView


__all__ = ['BaseLogView', 'LogListView']


class BaseLogView(ListView):
    station = None
    date = None
    delta = None

    def get_queryset(self):
        # only get logs for tracks: log for diffusion will be retrieved
        # by the diffusions' queryset.
        return super().get_queryset().station(self.station).on_air() \
                      .at(self.date).filter(track__isnull=False)

    def get_diffusions_queryset(self):
        return Diffusion.objects.station(self.station).on_air() \
                                .today(self.date)

    def get_object_list(self, queryset):
        diffs = deque(self.get_diffusions_queryset().order_by('start'))
        logs = list(queryset.order_by('date'))
        if not len(diffs):
            return logs

        object_list = []
        diff = None
        last_collision = None

        # TODO/FIXME: multiple diffs at once - recheck the whole algorithm in
        #       detail -- however I barely see cases except when there are diff
        #       collision or the streamer is not working
        for index, log in enumerate(logs):
            # get next diff
            if diff is None or diff.end < log.date:
                diff = diffs.popleft() if len(diffs) else None

            # no more diff that can collide: return list
            if diff is None:
                if last_collision and not object_list or \
                        object_list[-1] is not last_collision:
                    object_list.append(last_collision)
                return object_list + logs[index:]

            # diff colliding with log
            if diff.start <= log.date:
                if not object_list or object_list[-1] is not diff:
                    object_list.append(diff)
                if log.date <= diff.end:
                    last_collision = log
            else:
                # add last colliding log: track
                if last_collision is not None:
                    object_list.append(last_collision)

                object_list.append(log)
                last_collision = None
        return object_list


class LogListView(BaseView, BaseLogView):
    model = Log

    date = None
    max_age = 10
    min_date = None

    def get(self, request, *args, **kwargs):
        today = datetime.date.today()
        self.min_date = today - datetime.timedelta(days=self.max_age)
        self.date = min(max(self.min_date, self.kwargs['date']), today) \
            if 'date' in self.kwargs else today
        return super().get(request, *args, **kwargs)

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
            object_list=self.get_object_list(self.object_list),
            **kwargs
        )

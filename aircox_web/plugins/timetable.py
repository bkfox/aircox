import datetime

from django.db import models
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _

from aircox import models as aircox
from aircox_web.fields import PositiveSmallMinMaxField


class Timetable(models.Model):
    station = models.ForeignKey(
        aircox.Station, models.CASCADE, verbose_name=_('station'),
    )
    days_before = models.PositiveSmallMinMaxField(
        _('days before'), min=0, max=6,
        help_text=_('Count of days displayed current date'),
    )
    days_after = models.PositiveSmallMinMaxField(
        _('days after'), min=0, max=6,
        help_text=_('Count of days displayed current date'),
    )

    def get_queryset(self, date=None):
        date = date if date is not None else datetime.date.today()
        qs = aircox.Diffusion.objects.station(self.station)
        if self.days_before is None and self.days_after is None:
            return qs.at(date)

        start = date - datetime.timedelta(days=self.days_before) \
            if self.days_before else date
        stop = date + datetime.timedelta(days=self.days_after) \
            if self.days_after else date
        return aircox.Diffusion.objects.station(self.station) \
                     .after(start).before(stop)



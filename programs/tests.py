import datetime
import calendar
import logging
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.utils import timezone as tz

from aircox.programs.models import *

logger = logging.getLogger('aircox.test')
logger.setLevel('INFO')

class ScheduleCheck (TestCase):
    def setUp(self):
        self.schedules = [
            Schedule(
                date = tz.now(),
                duration = datetime.time(1,30),
                frequency = frequency,
            )
            for frequency in Schedule.Frequency.__members__.values()
        ]

    def test_frequencies(self):
        for schedule in self.schedules:
            logger.info('- test frequency %s' % schedule.get_frequency_display())
            date = schedule.date
            count = 24
            while count:
                logger.info('- month %(month)s/%(year)s' % {
                    'month': date.month,
                    'year': date.year
                })
                count -= 1
                dates = schedule.dates_of_month(date)
                if schedule.frequency == schedule.Frequency.one_on_two:
                    self.check_one_on_two(schedule, date, dates)
                elif schedule.frequency == schedule.Frequency.last:
                    self.check_last(schedule, date, dates)
                else:
                    pass
                date += relativedelta(months = 1)

    def check_one_on_two(self, schedule, date, dates):
        for date in dates:
            delta = date.date() - schedule.date.date()
            self.assertEqual(delta.days % 14, 0)

    def check_last(self, schedule, date, dates):
        month_info = calendar.monthrange(date.year, date.month)
        date = datetime.date(date.year, date.month, month_info[1])

        # end of month before the wanted weekday: move one week back
        if date.weekday() < schedule.date.weekday():
            date -= datetime.timedelta(days = 7)

        date -= datetime.timedelta(days = date.weekday())
        date += datetime.timedelta(days = schedule.date.weekday())
        self.assertEqual(date, dates[0].date())

    def check_n_of_week(self, schedule, date, dates):
        pass




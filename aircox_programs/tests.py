import datetime

from django.test import TestCase
from django.utils import timezone as tz

from aircox_programs.models import *

class Programs (TestCase):
    def setUp (self):
        stream = Stream.objects.get_or_create(
            name = 'diffusions',
            defaults = { 'type': Stream.Type['schedule'] }
        )[0]
        Program.objects.create(name = 'source', stream = stream)
        Program.objects.create(name = 'microouvert', stream = stream)
        #Stream.objects.create(name = 'bns', type = Stream.Type['random'], priority = 1)
        #Stream.objects.create(name = 'jingle', type = Stream.Type['random'] priority = 2)
        #Stream.objects.create(name = 'loves', type = Stream.Type['random'], priority = 3)
        pass

    def test_programs_schedules (self):
        program = Program.objects.get(name = 'source')

        sched_0 = self.create_schedule(program, 'one on two', [
                tz.datetime(2015, 10, 2, 18),
                tz.datetime(2015, 10, 16, 18),
                tz.datetime(2015, 10, 30, 18),
            ]
        )
        sched_1 = self.create_schedule(program, 'one on two', [
                tz.datetime(2015, 10, 5, 18),
                tz.datetime(2015, 10, 19, 18),
            ],
            rerun = sched_0
        )

        program = Program.objects.get(name = 'microouvert')
        # special case with november first week starting on sunday
        sched_2 = self.create_schedule(program, 'first and third', [
                tz.datetime(2015, 11, 6, 18),
                tz.datetime(2015, 11, 20, 18),
            ],
            date = tz.datetime(2015, 10, 23, 18),
        )

    def create_schedule (self, program, frequency, dates, date = None, rerun = None):
        frequency = Schedule.Frequency[frequency]
        schedule = Schedule(
            program = program,
            frequency = frequency,
            date = date or dates[0],
            rerun = rerun,
            duration = datetime.time(1, 30)
        )
        print(schedule.__dict__)
        schedule.save()

        self.check_schedule(schedule, dates)
        return schedule

    def check_schedule (self, schedule, dates):
        dates = [ tz.make_aware(date) for date in dates ]
        dates.sort()

        # match date and weeks
        for date in dates:
            #self.assertTrue(schedule.match(date, check_time = False))
            #self.assertTrue(schedule.match_week(date))

        # dates
        dates_ = schedule.dates_of_month(dates[0])
        dates_.sort()
        self.assertEqual(dates_, dates)

        # diffusions
        dates_ = schedule.diffusions_of_month(dates[0])
        dates_ = [date_.date for date_ in dates_]
        dates_.sort()
        self.assertEqual(dates_, dates)



import datetime

from django.test import TestCase
from django.utils import timezone as tz

from aircox.programs.models import *


class Programs (TestCase):
    def setUp (self):
        stream = Stream.objects.get_or_create(
            name = 'diffusions',
            defaults = { 'type': Stream.Type['schedule'] }
        )[0]
        Program.objects.create(name = 'source', stream = stream)
        Program.objects.create(name = 'microouvert', stream = stream)

        self.schedules = {}
        self.programs = {}

    def test_create_programs_schedules (self):
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

        self.programs[program.pk] = program

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

        self.schedules[schedule.pk] = (schedule, dates)
        return schedule

    def test_check_schedule (self):
        for schedule, dates in self.schedules:
            dates = [ tz.make_aware(date) for date in dates ]
            dates.sort()

            # dates
            dates_ = schedule.dates_of_month(dates[0])
            dates_.sort()
            self.assertEqual(dates_, dates)

            # diffusions
            dates_ = schedule.diffusions_of_month(dates[0])
            dates_ = [date_.date for date_ in dates_]
            dates_.sort()
            self.assertEqual(dates_, dates)



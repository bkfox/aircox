import datetime

from django.core.management.base            import BaseCommand, CommandError
from django.utils                           import timezone, dateformat

import programs.models                      as models
import programs.settings


class Diffusion:
    ref = None
    date_start = None
    date_end = None

    def __init__ (self, ref, date_start, date_end):
        self.ref = ref
        self.date_start = date_start
        self.date_end = date_end

    def __lt__ (self, d):
        return self.date_start < d.date_start and \
               self.date_end < d.date_end



class Command (BaseCommand):
    help= "check sounds to diffuse"

    diffusions = set()

    def handle(self, *args, **options):
        self.get_next_events()
        self.get_next_episodes()

        for diffusion in self.diffusions:
            print( diffusion.ref.__str__()
                 , diffusion.date_start
                 , diffusion.date_end)



    def get_next_episodes (self):
        schedules = models.Schedule.objects.filter()
        for schedule in schedules:
            date = schedule.next_date()
            if not date:
                continue

            dt = datetime.timedelta( hours = schedule.duration.hour
                                   , minutes = schedule.duration.minute
                                   , seconds = schedule.duration.second )

            ref = models.Episode.objects.filter(date = date)[:1]
            if not ref:
                ref = ( schedule.parent, )

            diffusion = Diffusion(ref[0], date, date + dt)
            self.diffusions.add(diffusion)


    def get_next_events (self):
        events = models.Event.objects.filter(date_end__gt = timezone.now(),
                                             canceled = False) \
                                     .extra(order_by = ['date'])[:10]
        for event in events:
            diffusion = Diffusion(event, event.date, event.date_end)
            self.diffusions.add(diffusion)






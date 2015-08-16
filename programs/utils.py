from django.utils                   import timezone

from programs.models                import Schedule, Event, Episode,\
                                           SoundFile, Frequency



def update_scheduled_events (date):
    """
    Update planified events from schedules
    TODO: notification in case of conflicts?
    """
    all_schedules = Schedule.objects().all()
    schedules = [ schedule
                    for schedule in models.Schedule.objects().all()
                    if schedule.match-date(date) ]

    schedules.sort(key = lambda e: e.date)

    for schedule in schedules:
        if schedule.frequency == Frequency['ponctual']:
            continue

        ev_date = timezone.datetime(date.year, date.month, date.day,
                                    schedule.date.hour, schedule.date.minute)

        # if event exists, pass
        n = Event.objects() \
                 .filter(date = ev_date, parent__parent = schedule.parent) \
                 .count()
        if n:
            continue

        ep_date = ev_date

        # rerun?
        if schedule.rerun:
            schedule = schedule.rerun
            date_ = schedule.date

        episode = Episode.objects().filter(date = date)



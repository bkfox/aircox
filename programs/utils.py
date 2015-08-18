from django.utils                   import timezone

from programs.models                import Schedule, Event, Episode,\
                                           EventType



def scheduled_month_events (date = None, unsaved_only = False):
    """
    Return a list of scheduled events for the month of the given date. For the
    non existing events, a program attribute to the corresponding program is
    set.
    """
    if not date:
        date = timezone.datetime.today()

    schedules = Schedule.objects.all()
    events = []

    for schedule in schedules:
        dates = schedule.dates_of_month()
        for date in dates:
            event = Event.objects \
                         .filter(date = date, parent__parent = schedule.parent)

            if event.count():
                if not unsaved_only:
                    events.append(event)
                continue

            # get episode
            ep_date = date
            if schedule.rerun:
                ep_date = schedule.rerun.date

            episode = Episode.objects().filter( date = ep_date
                                              , parent = schedule.parent )
            episode  = episode[0] if episode.count() else None

            # make event
            event = Event( parent = episode
                         , program = schedule.parent
                         , type = EventType['diffuse']
                         , date = date
                         , stream = settings.AIRCOX_SCHEDULED_STREAM
                         , scheduled = True
                         )
            event.program = schedule.program
            events.append(event)
    return events



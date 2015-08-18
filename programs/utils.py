from django.utils                   import timezone

from programs.models                import Schedule, Diffusion, Episode,\
                                           DiffusionType



def scheduled_month_diffusions (date = None, unsaved_only = False):
    """
    Return a list of scheduled diffusions for the month of the given date. For the
    non existing diffusions, a program attribute to the corresponding program is
    set.
    """
    if not date:
        date = timezone.datetime.today()

    schedules = Schedule.objects.all()
    diffusions = []

    for schedule in schedules:
        dates = schedule.dates_of_month()
        for date in dates:
            diffusion = Diffusion.objects \
                         .filter(date = date, parent__parent = schedule.parent)

            if diffusion.count():
                if not unsaved_only:
                    diffusions.append(diffusion)
                continue

            # get episode
            ep_date = date
            if schedule.rerun:
                ep_date = schedule.rerun.date

            episode = Episode.objects().filter( date = ep_date
                                              , parent = schedule.parent )
            episode  = episode[0] if episode.count() else None

            # make diffusion
            diffusion = Diffusion( parent = episode
                         , program = schedule.parent
                         , type = DiffusionType['diffuse']
                         , date = date
                         , stream = settings.AIRCOX_SCHEDULED_STREAM
                         , scheduled = True
                         )
            diffusion.program = schedule.program
            diffusions.append(diffusion)
    return diffusions



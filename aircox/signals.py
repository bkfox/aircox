from django.db.models.signals import post_save, pre_delete

from django.dispatch import receiver
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.contenttypes.models import ContentType

import aircox.models as models
import aircox.utils as utils

# FIXME: avoid copy of the code in schedule_post_saved and
#        schedule_pre_delete

@receiver(post_save, sender=models.Schedule)
def schedule_post_saved(sender, instance, created, *args, **kwargs):
    # TODO: case instance.program has changed
    if not instance.program.sync:
        return

    initial = instance._Schedule__initial
    if not initial or not instance.changed(['date','duration', 'frequency']):
        return

    if not initial.get('date') or not initial.get('duration') or not initial.get('frequency'):
        return

    # old schedule and timedelta
    old_sched = models.Schedule(
        program = instance.program,
        date = initial['date'],
        duration = initial['duration'],
        frequency = initial['frequency'],
    )
    delta = instance.date - old_sched.date

    # update diffusions...
    qs = models.Diffusion.objects.get_after().filter(
        program = instance.program
    )
    for diff in qs:
        if not old_sched.match(diff.date):
            continue
        diff.start += delta
        diff.end = diff.start + utils.to_timedelta(instance.duration)
        diff.save()

@receiver(pre_delete, sender=models.Schedule)
def schedule_pre_delete(sender, instance, *args, **kwargs):
    if not instance.program.sync:
        return

    initial = instance._Schedule__initial
    if not initial or not instance.changed(['date','duration', 'frequency']):
        return

    old_sched = models.Schedule(
        date = initial['date'],
        duration = initial['duration'],
        frequency = initial['frequency'],
    )

    qs = models.Diffusion.objects.get_after().filter(
        program = instance.program
    )
    for diff in qs:
        if not old_sched.match(diff.date):
            continue
        diff.delete()


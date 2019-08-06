import pytz

from django.contrib.auth.models import User, Group, Permission
from django.db.models import F, signals
from django.dispatch import receiver
from django.utils import timezone as tz

from .. import settings, utils
from . import Diffusion, Episode, Program, Schedule


# Add a default group to a user when it is created. It also assigns a list
# of permissions to the group if it is created.
#
# - group name: settings.AIRCOX_DEFAULT_USER_GROUP
# - group permissions: settings.AIRCOX_DEFAULT_USER_GROUP_PERMS
#
@receiver(signals.post_save, sender=User)
def user_default_groups(sender, instance, created, *args, **kwargs):
    """
    Set users to different default groups
    """
    if not created or instance.is_superuser:
        return

    for groupName, permissions in settings.AIRCOX_DEFAULT_USER_GROUPS.items():
        if instance.groups.filter(name=groupName).count():
            continue

        group, created = Group.objects.get_or_create(name=groupName)
        if created and permissions:
            for codename in permissions:
                permission = Permission.objects.filter(
                    codename=codename).first()
                if permission:
                    group.permissions.add(permission)
            group.save()
        instance.groups.add(group)


@receiver(signals.post_save, sender=Program)
def program_post_save(sender, instance, created, *args, **kwargs):
    """
    Clean-up later diffusions when a program becomes inactive
    """
    if not instance.active:
        Diffusion.objects.program(instance).after().delete()
        Episode.object.program(instance).filter(diffusion__isnull=True) \
               .delete()


@receiver(signals.pre_save, sender=Schedule)
def schedule_pre_save(sender, instance, *args, **kwargs):
    if getattr(instance, 'pk') is not None:
        instance._initial = Schedule.objects.get(pk=instance.pk)


# TODO
@receiver(signals.post_save, sender=Schedule)
def schedule_post_save(sender, instance, created, *args, **kwargs):
    """
    Handles Schedule's time, duration and timezone changes and update
    corresponding diffusions accordingly.
    """
    initial = getattr(instance, '_initial', None)
    if not initial or ((instance.time, instance.duration, instance.timezone) ==
                       (initial.time, initial.duration, initial.timezone)):
        return

    today = tz.datetime.today()
    delta = instance.normalize(today) - initial.normalize(today)

    qs = Diffusion.objects.program(instance.program).after()
    pks = [d.pk for d in qs if initial.match(d.date)]
    qs.filter(pk__in=pks).update(
        start=F('start') + delta,
        end=F('start') + delta + utils.to_timedelta(instance.duration)
    )


@receiver(signals.pre_delete, sender=Schedule)
def schedule_pre_delete(sender, instance, *args, **kwargs):
    """
    Delete later corresponding diffusion to a changed schedule.
    """
    if not instance.program.sync:
        return

    qs = Diffusion.objects.program(instance.program).after()
    pks = [d.pk for d in qs if instance.match(d.date)]
    qs.filter(pk__in=pks).delete()


@receiver(signals.post_delete, sender=Diffusion)
def diffusion_post_delete(sender, instance, *args, **kwargs):
    Episode.objects.filter(diffusion__isnull=True, content_isnull=True,
                           sound__isnull=True) \
                   .delete()



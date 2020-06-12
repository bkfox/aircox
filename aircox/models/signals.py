import pytz

from django.contrib.auth.models import User, Group, Permission
from django.db import transaction
from django.db.models import F, signals
from django.dispatch import receiver
from django.utils import timezone as tz

from .. import settings, utils
from . import Diffusion, Episode, Page, Program, Schedule


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

    for group_name, permissions in settings.AIRCOX_DEFAULT_USER_GROUPS.items():
        if instance.groups.filter(name=group_name).count():
            continue

        group, created = Group.objects.get_or_create(name=group_name)
        if created and permissions:
            for codename in permissions:
                permission = Permission.objects.filter(
                    codename=codename).first()
                if permission:
                    group.permissions.add(permission)
            group.save()
        instance.groups.add(group)


@receiver(signals.post_save, sender=Page)
def page_post_save(sender, instance, created, *args, **kwargs):
    if not created and instance.cover:
        Page.objects.filter(parent=instance, cover__isnull=True) \
                    .update(cover=instance.cover)


@receiver(signals.post_save, sender=Program)
def program_post_save(sender, instance, created, *args, **kwargs):
    """
    Clean-up later diffusions when a program becomes inactive
    """
    if not instance.active:
        Diffusion.object.program(instance).after(tz.now()).delete()
        Episode.object.parent(instance).filter(diffusion__isnull=True) \
               .delete()

    cover = getattr(instance, '__initial_cover', None)
    if cover is None and instance.cover is not None:
        Episode.objects.parent(instance) \
                       .filter(cover__isnull=True) \
                       .update(cover=instance.cover)



@receiver(signals.pre_save, sender=Schedule)
def schedule_pre_save(sender, instance, *args, **kwargs):
    if getattr(instance, 'pk') is not None:
        instance._initial = Schedule.objects.get(pk=instance.pk)


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
    duration = utils.to_timedelta(instance.duration)
    with transaction.atomic():
        qs = Diffusion.objects.filter(schedule=instance).after(tz.now())
        for diffusion in qs:
            diffusion.start = diffusion.start + delta
            diffusion.end = diffusion.start + duration
            diffusion.save()


@receiver(signals.pre_delete, sender=Schedule)
def schedule_pre_delete(sender, instance, *args, **kwargs):
    """ Delete later corresponding diffusion to a changed schedule. """
    Diffusion.objects.filter(schedule=instance).after(tz.now()).delete()
    Episode.objects.filter(diffusion__isnull=True, content__isnull=True,
                           sound__isnull=True).delete()

@receiver(signals.post_delete, sender=Diffusion)
def diffusion_post_delete(sender, instance, *args, **kwargs):
    Episode.objects.filter(diffusion__isnull=True, content__isnull=True,
                           sound__isnull=True).delete()



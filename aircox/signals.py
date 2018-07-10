import pytz

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.db.models.signals import post_save, pre_save, pre_delete, m2m_changed
from django.dispatch import receiver, Signal
from django.utils import timezone as tz
from django.utils.translation import ugettext as _, ugettext_lazy

import aircox.models as models
import aircox.utils as utils
import aircox.settings as settings



# Add a default group to a user when it is created. It also assigns a list
# of permissions to the group if it is created.
#
# - group name: settings.AIRCOX_DEFAULT_USER_GROUP
# - group permissions: settings.AIRCOX_DEFAULT_USER_GROUP_PERMS
#
@receiver(post_save, sender=User)
def user_default_groups(sender, instance, created, *args, **kwargs):
    """
    Set users to different default groups
    """
    if not created or instance.is_superuser:
        return

    for groupName, permissions in settings.AIRCOX_DEFAULT_USER_GROUPS.items():
        if instance.groups.filter(name = groupName).count():
            continue

        group, created = Group.objects.get_or_create(name = groupName)
        if created and permissions:
            for codename in permissions:
                permission = Permission.objects.filter(codename = codename).first()
                if permission:
                    group.permissions.add(permission)
            group.save()
        instance.groups.add(group)

@receiver(post_save, sender=models.Program)
def program_post_save(sender, instance, created, *args, **kwargs):
    """
    Clean-up later diffusions when a program becomes inactive
    """
    if not instance.active:
        instance.diffusion_set.after().delete()

@receiver(post_save, sender=models.Schedule)
def schedule_post_save(sender, instance, created, *args, **kwargs):
    """
    Handles Schedule's time, duration and timezone changes and update
    corresponding diffusions accordingly.
    """
    if created or not instance.program.sync or \
            not instance.changed(['time','duration','timezone']):
        return

    initial = instance._Schedule__initial
    initial = models.Schedule(**{ k: v
        for k, v in instance._Schedule__initial.items()
            if not k.startswith('_')
    })

    today = tz.datetime.today()
    delta = instance.normalize(today) - \
            initial.normalize(today)

    qs = models.Diffusion.objects.program(instance.program).after()
    pks = [ d.pk for d in qs if initial.match(d.date) ]
    qs.filter(pk__in = pks).update(
        start = F('start') + delta,
        end = F('start') + delta + utils.to_timedelta(instance.duration)
    )


@receiver(pre_delete, sender=models.Schedule)
def schedule_pre_delete(sender, instance, *args, **kwargs):
    """
    Delete later corresponding diffusion to a changed schedule.
    """
    if not instance.program.sync:
        return

    qs = models.Diffusion.objects.program(instance.program).after()
    pks = [ d.pk for d in qs if instance.match(d.date) ]
    qs.filter(pk__in = pks).delete()



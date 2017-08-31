import pytz

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.db.models.signals import post_save, pre_save, pre_delete, m2m_changed
from django.dispatch import receiver
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


# FIXME: avoid copy of the code in schedule_post_saved and
#        schedule_pre_delete

@receiver(post_save, sender=models.Schedule)
def schedule_post_saved(sender, instance, created, *args, **kwargs):
    # TODO: case instance.program | instance.frequency has changed
    if not instance.program.sync:
        return

    initial = instance._Schedule__initial
    if not initial or not instance.changed(['date','duration', 'frequency']):
        return

    if not initial.get('date') or not initial.get('duration') \
            or not initial.get('frequency'):
        return

    # old schedule and timedelta
    old = models.Schedule(**{ key: initial.get(key)
        for key in ('date','timezone','duration','frequency')
    })
    start_delta = instance.local_date - old.local_date

    old.date = old.local_date.astimezone(pytz.UTC)

    qs = models.Diffusion.objects.station(
        instance.program.station,
    )

    pks = [ item.pk for item in qs if old.match(item.date) ]
    qs.filter(pk__in = pks).update(
        start = F('start') + start_delta,
        end = F('start') + start_delta + utils.to_timedelta(instance.duration)
    )
    return

@receiver(pre_delete, sender=models.Schedule)
def schedule_pre_delete(sender, instance, *args, **kwargs):
    if not instance.program.sync:
        return

    initial = instance._Schedule__initial
    if not initial or not instance.changed(['date','duration', 'frequency']):
        return

    old = models.Schedule(**{ key: initial.get(key)
        for key in ('date','timezone','duration','frequency')
    })

    qs = models.Diffusion.objects.station(
        instance.program.station,
    )

    pks = [ item.pk for item in qs if old.match(item.date) ]
    qs.filter(pk__in = pks).delete()


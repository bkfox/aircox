from django.db.models.signals import post_save
from django.dispatch import receiver

import aircox.models


@receiver(post_save, sender=programs.Program)
def on_new_program(sender, instance, created, *args):
    import aircox_cms.models as models
    if not created or instance.page.count():
        return



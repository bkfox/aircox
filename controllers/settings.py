import os
import stat

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


# Working directory for the controllers
ensure('AIRCOX_CONTROLLERS_MEDIA', '/tmp/aircox')



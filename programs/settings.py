import os

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


ensure('AIRCOX_PROGRAMS_DIR',
       os.path.join(settings.MEDIA_ROOT, 'programs'))
ensure('AIRCOX_SOUNDFILE_DEFAULT_DIR',
       os.path.join(AIRCOX_PROGRAMS_DIR + 'default'))




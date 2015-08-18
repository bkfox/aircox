import os

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


# Directory for the programs data
ensure('AIRCOX_PROGRAMS_DIR',
       os.path.join(settings.MEDIA_ROOT, 'programs'))

# Default directory for the soundfiles
ensure('AIRCOX_SOUNDFILE_DEFAULT_DIR',
       os.path.join(AIRCOX_PROGRAMS_DIR + 'default'))

# Extension of sound files
ensure('AIRCOX_SOUNDFILE_EXT',
        ('ogg','flac','wav','mp3','opus'))

# Stream for the scheduled diffusions
ensure('AIRCOX_SCHEDULED_STREAM', 0)



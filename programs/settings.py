import os
import stat

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


# Directory for the programs data
ensure('AIRCOX_PROGRAMS_DIR',
       os.path.join(settings.MEDIA_ROOT, 'programs'))

# Default directory for the sounds that not linked to a program
ensure('AIRCOX_SOUND_DEFAULT_DIR',
       os.path.join(AIRCOX_PROGRAMS_DIR, 'defaults')),
# Sub directory used for the complete episode sounds
ensure('AIRCOX_SOUND_ARCHIVES_SUBDIR', 'archives')
# Sub directory used for the excerpts of the episode
ensure('AIRCOX_SOUND_EXCERPTS_SUBDIR', 'excerpts')

# Change sound perms based on 'public' attribute if True
ensure('AIRCOX_SOUND_AUTO_CHMOD', True)
# Chmod bits flags as a tuple for (not public, public). Use os.chmod
# and stat.*
ensure(
    'AIRCOX_SOUND_CHMOD_FLAGS',
    (stat.S_IRWXU, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH )
)

# Quality attributes passed to sound_quality_check from sounds_monitor
ensure('AIRCOX_SOUND_QUALITY', {
        'attribute': 'RMS lev dB',
        'range': (-18.0, -8.0),
        'sample_length': 120,
    }
)

# Extension of sound files
ensure('AIRCOX_SOUND_FILE_EXT',
        ('.ogg','.flac','.wav','.mp3','.opus'))

# Stream for the scheduled diffusions
ensure('AIRCOX_SCHEDULED_STREAM', 0)


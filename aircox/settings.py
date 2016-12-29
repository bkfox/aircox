import os
import stat

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)

# group to assign to users at their creation, along with the permissions
# to add to each group.
ensure('AIRCOX_DEFAULT_USER_GROUPS', {
    'Radio Hosts': (
        'change_program', 'change_diffusion',
        'change_sound',
        'add_track', 'change_track', 'delete_track',
        'add_tag', 'change_tag', 'delete_tag',
    ),
    # ensure user can log in using Wagtail
    'Editors': None
})

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
ensure(
    'AIRCOX_SOUND_FILE_EXT',
    ('.ogg','.flac','.wav','.mp3','.opus')
)

# Stream for the scheduled diffusions
ensure('AIRCOX_SCHEDULED_STREAM', 0)


# Import playlist: columns for CSV file
ensure(
    'AIRCOX_IMPORT_PLAYLIST_CSV_COLS',
    ('artist', 'title', 'minutes', 'seconds', 'tags', 'info')
)
# Import playlist: column delimiter of csv text files
ensure('AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER', ';')
# Import playlist: text delimiter of csv text files
ensure('AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE', '"')


# Controllers working directory
ensure('AIRCOX_CONTROLLERS_WORKING_DIR', '/tmp/aircox')



import os
import stat

from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)

########################################################################
# Global & misc
########################################################################
# group to assign to users at their creation, along with the permissions
# to add to each group.
ensure('AIRCOX_DEFAULT_USER_GROUPS', {
    'Radio Hosts': (
        'change_program', 'change_diffusion',
        'change_sound',
        'add_track', 'change_track', 'delete_track',
        'add_tag', 'change_tag', 'delete_tag',
        'add_comment', 'edit_comment', 'delete_comment',
    ),
    # ensure user can log in using Wagtail
    'Editors': None,
    # ensure user can publish
    'Moderators': None,
})

# Directory for the programs data
ensure('AIRCOX_PROGRAMS_DIR',
       os.path.join(settings.MEDIA_ROOT, 'programs'))

# Directory for working data
ensure('AIRCOX_DATA_DIR',
       os.path.join(settings.PROJECT_ROOT, 'data'))


########################################################################
# Programs & Episodes
########################################################################
# default title for episodes
ensure('AIRCOX_EPISODE_TITLE', '{program.title} - {date}')
# date format in episode title (python's strftime)
ensure('AIRCOX_EPISODE_TITLE_DATE_FORMAT', '%-d %B %Y')

########################################################################
# Logs & Archives
########################################################################
# Directory where to save logs' archives
ensure('AIRCOX_LOGS_ARCHIVES_DIR',
       os.path.join(AIRCOX_DATA_DIR, 'archives')
)
# In days, minimal age of a log before it is archived
ensure('AIRCOX_LOGS_ARCHIVES_MIN_AGE', 60)


########################################################################
# Sounds
########################################################################
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


########################################################################
# Streamer & Controllers
########################################################################
# Controllers working directory
ensure('AIRCOX_CONTROLLERS_WORKING_DIR', '/tmp/aircox')


########################################################################
# Playlist import from CSV
########################################################################
# Columns for CSV file
ensure(
    'AIRCOX_IMPORT_PLAYLIST_CSV_COLS',
    ('artist', 'title', 'minutes', 'seconds', 'tags', 'info')
)
# Column delimiter of csv text files
ensure('AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER', ';')
# Text delimiter of csv text files
ensure('AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE', '"')




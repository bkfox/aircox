import os

from django.conf import settings


#class BaseSettings:
#    deprecated = set()
#
#    def __init__(self, user_conf):
#        if user_conf:
#            for key, value in user_conf.items():
#                if not hasattr(self, key):
#                    if key in self.deprecated:
#                        raise ValueError('"{}" config is deprecated'.format(key))
#                    else:
#                        raise ValueError('"{}" is not a config value'.format(key))
#                setattr(self, key, value)
#
#
#class Settings(BaseSettings):
#    default_user_groups = {
#
#    }
#
#    programs_dir = os.path.join(settings.MEDIA_ROOT, 'programs'),
#    """ Programs data directory. """
#    episode_title = '{program.title} - {date}'
#    """ Default episodes title. """
#    episode_title_date_format = '%-d %B %Y'
#    """ Date format used in episode title. """
#
#    logs_archives_dir = os.path.join(settings.PROJECT_ROOT, 'logs/archives')
#    """ Directory where logs are saved once archived """
#    logs_archive_age = 30
#    """ Default age of log before being archived """
#
#    sounds_default_dir = os.path.join(settings.MEDIA_ROOT, 'programs/defaults')
#    sound_archive_dir = 'archives'
#    sound_excerpt_dir = 'excerpts'
#    sound_quality = {
#        'attribute': 'RMS lev dB',
#        'range': (-18.0, -8.0),
#        'sample_length': 120,
#    }
#    sound_ext = ('.ogg', '.flac', '.wav', '.mp3', '.opus')
#
#    # TODO: move into aircox_streamer
#    streamer_working_dir = '/tmp/aircox'
#
#
#

def ensure(key, default):
    globals()[key] = getattr(settings, key, default)


########################################################################
# Global & misc
########################################################################
# group to assign to users at their creation, along with the permissions
# to add to each group.
ensure('AIRCOX_DEFAULT_USER_GROUPS', {
    'radio hosts': (
        # TODO include content_type in order to avoid clash with potential
        #      extra applications

        # aircox
        'change_program', 'change_episode', 'change_diffusion',
        'add_comment', 'change_comment', 'delete_comment',
        'add_article', 'change_article', 'delete_article',
        'change_sound',
        'add_track', 'change_track', 'delete_track',

        # taggit
        'add_tag', 'change_tag', 'delete_tag',

        # filer
        'add_folder', 'change_folder', 'delete_folder', 'can_use_directory_listing',
        'add_image', 'change_image', 'delete_image',
    ),
})

# Directory for the programs data
ensure('AIRCOX_PROGRAMS_DIR',
       os.path.join(settings.MEDIA_ROOT, 'programs'))


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
ensure('AIRCOX_LOGS_ARCHIVES_DIR', os.path.join(settings.PROJECT_ROOT, 'logs/archives'))
# In days, minimal age of a log before it is archived
ensure('AIRCOX_LOGS_ARCHIVES_AGE', 60)


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
    ('.ogg', '.flac', '.wav', '.mp3', '.opus')
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

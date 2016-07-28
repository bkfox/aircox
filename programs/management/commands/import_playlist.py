"""
Import one or more playlist for the given sound. Attach it to the sound
or to the related Diffusion if wanted.

Playlists are in CSV format, where columns are separated with a
'{settings.AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER}'. Text quote is
{settings.AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE}.
The order of the elements is: {settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS}

If 'minutes' or 'seconds' are given, position will be expressed as timed
position, instead of position in playlist.
"""
import os
import csv
import logging
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from aircox.programs.models import *
import aircox.programs.settings as settings
__doc__ = __doc__.format(settings = settings)

logger = logging.getLogger('aircox.tools')


class Importer:
    data = None
    tracks = None

    def __init__(self, related = None, path = None, save = False):
        if path:
            self.read(path)
            if related:
                self.make_playlist(related, save)

    def reset(self):
        self.data = None
        self.tracks = None

    def read(self, path):
        if not os.path.exists(path):
            return True
        with open(path, 'r') as file:
            self.data = list(csv.reader(
                file,
                delimiter = settings.AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER,
                quotechar = settings.AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE,
            ))

    def __get(self, line, field, default = None):
        maps = settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS
        if field not in maps:
            return default
        index = maps.index(field)
        return line[index] if index < len(line) else default

    def make_playlist(self, related, save = False):
        """
        Make a playlist from the read data, and return it. If save is
        true, save it into the database
        """
        maps = settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS
        tracks = []

        in_seconds = ('minutes' or 'seconds') in maps
        for index, line in enumerate(self.data):
            position = \
                int(self.__get(line, 'minutes', 0)) * 60 + \
                int(self.__get(line, 'seconds', 0)) \
                if in_seconds else index

            track, created = Track.objects.get_or_create(
                related_type = ContentType.objects.get_for_model(related),
                related_id = related.pk,
                title = self.__get(line, 'title'),
                artist = self.__get(line, 'artist'),
                position = position,
            )

            track.in_seconds = in_seconds
            track.info = self.__get(line, 'info')
            tags = self.__get(line, 'tags')
            if tags:
                track.tags.add(*tags.split(','))

            if save:
                track.save()
            tracks.append(track)
        self.tracks = tracks
        return tracks


class Command (BaseCommand):
    help= __doc__

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        now = tz.datetime.today()

        parser.add_argument(
            'path', metavar='PATH', type=str,
            help='path of the input playlist to read'
        )
        parser.add_argument(
            '--sound', '-s', type=str,
            help='generate a playlist for the sound of the given path. '
                 'If not given, try to match a sound with the same path.'
        )
        parser.add_argument(
            '--diffusion', '-d', action='store_true',
            help='try to get the diffusion relative to the sound if it exists'
        )

    def handle (self, path, *args, **options):
        # FIXME: absolute/relative path of sounds vs given path
        if options.get('sound'):
            related = Sound.objects.filter(
                path__icontains = options.get('sound')
            ).first()
        else:
            path, ext = os.path.splitext(options.get('path'))
            related = Sound.objects.filter(path__icontains = path).first()

        if not related:
            logger.error('no sound found in the database for the path ' \
                         '{path}'.format(path=path))
            return -1

        if options.get('diffusion') and related.diffusion:
            related = related.diffusion

        importer = Importer(related = related, path = path, save = True)
        for track in importer.tracks:
            logger.info('imported track at {pos}: {title}, by '
                        '{artist}'.format(
                    pos = track.position,
                    title = track.title, artist = track.artist
                )
            )


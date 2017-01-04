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

from aircox.models import *
import aircox.settings as settings
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
            self.data = list(csv.DictReader(
                (row for row in file if not row.startswith('#')),
                fieldnames = settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS,
                delimiter = settings.AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER,
                quotechar = settings.AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE,
            ))

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
                int(line.get('minute') or 0) * 60 + \
                int(line.get('seconds') or 0) \
                if in_seconds else index

            track, created = Track.objects.get_or_create(
                related_type = ContentType.objects.get_for_model(related),
                related_id = related.pk,
                title = line.get('title'),
                artist = line.get('artist'),
                position = position,
            )

            track.in_seconds = in_seconds
            track.info = line.get('info')
            tags = line.get('tags')
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
            path_, ext = os.path.splitext(path)
            related = Sound.objects.filter(path__icontains = path_).first()

        if not related:
            logger.error('no sound found in the database for the path ' \
                         '{path}'.format(path=path))
            return

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


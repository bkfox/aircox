"""
Import one or more playlist for the given sound. Attach it to the sound
or to the related Diffusion if wanted.

We support different formats:
- plain text: a track per line, where columns are separated with a
    '{settings.AIRCOX_IMPORT_PLAYLIST_PLAIN_DELIMITER}'.
    The order of the elements is: {settings.AIRCOX_IMPORT_PLAYLIST_PLAIN_COLS}
- csv: CSV file where columns are separated with a
    '{settings.AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER)}'. Text quote is
    {settings.AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE}.
    The order of the elements is: {settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS}

If 'minutes' or 'seconds' are given, position will be expressed as timed
position, instead of position in playlist.

Base the format detection using file extension. If '.csv', uses CSV importer,
otherwise plain text one.
"""
import os
import csv
import logging
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError

from aircox.programs.models import *
import aircox.programs.settings as settings
__doc__ = __doc__.format(settings)

logger = logging.getLogger('aircox.tools')


class Importer:
    type = None
    data = None
    tracks = None

    def __init__(self, related = None, path = None):
        if path:
            self.read(path)
            if related:
                self.make_playlist(related, True)

    def reset(self):
        self.type = None
        self.data = None
        self.tracks = None

    def read(self, path):
        if not os.path.exists(path):
            return True

        with open(path, 'r') as file:
            sp, *ext = os.path.splitext(path)[1]
            if ext[0] and ext[0] == 'csv':
                self.type = 'csv'
                self.data = csv.reader(
                    file,
                    delimiter = settings.AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER,
                    quotechar = settings.AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE,
                )
            else:
                self.type = 'plain'
                self.data = [
                    line.split(settings.AIRCOX_IMPORT_PLAYLIST_PLAIN_DELIMITER)
                    for line in file.readlines()
                ]

    def __get(self, line, field, default = None):
        maps = settings.AIRCOX_IMPORT_CSV_COLS
        if field not in maps:
            return default
        index = maps.index(field)
        return line[index] if index < len(line) else default

    def make_playlist(self, related, save = False):
        """
        Make a playlist from the read data, and return it. If save is
        true, save it into the database
        """
        maps = settings.AIRCOX_IMPORT_CSV_COLS if self.type == 'csv' else \
               settings.AIRCOX_IMPORT_PLAIN_COLS
        tracks = []

        for index, line in enumerate(self.data):
            if ('minutes' or 'seconds') in maps:
                kwargs['pos_in_secs'] = True
                kwargs['pos'] = int(self.__get(line, 'minutes', 0)) * 60 + \
                                int(self.__get(line, 'seconds', 0))
            else:
                kwargs['pos'] = index

            kwargs['related'] = related
            kwargs.update({
                k: self.__get(line, k) for k in maps
                if k not in ('minutes', 'seconds')
            })

            track = Track(**kwargs)
            # FIXME: bulk_create?
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
            'path', type=str,
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
            related = Sound.objects.filter(path__icontains = path).first()
        else:
            path, ext = os.path.splitext(options.get('path'))
            related = Sound.objects.filter(path__icontains = path).first()

        if not related:
            logger.error('no sound found in the database for the path ' \
                         '{path}'.format(path=path))
            return -1

        if options.get('diffusion') and related.diffusion:
            related = related.diffusion

        importer = Importer(related = related, path = path)
        for track in importer.tracks:
            logger.log('imported track at {pos}: {name}, by '
                       '{artist}'.format(
                    pos = track.pos,
                    name = track.name, artist = track.artist
                )
            )


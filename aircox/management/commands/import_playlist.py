"""
Import one or more playlist for the given sound. Attach it to the provided
sound.

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

from aircox import settings
from aircox.models import *

__doc__ = __doc__.format(settings=settings)

logger = logging.getLogger('aircox.commands')


class PlaylistImport:
    path = None
    data = None
    tracks = None
    track_kwargs = {}

    def __init__(self, path=None, **track_kwargs):
        self.path = path
        self.track_kwargs = track_kwargs

    def reset(self):
        self.data = None
        self.tracks = None

    def run(self):
        self.read()
        if self.track_kwargs.get('sound') is not None:
            self.make_playlist()

    def read(self):
        if not os.path.exists(self.path):
            return True
        with open(self.path, 'r') as file:
            logger.info('start reading csv ' + self.path)
            self.data = list(csv.DictReader(
                (row for row in file
                    if not (row.startswith('#') or row.startswith('\ufeff#'))
                    and row.strip()),
                fieldnames=settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS,
                delimiter=settings.AIRCOX_IMPORT_PLAYLIST_CSV_DELIMITER,
                quotechar=settings.AIRCOX_IMPORT_PLAYLIST_CSV_TEXT_QUOTE,
            ))

    def make_playlist(self):
        """
        Make a playlist from the read data, and return it. If save is
        true, save it into the database
        """
        if self.track_kwargs.get('sound') is None:
            logger.error('related track\'s sound is missing. Skip import of ' +
                         self.path + '.')
            return

        maps = settings.AIRCOX_IMPORT_PLAYLIST_CSV_COLS
        tracks = []

        logger.info('parse csv file ' + self.path)
        has_timestamp = ('minutes' or 'seconds') in maps
        for index, line in enumerate(self.data):
            if ('title' or 'artist') not in line:
                return
            try:
                timestamp = int(line.get('minutes') or 0) * 60 + \
                    int(line.get('seconds') or 0) \
                    if has_timestamp else None

                track, created = Track.objects.get_or_create(
                    title=line.get('title'),
                    artist=line.get('artist'),
                    position=index,
                    **self.track_kwargs
                )
                track.timestamp = timestamp
                print('track', track, timestamp)
                track.info = line.get('info')
                tags = line.get('tags')
                if tags:
                    track.tags.add(*tags.split(','))
            except Exception as err:
                logger.warning(
                    'an error occured for track {index}, it may not '
                    'have been saved: {err}'
                    .format(index=index, err=err)
                )
                continue

            track.save()
            tracks.append(track)
        self.tracks = tracks
        return tracks


class Command (BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        parser.add_argument(
            'path', metavar='PATH', type=str,
            help='path of the input playlist to read'
        )
        parser.add_argument(
            '--sound', '-s', type=str,
            help='generate a playlist for the sound of the given path. '
                 'If not given, try to match a sound with the same path.'
        )

    def handle(self, path, *args, **options):
        # FIXME: absolute/relative path of sounds vs given path
        if options.get('sound'):
            sound = Sound.objects.filter(path__icontains=options.get('sound'))\
                                 .first()
        else:
            path_, ext = os.path.splitext(path)
            sound = Sound.objects.filter(path__icontains=path_).first()

        if not sound:
            logger.error('no sound found in the database for the path '
                         '{path}'.format(path=path))
            return

        # FIXME: auto get sound.episode if any
        importer = PlaylistImport(path, sound=sound).run()
        for track in importer.tracks:
            logger.info('track #{pos} imported: {title}, by {artist}'.format(
                pos=track.position, title=track.title, artist=track.artist
            ))


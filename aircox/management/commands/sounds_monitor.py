#! /usr/bin/env python3

"""
Monitor sound files; For each program, check for:
- new files;
- deleted files;
- differences between files and sound;
- quality of the files;

It tries to parse the file name to get the date of the diffusion of an
episode and associate the file with it; We use the following format:
    yyyymmdd[_n][_][name]

Where:
    'yyyy' the year of the episode's diffusion;
    'mm' the month of the episode's diffusion;
    'dd' the day of the episode's diffusion;
    'n' the number of the episode (if multiple episodes);
    'name' the title of the sound;


To check quality of files, call the command sound_quality_check using the
parameters given by the setting AIRCOX_SOUND_QUALITY. This script requires
Sox (and soxi).
"""
from argparse import RawTextHelpFormatter
import concurrent.futures as futures
import datetime
import atexit
import logging
import os
import re
import time

import mutagen
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileModifiedEvent

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz
from django.utils.translation import gettext as _

from aircox import settings, utils
from aircox.models import Diffusion, Program, Sound, Track
from .import_playlist import PlaylistImport

logger = logging.getLogger('aircox.commands')


sound_path_re = re.compile(
    '^(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})'
    '(_(?P<hour>[0-9]{2})h(?P<minute>[0-9]{2}))?'
    '(_(?P<n>[0-9]+))?'
    '_?(?P<name>.*)$'
)


class SoundFile:
    path = None
    info = None
    path_info = None
    sound = None

    def __init__(self, path):
        self.path = path

    def sync(self, sound=None, program=None, deleted=False, **kwargs):
        """
        Update related sound model and save it.
        """
        if deleted:
            sound = Sound.objects.filter(path=self.path).first()
            if sound:
                sound.type = sound.TYPE_REMOVED
                sound.check_on_file()
                sound.save()
                return sound

        # FIXME: sound.program as not null
        program = kwargs['program'] = Program.get_from_path(self.path)
        sound, created = Sound.objects.get_or_create(path=self.path, defaults=kwargs) \
                         if not sound else (sound, False)

        sound.program = program
        if created or sound.check_on_file():
            logger.info('sound is new or have been modified -> %s', self.path)
            self.read_path()
            sound.name = self.path_info.get('name')

            self.read_file_info()
            if self.info is not None:
                sound.duration = utils.seconds_to_time(self.info.info.length)

        # check for episode
        if sound.episode is None and self.read_path():
            self.find_episode(program)

        self.sound = sound
        sound.save()
        if self.info is not None:
            self.find_playlist(sound)
        return sound

    def read_path(self):
        """
        Parse file name to get info on the assumption it has the correct
        format (given in Command.help). Return True if path contains informations.
        """
        if self.path_info:
            return 'year' in self.path_info

        name = os.path.splitext(os.path.basename(self.path))[0]
        match = sound_path_re.search(name)
        if match:
            self.path_info = match.groupdict()
            return True
        else:
            self.path_info = {'name': name}
            return False

    def read_file_info(self):
        """ Read file information and metadata. """
        if os.path.exists(self.path):
            self.info = mutagen.File(self.path)
        else:
            self.info = None

    def find_episode(self, program):
        """
        For a given program, check if there is an initial diffusion
        to associate to, using the date info we have. Update self.sound
        and save it consequently.

        We only allow initial diffusion since there should be no
        rerun.
        """
        pi = self.path_info
        if 'year' not in pi or not self.sound or self.sound.episode:
            return None

        if 'hour' not in pi:
            date = datetime.date(pi.get('year'), pi.get('month'), pi.get('day'))
        else:
            date = tz.datetime(pi.get('year'), pi.get('month'), pi.get('day'),
                               pi.get('hour') or 0, pi.get('minute') or 0)
            date = tz.get_current_timezone().localize(date)

        diffusion = program.diffusion_set.initial().at(date).first()
        if not diffusion:
            return None

        logger.info('%s <--> %s', self.sound.path, str(diffusion.episode))
        self.sound.episode = diffusion.episode
        return diffusion

    def find_playlist(self, sound=None, use_meta=True):
        """
        Find a playlist file corresponding to the sound path, such as:
            my_sound.ogg => my_sound.csv

        Use sound's file metadata if no corresponding playlist has been
        found and `use_meta` is True.
        """
        if sound is None:
            sound = self.sound

        if sound.track_set.count():
            return

        # import playlist
        path = os.path.splitext(self.sound.path)[0] + '.csv'
        if os.path.exists(path):
            PlaylistImport(path, sound=sound).run()
        # use metadata
        elif use_meta:
            if self.info is None:
                self.read_file_info()
            if self.info.tags:
                tags = self.info.tags
                info = '{} ({})'.format(tags.get('album'), tags.get('year')) \
                    if ('album' and 'year' in tags) else tags.get('album') \
                    if 'album' in tags else tags.get('year', '')

                track = Track(sound=sound,
                              position=int(tags.get('tracknumber', 0)),
                              title=tags.get('title', self.path_info['name']),
                              artist=tags.get('artist', _('unknown')),
                              info=info)
                track.save()


class MonitorHandler(PatternMatchingEventHandler):
    """
    Event handler for watchdog, in order to be used in monitoring.
    """
    pool = None

    def __init__(self, subdir, pool):
        """
        subdir: AIRCOX_SOUND_ARCHIVES_SUBDIR or AIRCOX_SOUND_EXCERPTS_SUBDIR
        """
        self.subdir = subdir
        self.pool = pool

        if self.subdir == settings.AIRCOX_SOUND_ARCHIVES_SUBDIR:
            self.sound_kwargs = {'type': Sound.TYPE_ARCHIVE}
        else:
            self.sound_kwargs = {'type': Sound.TYPE_EXCERPT}

        patterns = ['*/{}/*{}'.format(self.subdir, ext)
                    for ext in settings.AIRCOX_SOUND_FILE_EXT]
        super().__init__(patterns=patterns, ignore_directories=True)

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        logger.info('sound modified: %s', event.src_path)
        def updated(event, sound_kwargs):
            SoundFile(event.src_path).sync(**sound_kwargs)
        self.pool.submit(updated, event, self.sound_kwargs)

    def on_moved(self, event):
        logger.info('sound moved: %s -> %s', event.src_path, event.dest_path)
        def moved(event, sound_kwargs):
            sound = Sound.objects.filter(path=event.src_path)
            sound_file = SoundFile(event.dest_path) if not sound else sound
            sound_file.sync(**sound_kwargs)
        self.pool.submit(moved, event, self.sound_kwargs)

    def on_deleted(self, event):
        logger.info('sound deleted: %s', event.src_path)
        def deleted(event):
            SoundFile(event.src_path).sync(deleted=True)
        self.pool.submit(deleted, event.src_path)


class Command(BaseCommand):
    help = __doc__

    def report(self, program=None, component=None, *content):
        if not component:
            logger.info('%s: %s', str(program),
                        ' '.join([str(c) for c in content]))
        else:
            logger.info('%s, %s: %s', str(program), str(component),
                        ' '.join([str(c) for c in content]))

    def scan(self):
        """
        For all programs, scan dirs
        """
        logger.info('scan all programs...')
        programs = Program.objects.filter()

        dirs = []
        for program in programs:
            logger.info('#%d %s', program.id, program.title)
            self.scan_for_program(
                program, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR,
                type=Sound.TYPE_ARCHIVE,
            )
            self.scan_for_program(
                program, settings.AIRCOX_SOUND_EXCERPTS_SUBDIR,
                type=Sound.TYPE_EXCERPT,
            )
            dirs.append(os.path.join(program.path))

    def scan_for_program(self, program, subdir, **sound_kwargs):
        """
        Scan a given directory that is associated to the given program, and
        update sounds information.
        """
        logger.info('- %s/', subdir)
        if not program.ensure_dir(subdir):
            return

        subdir = os.path.join(program.path, subdir)
        sounds = []

        # sounds in directory
        for path in os.listdir(subdir):
            path = os.path.join(subdir, path)
            if not path.endswith(settings.AIRCOX_SOUND_FILE_EXT):
                continue

            sound_file = SoundFile(path)
            sound_file.sync(program=program, **sound_kwargs)
            sounds.append(sound_file.sound.pk)

        # sounds in db & unchecked
        sounds = Sound.objects.filter(path__startswith=subdir). \
            exclude(pk__in=sounds)
        self.check_sounds(sounds, program=program)

    def check_sounds(self, qs, **sync_kwargs):
        """ Only check for the sound existence or update """
        # check files
        for sound in qs:
            if sound.check_on_file():
                SoundFile(sound.path).sync(sound=sound, **sync_kwargs)

    def monitor(self):
        """ Run in monitor mode """
        with futures.ThreadPoolExecutor() as pool:
            archives_handler = MonitorHandler(settings.AIRCOX_SOUND_ARCHIVES_SUBDIR, pool)
            excerpts_handler = MonitorHandler(settings.AIRCOX_SOUND_EXCERPTS_SUBDIR, pool)

            observer = Observer()
            observer.schedule(archives_handler, settings.AIRCOX_PROGRAMS_DIR,
                              recursive=True)
            observer.schedule(excerpts_handler, settings.AIRCOX_PROGRAMS_DIR,
                              recursive=True)
            observer.start()

            def leave():
                observer.stop()
                observer.join()
            atexit.register(leave)

            while True:
                time.sleep(1)

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        parser.add_argument(
            '-q', '--quality_check', action='store_true',
            help='Enable quality check using sound_quality_check on all '
                 'sounds marqued as not good'
        )
        parser.add_argument(
            '-s', '--scan', action='store_true',
            help='Scan programs directories for changes, plus check for a '
                 ' matching diffusion on sounds that have not been yet assigned'
        )
        parser.add_argument(
            '-m', '--monitor', action='store_true',
            help='Run in monitor mode, watch for modification in the filesystem '
                 'and react in consequence'
        )

    def handle(self, *args, **options):
        if options.get('scan'):
            self.scan()
        #if options.get('quality_check'):
        #    self.check_quality(check=(not options.get('scan')))
        if options.get('monitor'):
            self.monitor()

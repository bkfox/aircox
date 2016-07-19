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
import os
import time
import re
import logging
import subprocess
from argparse import RawTextHelpFormatter
import atexit

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileModifiedEvent

from django.core.management.base import BaseCommand, CommandError

from aircox.programs.models import *
import aircox.programs.settings as settings
import aircox.programs.utils as utils

logger = logging.getLogger('aircox.tools')

class SoundInfo:
    name = ''
    sound = None

    year = None
    month = None
    day = None
    n = None
    duration = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        """
        Parse file name to get info on the assumption it has the correct
        format (given in Command.help)
        """
        file_name = os.path.basename(value)
        file_name = os.path.splitext(file_name)[0]
        r = re.search('^(?P<year>[0-9]{4})'
                      '(?P<month>[0-9]{2})'
                      '(?P<day>[0-9]{2})'
                      '(_(?P<n>[0-9]+))?'
                      '_?(?P<name>.*)$',
                      file_name)

        if not (r and r.groupdict()):
            r = { 'name': file_name }
            logger.info('file name can not be parsed -> %s', value)
        else:
            r = r.groupdict()

        self._path = value
        self.name = r['name'].replace('_', ' ').capitalize()
        self.year = int(r.get('year')) if 'year' in r else None
        self.month = int(r.get('month')) if 'month' in r else None
        self.day = int(r.get('day')) if 'day' in r else None
        self.n = r.get('n')
        return r

    def __init__(self, path = ''):
        self.path = path

    def get_duration(self):
        p = subprocess.Popen(['soxi', '-D', self.path],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if not err:
            duration = utils.seconds_to_time(int(float(out)))
            self.duration = duration
            return duration

    def get_sound(self, kwargs = None, save = True):
        """
        Get or create a sound using self info.

        If the sound is created/modified, get its duration and update it
        (if save is True, sync to DB), and check for a playlist file.
        """
        sound, created = Sound.objects.get_or_create(
            path = self.path,
            defaults = kwargs
        )
        if created or sound.check_on_file():
            logger.info('sound is new or have been modified -> %s', self.path)
            sound.duration = self.get_duration()
            sound.name = self.name
            if save:
                sound.save()
        self.sound = sound
        return sound

    def find_playlist(self, sound):
        """
        Find a playlist file corresponding to the sound path
        """
        import aircox.programs.management.commands.import_playlist \
                as import_playlist

        path = os.path.splitext(self.sound.path)[0] + '.csv'
        if not os.path.exists(path):
            return

        old = Track.get_for(object = sound)
        if old:
            return

        import_playlist.Importer(sound, path, save=True)

    def find_diffusion(self, program, save = True):
        """
        For a given program, check if there is an initial diffusion
        to associate to, using the date info we have. Update self.sound
        and save it consequently.

        We only allow initial diffusion since there should be no
        rerun.
        """
        if self.year == None or not self.sound or self.sound.diffusion:
            return;

        diffusion = Diffusion.objects.filter(
            program = program,
            initial__isnull = True,
            start__year = self.year,
            start__month = self.month,
            start__day = self.day,
        )
        if not diffusion:
            return
        diffusion = diffusion[0]

        logger.info('diffusion %s mathes to sound -> %s', str(diffusion),
                    sound.path)
        self.sound.diffusion = diffusion
        if save:
            self.sound.save()
        return diffusion


class MonitorHandler(PatternMatchingEventHandler):
    """
    Event handler for watchdog, in order to be used in monitoring.
    """
    def __init__(self, subdir):
        """
        subdir: AIRCOX_SOUND_ARCHIVES_SUBDIR or AIRCOX_SOUND_EXCERPTS_SUBDIR
        """
        self.subdir = subdir
        if self.subdir == settings.AIRCOX_SOUND_ARCHIVES_SUBDIR:
            self.sound_kwargs = { 'type': Sound.Type.archive }
        else:
            self.sound_kwargs = { 'type': Sound.Type.excerpt }

        patterns = ['*/{}/*{}'.format(self.subdir, ext)
                    for ext in settings.AIRCOX_SOUND_FILE_EXT ]
        super().__init__(patterns=patterns, ignore_directories=True)

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        logger.info('sound modified: %s', event.src_path)
        program = Program.get_from_path(event.src_path)
        if not program:
            return

        si = SoundInfo(event.src_path)
        si.get_sound(self.sound_kwargs, True)
        if si.year != None:
            si.find_diffusion(program)

    def on_deleted(self, event):
        logger.info('sound deleted: %s', event.src_path)
        sound = Sound.objects.filter(path = event.src_path)
        if sound:
            sound = sound[0]
            sound.removed = True
            sound.save()

    def on_moved(self, event):
        logger.info('sound moved: %s -> %s', event.src_path, event.dest_path)
        sound = Sound.objects.filter(path = event.src_path)
        if not sound:
            self.on_modified(
                FileModifiedEvent(event.dest_path)
            )
            return

        sound = sound[0]
        sound.path = event.dest_path
        sound.save()


class Command(BaseCommand):
    help= __doc__

    def report(self, program = None, component = None, *content):
        if not component:
            logger.info('%s: %s', str(program), ' '.join([str(c) for c in content]))
        else:
            logger.info('%s, %s: %s', str(program), str(component),
                        ' '.join([str(c) for c in content]))

    def add_arguments(self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            '-q', '--quality_check', action='store_true',
            help='Enable quality check using sound_quality_check on all ' \
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
        if options.get('quality_check'):
            self.check_quality(check = (not options.get('scan')) )
        if options.get('monitor'):
            self.monitor()

    @staticmethod
    def check_sounds(qs):
        """
        Only check for the sound existence or update
        """
        # check files
        for sound in qs:
            if sound.check_on_file():
                sound.save(check = False)

    def scan(self):
        """
        For all programs, scan dirs
        """
        logger.info('scan all programs...')
        programs = Program.objects.filter()

        for program in programs:
            logger.info('#%d %s', program.id, program.name)
            self.scan_for_program(
                program, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR,
                type = Sound.Type.archive,
            )
            self.scan_for_program(
                program, settings.AIRCOX_SOUND_EXCERPTS_SUBDIR,
                type = Sound.Type.excerpt,
            )

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
            print(path)
            path = os.path.join(subdir, path)
            if not path.endswith(settings.AIRCOX_SOUND_FILE_EXT):
                continue

            si = SoundInfo(path)
            si.get_sound(sound_kwargs, True)
            si.find_diffusion(program)
            si.find_playlist(si.sound)
            sounds.append(si.sound.pk)

        # sounds in db & unchecked
        sounds = Sound.objects.filter(path__startswith = subdir). \
                               exclude(pk__in = sounds)
        self.check_sounds(sounds)

    def check_quality(self, check = False):
        """
        Check all files where quality has been set to bad
        """
        import aircox.programs.management.commands.sounds_quality_check \
                as quality_check

        sounds = Sound.objects.filter(good_quality = False)
        if check:
            self.check_sounds(sounds)
            files = [ sound.path for sound in sounds
                        if not sound.removed and os.path.exists(sound.path) ]
        else:
            files = [ sound.path for sound in sounds.filter(removed = False)
                        if os.path.exists(sound.path) ]

        logger.info('quality check...',)
        cmd = quality_check.Command()
        cmd.handle( files = files,
                    **settings.AIRCOX_SOUND_QUALITY )

        logger.info('update database')
        def update_stats(sound_info, sound):
            stats = sound_info.get_file_stats()
            if stats:
                duration = int(stats.get('length'))
                sound.duration = utils.seconds_to_time(duration)

        for sound_info in cmd.good:
            sound = Sound.objects.get(path = sound_info.path)
            sound.good_quality = True
            update_stats(sound_info, sound)
            sound.save(check = False)

        for sound_info in cmd.bad:
            sound = Sound.objects.get(path = sound_info.path)
            update_stats(sound_info, sound)
            sound.save(check = False)

    def monitor(self):
        """
        Run in monitor mode
        """
        archives_handler = MonitorHandler(
            subdir = settings.AIRCOX_SOUND_ARCHIVES_SUBDIR
        )
        excerpts_handler = MonitorHandler(
            subdir = settings.AIRCOX_SOUND_EXCERPTS_SUBDIR
        )

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



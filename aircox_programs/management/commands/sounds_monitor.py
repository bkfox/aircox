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
import re
import subprocess
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError

from aircox_programs.models import *
import aircox_programs.settings as settings
import aircox_programs.utils as utils


class Command (BaseCommand):
    help= __doc__

    def report (self, program = None, component = None, *content):
        if not component:
            print('{}: '.format(program), *content)
        else:
            print('{}, {}: '.format(program, component), *content)

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            '-q', '--quality_check', action='store_true',
            help='Enable quality check using sound_quality_check on all ' \
                 'sounds marqued as not good'
        )
        parser.add_argument(
            '-s', '--scan', action='store_true',
            help='Scan programs directories for changes, plus check for a '
                 ' matching episode on sounds that have not been yet assigned'
        )

    def handle (self, *args, **options):
        if options.get('scan'):
            self.scan()
        if options.get('quality_check'):
            self.check_quality(check = (not options.get('scan')) )

    def _get_duration (self, path):
        p = subprocess.Popen(['soxi', '-D', path], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if not err:
            return utils.seconds_to_time(int(float(out)))

    def get_sound_info (self, program, path):
        """
        Parse file name to get info on the assumption it has the correct
        format (given in Command.help)
        """
        file_name = os.path.basename(path)
        file_name = os.path.splitext(file_name)[0]
        r = re.search('^(?P<year>[0-9]{4})'
                      '(?P<month>[0-9]{2})'
                      '(?P<day>[0-9]{2})'
                      '(_(?P<n>[0-9]+))?'
                      '_?(?P<name>.*)$',
                      file_name)

        if not (r and r.groupdict()):
            self.report(program, path, "file path is not correct, use defaults")
            r = {
                'name': file_name
            }
        else:
            r = r.groupdict()

        r['duration'] = self._get_duration(path)
        r['name'] = r['name'].replace('_', ' ').capitalize()
        r['path'] = path
        return r

    def find_initial (self, program, sound_info):
        """
        For a given program, and sound path check if there is an initial
        diffusion to associate to, using the diffusion's date.

        If there is no matching episode, return None.
        """
        # check on episodes
        diffusion = Diffusion.objects.filter(
            program = program,
            date__year = int(sound_info['year']),
            date__month = int(sound_info['month']),
            date__day = int(sound_info['day'])
        )

        if not diffusion.count():
            self.report(program, sound_info['path'],
                        'no diffusion found for the given date')
            return
        return diffusion[0]

    @staticmethod
    def check_sounds (qs):
        """
        Only check for the sound existence or update
        """
        # check files
        for sound in qs:
            if sound.check_on_file():
                sound.save(check = False)

    def scan (self):
        """
        For all programs, scan dirs
        """
        print('scan files for all programs...')
        programs = Program.objects.filter()

        for program in programs:
            print('- program', program.name)
            self.scan_for_program(
                program, settings.AIRCOX_SOUND_ARCHIVES_SUBDIR,
                type = Sound.Type['archive'],
            )
            self.scan_for_program(
                program, settings.AIRCOX_SOUND_EXCERPTS_SUBDIR,
                type = Sound.Type['excerpt'],
            )

    def scan_for_program (self, program, subdir, **sound_kwargs):
        """
        Scan a given directory that is associated to the given program, and
        update sounds information.
        """
        print(' - scan files in', subdir)
        if not program.ensure_dir(subdir):
            return

        subdir = os.path.join(program.path, subdir)

        # new/existing sounds
        for path in os.listdir(subdir):
            path = os.path.join(subdir, path)
            if not path.endswith(settings.AIRCOX_SOUND_FILE_EXT):
                continue

            sound_info = self.get_sound_info(program, path)
            sound = Sound.objects.get_or_create(
                path = path,
                defaults = { 'name': sound_info['name'],
                             'duration': sound_info['duration'] or None }
            )[0]
            sound.__dict__.update(sound_kwargs)
            sound.save(check = False)

            # initial diffusion association
            if 'year' in sound_info:
                initial = self.find_initial(program, sound_info)
                if initial:
                    if initial.initial:
                        # FIXME: allow user to overwrite rerun info?
                        self.report(program, path,
                                    'the diffusion must be an initial diffusion')
                    else:
                        sound = initial.sounds.get_queryset() \
                                    .filter(path == sound.path)
                        if not sound:
                            self.report(program, path,
                                        'add sound to diffusion ', initial.id)
                            initial.sounds.add(sound)
                            initial.save()

        self.check_sounds(Sound.objects.filter(path__startswith = subdir))

    def check_quality (self, check = False):
        """
        Check all files where quality has been set to bad
        """
        import aircox_programs.management.commands.sounds_quality_check \
                as quality_check

        sounds = Sound.objects.filter(good_quality = False)
        if check:
            self.check_sounds(sounds)
            files = [ sound.path for sound in sounds if not sound.removed ]
        else:
            files = [ sound.path for sound in sounds.filter(removed = False) ]

        print('start quality check...')
        cmd = quality_check.Command()
        cmd.handle( files = files,
                    **settings.AIRCOX_SOUND_QUALITY )

        print('- update sounds in database')
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


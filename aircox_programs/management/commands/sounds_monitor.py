"""
Monitor sound files; For each program, check for:
- new files;
- deleted files;
- differences between files and sound;
- quality of the files;

It tries to parse the file name to get the date of the diffusion of an
episode and associate the file with it; We use the following format:
    yyyymmdd[_n][_][title]

Where:
    'yyyy' is the year of the episode's diffusion;
    'mm' is the month of the episode's diffusion;
    'dd' is the day of the episode's diffusion;
    'n' is the number of the episode (if multiple episodes);
    'title' the title of the sound;


To check quality of files, call the command sound_quality_check using the
parameters given by the setting AIRCOX_SOUND_QUALITY.
"""
import os
import re
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from aircox_programs.models import *
import aircox_programs.settings as settings


class Command (BaseCommand):
    help= __doc__

    def report (self, program = None, component = None, *content):
        if not component:
            print('{}: '.format(program), *content)
        else:
            print('{}, {}: '.format(program, component), *content)

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter

    def handle (self, *args, **options):
        programs = Program.objects.filter()

        for program in programs:
            path = lambda x: os.path.join(program.path, x)
            self.check_files(
                program, path(settings.AIRCOX_SOUND_ARCHIVES_SUBDIR),
                archive = True,
            )
            self.check_files(
                program, path(settings.AIRCOX_SOUND_EXCERPTS_SUBDIR),
                excerpt = True,
            )

        self.check_quality()

    def get_sound_info (self, path):
        """
        Parse file name to get info on the assumption it has the correct
        format (given in Command.help)
        """
        r = re.search('^(?P<year>[0-9]{4})'
                      '(?P<month>[0-9]{2})'
                      '(?P<day>[0-9]{2})'
                      '(_(?P<n>[0-9]+))?'
                      '_?(?P<name>.*)\.\w+$',
                      os.path.basename(path))

        if not (r and r.groupdict()):
            self.report(program, path, "file path is not correct, use defaults")
            r = {
                'name': os.path.splitext(path)
            }
        r['path'] = path
        return r

    def ensure_sound (self, sound_info):
        """
        Return the Sound for the given sound_info; If not found, create it
        without saving it.
        """
        sound = Sound.objects.filter(path = path)
        if sound:
            sound = sound[0]
        else:
            sound = Sound(path = path, title = sound_info['name'])

    def find_episode (self, program, sound_info):
        """
        For a given program, and sound path check if there is an episode to
        associate to, using the diffusion's date.

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
            self.report(program, path, 'no diffusion found for the given date')
            return
        diffusion = diffusion[0]
        return diffusion.episode or None


    def check_files (self, program, dir_path, **sound_kwargs):
        """
        Scan a given directory that is associated to the given program, and
        update sounds information.
        """
        if not os.path.exists(dir_path):
            return

        # new/existing sounds
        for path in os.listdir(dir_path):
            path = dir_path + '/' + path
            if not path.endswith(settings.AIRCOX_SOUNDFILE_EXT):
                continue

            sound_info = self.get_sound_info(path)
            sound = self.ensure_sound(sound_info)
            sound.__dict__.update(sound_kwargs)
            sound.save(check = False)

            # episode and relation
            if 'year' in sound_info:
                episode = self.find_episode(program, sound_info)
                if episode:
                    for sound_ in episode.sounds.get_queryset():
                        if sound_.path == sound.path:
                            break
                    else:
                        self.report(program, path, 'add sound to episode ',
                                    episode.id)
                        episode.sounds.add(sound)
                        episode.save()

        # check files
        for sound in Sound.object.filter(path__startswith = path):
            if sound.check():
                sound.save(check = False)


    def check_quality (self):
        """
        Check all files where quality has been set to bad
        """



import os
import re

from django.core.management.base    import BaseCommand, CommandError
from django.utils                   import timezone
from programs.models                import *
import programs.settings            as settings


class Command (BaseCommand):
    help= "Take a look at the programs directory to check on new podcasts"


    def report (self, program = None, component = None, *content):
        if not component:
            print('{}: '.format(program), *content)
        else:
            print('{}, {}: '.format(program, component), *content)


    def handle (self, *args, **options):
        programs = Program.objects.filter()

        for program in programs:
            self.scan_dir(program, program.path + '/public', public = True)
            self.scan_dir(program, program.path + '/podcasts', embed = True)
            self.scan_dir(program, program.path + '/private')


    def ensure_episode (self, program, sound):
        """
        For a given program, check if there is an episode to associate to.
        This makes the assumption that the name of the file has the following
        format:
            yyyymmdd[_n][_][title]

            Where:
            yyyy: is the year of the episode's diffusion
            mm: is the month of the episode's diffusion
            dd: is the day of the episode's diffusion
            n: is the number of the episode (if multiple episodes)

        We check against the diffusion rather than the episode's date, because
        this is the diffusion that defines when the sound will be podcasted for
        the first time.

        We create the episode if it does not exists only if there is a diffusion
        matching the date of the sound, in order to respect the hierarchy of
        episode creation.

        We dont create episode if it does not exists, because only episodes must
        be created through diffusions

        TODO: multiple diffusions at the same date
        """
        path = os.path.basename(sound.path)
        r = re.search('^(?P<year>[0-9]{4})'
                       '(?P<month>[0-9]{2})'
                       '(?P<day>[0-9]{2})'
                       '(_(?P<n>[0-9]+))?'
                       '_?(?P<name>.*)\.\w+$'
                     , path)

        if not r:
            return
        r = r.groupdict()

        # check on episodes
        diffusion = Diffusion.objects.filter( program = program
                                            , date__year = int(r['year'])
                                            , date__month = int(r['month'])
                                            , date__day = int(r['day'])
                                            )
        if not diffusion.count():
            self.report(program, path, 'no diffusion found for the given date')
            return

        diffusion = diffusion[0]
        if diffusion.episode:
            return diffusion.episode

        episode = Episode( parent = program
                         , title = r.get('name') \
                                    .replace('_', ' ') \
                                    .capitalize()
                         , date = diffusion.date
                         )
        episode.save()
        if program.tags.all():
            episode.tags.add(program.tags.all())
        self.report(program, path, 'episode does not exist, create')
        return episode


    def scan_dir (self, program, dir_path, public = False, embed = False):
        """
        Scan a given directory that is associated to the given program, and
        update sounds information

        Return a list of scanned sounds
        """
        if not os.path.exists(dir_path):
            return

        paths = []
        for path in os.listdir(dir_path):
            path = dir_path + '/' + path
            if not path.endswith(settings.AIRCOX_SOUNDFILE_EXT):
                continue

            paths.append(path)

            # check for new sound files or update
            sound = Sound.objects.filter(path = path)
            if sound.count():
                sound = sound[0]
            else:
                sound = Sound(path = path)

            # check for the corresponding episode:
            episode = self.ensure_episode(program, sound)
            if not episode:
                continue

            sound.save()

            for sound_ in episode.sounds.get_queryset():
                if sound_.path == sound.path:
                    continue

            self.report(program, path, 'associate sound to episode '
                       , episode.id)
            episode.sounds.add(sound)

        return paths


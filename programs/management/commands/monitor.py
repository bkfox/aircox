import os

from django.core.management.base           import BaseCommand, CommandError
import programs.models                     as models
import programs.settings


class Command (BaseCommand):
    help= "Take a look at the programs directory to check on new podcasts"


    def handle (self, *args, **options):
        programs = models.Program.objects.filter(schedule__isnull = True)

        for program in programs:
            self.scan(program, program.path + '/public', public = True)
            self.scan(program, program.path + '/podcasts', embed = True)
            self.scan(program, program.path + '/private')


    def scan (self, program, path, public = False, embed = False):
        try:
            for filename in os.listdir(path):
                long_filename = path + '/' + filename

                # check for new sound files
                # stat the sound files
                # match sound files against episodes - if not found, create it
                # upload public podcasts to mixcloud if required
        except:
            pass


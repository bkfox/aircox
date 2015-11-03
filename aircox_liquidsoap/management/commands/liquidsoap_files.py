"""
Generate configuration files and playlists for liquidsoap using settings, streams and
so on
"""
import os
import re
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.views.generic.base import View
from django.template.loader import render_to_string

import aircox_liquidsoap.settings as settings
import aircox_programs.models as models



class Command (BaseCommand):
    help= __doc__
    output_dir = settings.AIRCOX_LIQUIDSOAP_MEDIA

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            'output', metavar='PATH', type=str, nargs='?',
            help='force output to file (- to stdout) for single actions; to a '
                 'given dir when using --all')
        parser.add_argument(
            '-c', '--config', action='store_true',
            help='Generate liquidsoap config file'
        )
        parser.add_argument(
            '-s', '--stream', type=int,
            help='Generate the playlist of a stream with the given id'
        )
        parser.add_argument(
            '-S', '--streams', action='store_true',
            help='Generate all playlists'
        )
        parser.add_argument(
            '-a', '--all', action='store_true',
            help='Generate all playlists and config file'
        )

    def handle (self, *args, **options):
        output = options.get('output') or None
        if options.get('config'):
            data = self.get_config(output = output)
            return

        if options.get('stream'):
            stream = options['stream']
            if type(stream) is int:
                stream = models.Stream.objects.get(id = stream)

            data = self.get_playlist(stream, output = output)
            return

        if options.get('all') or options.get('streams'):
            if output:
                if not os.path.isdir(output):
                    raise CommandError('given output is not a directory')
                self.output_dir = output

            if options.get('all'):
                self.handle(config = True)

            for stream in models.Stream.objects.filter(active = True):
                self.handle(stream = stream)
            self.output_dir = settings.AIRCOX_LIQUIDSOAP_MEDIA
            return

        raise CommandError('nothing to do')

    def print (self, data, path, default):
        if path and path == '-':
            print(data)
            return

        if not path:
            path = os.path.join(self.output_dir, default)
        with open(path, 'w+') as file:
            file.write(data)

    @staticmethod
    def __render_stream_in_radio (stream):
        if stream.time_start and stream.time_end:
            data = '({}-{}, {})'.format(
                stream.time_start.strftime('%Hh%M'),
                stream.time_end.strftime('%Hh%M'),
                stream.get_slug_name()
            )
        else:
            data = stream.get_slug_name()

        if stream.delay:
            data = 'delay({}., {})'.format(
                    stream.delay.strftime('%s'),
                    data
                )
        return data

    def get_config (self, output = None):
        streams = models.Stream.objects.filter(active = True).order_by('type')[:]
        for stream in streams:
            stream.render_in_radio = self.__render_stream_in_radio(stream)

        context = {
            'streams': streams,
            'settings': settings,
        }

        data = render_to_string('aircox_liquidsoap/config.liq', context)
        data = re.sub(r'\\\n', r'#\\n#', data)
        data = data.replace('\n', '')
        data = re.sub(r'#\\n#', '\n', data)
        self.print(data, output, 'aircox.liq')

    def get_playlist (self, stream, output = None):
        data = '/media/data/musique/free/Professor Kliq -- 28 Days With The OP-1' \
               '-- jm148689/1_Coffee.ogg\n'
        self.print(data, output, 'stream_{}.m3u'.format(stream.pk))




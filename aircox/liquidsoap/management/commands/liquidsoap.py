"""
Main tool to work with liquidsoap. We can:
- monitor Liquidsoap's sources and do logs, print what's on air.
- generate configuration files and playlists for a given station
"""
import os
import time
import re
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils import timezone as tz

import aircox.programs.models as models
import aircox.programs.settings as programs_settings

import aircox.liquidsoap.settings as settings
import aircox.liquidsoap.utils as utils


class StationConfig:
    controller = None

    def __init__ (self, station):
        self.controller = utils.Controller(station, False)

    def handle (self, options):
        if options.get('config') or options.get('all'):
            self.make_config()
        if options.get('streams') or options.get('all'):
            self.make_playlists()

    def make_config (self):
        context = {
            'controller': self.controller,
            'settings': settings,
        }

        data = render_to_string('aircox_liquidsoap/station.liq', context)
        data = re.sub(r'\s*\\\n', r'#\\n#', data)
        data = data.replace('\n', '')
        data = re.sub(r'#\\n#', '\n', data)
        with open(self.controller.config_path, 'w+') as file:
            file.write(data)

    def make_playlists (self):
        for stream in self.controller.streams.values():
            program = stream.program

            sounds = models.Sound.objects.filter(
                # good_quality = True,
                type = models.Sound.Type['archive'],
                path__startswith = os.path.join(
                    programs_settings.AIRCOX_SOUND_ARCHIVES_SUBDIR,
                    program.path
                )
            )
            with open(stream.path, 'w+') as file:
                file.write('\n'.join(sound.path for sound in sounds))


class Command (BaseCommand):
    help= __doc__
    output_dir = settings.AIRCOX_LIQUIDSOAP_MEDIA

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter

        group = parser.add_argument_group('monitor')
        group.add_argument(
            '-o', '--on_air', action='store_true',
            help='print what is on air'
        )
        group.add_argument(
            '-m', '--monitor', action='store_true',
            help='run in monitor mode'
        )
        group.add_argument(
            '-d', '--delay', type=int,
            default=1000,
            help='time to sleep in milliseconds before update on monitor'
        )

        group = parser.add_argument_group('configuration')
        parser.add_argument(
            '-s', '--station', type=int,
            help='generate files for the given station (if not set, do it for'
                 ' all available stations)'
        )
        parser.add_argument(
            '-c', '--config', action='store_true',
            help='generate liquidsoap config file'
        )
        parser.add_argument(
            '-S', '--streams', action='store_true',
            help='generate all stream playlists'
        )
        parser.add_argument(
            '-a', '--all', action='store_true',
            help='shortcut for -cS'
        )


    def handle (self, *args, **options):
        if options.get('station'):
            station = models.Station.objects.get(id = options.get('station'))
            StationConfig(station).handle(options)
        elif options.get('all') or options.get('config') or \
                options.get('streams'):
            for station in models.Station.objects.filter(active = True):
                StationConfig(station).handle(options)

        if options.get('on_air') or options.get('monitor'):
            self.handle_monitor(options)

    def handle_monitor (self, options):
        self.monitor = utils.Monitor()
        self.monitor.update()

        if options.get('on_air'):
            for id, controller in self.monitor.controller.items():
                print(id, controller.on_air)
            return

        if options.get('monitor'):
            delay = options.get('delay') / 1000
            while True:
                for controller in self.monitor.controllers.values():
                    controller.monitor()
                time.sleep(delay)
            return



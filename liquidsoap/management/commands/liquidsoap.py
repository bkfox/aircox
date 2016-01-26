"""
Main tool to work with liquidsoap. We can:
- monitor Liquidsoap's sources and do logs, print what's on air.
- generate configuration files and playlists for a given station
"""
import os
import time
import re
import subprocess
import atexit
from argparse import RawTextHelpFormatter

from django.conf import settings as main_settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils import timezone as tz

import aircox.programs.models as programs
import aircox.programs.settings as programs_settings
from aircox.programs.utils import to_timedelta

import aircox.liquidsoap.settings as settings
import aircox.liquidsoap.utils as utils


class StationConfig:
    """
    Configuration and playlist generator for a station.
    """
    controller = None
    process = None

    def __init__ (self, station):
        self.controller = utils.Controller(station, False)

    def handle (self, options):
        os.makedirs(self.controller.path, exist_ok = True)
        if options.get('config') or options.get('all'):
            self.make_config()
        if options.get('streams') or options.get('all'):
            self.make_playlists()

    def make_config (self):
        log_script = main_settings.BASE_DIR \
                     if hasattr(main_settings, 'BASE_DIR') else \
                     main_settings.PROJECT_ROOT
        log_script = os.path.join(log_script, 'manage.py') + \
                        ' liquidsoap_log'

        context = {
            'controller': self.controller,
            'settings': settings,
            'log_script': log_script,
        }

        data = render_to_string('aircox/liquidsoap/station.liq', context)
        data = re.sub(r'\s*\\\n', r'#\\n#', data)
        data = data.replace('\n', '')
        data = re.sub(r'#\\n#', '\n', data)
        with open(self.controller.config_path, 'w+') as file:
            file.write(data)

    def make_playlists (self):
        for stream in self.controller.streams.values():
            program = stream.program

            sounds = programs.Sound.objects.filter(
                # good_quality = True,
                type = programs.Sound.Type['archive'],
                path__startswith = os.path.join(
                    programs_settings.AIRCOX_SOUND_ARCHIVES_SUBDIR,
                    program.path
                )
            )
            with open(stream.path, 'w+') as file:
                file.write('\n'.join(sound.path for sound in sounds))

    def run (self):
        """
        Run subprocess in background, register a terminate handler, and
        return process instance.
        """
        self.process = \
            subprocess.Popen(['liquidsoap', '-v', self.controller.config_path],
                             stderr=subprocess.STDOUT)
        atexit.register(self.process.terminate)
        return self.process


class Monitor:
    @classmethod
    def run (cl, controller):
        """
        Run once the monitor on the controller
        """
        if not controller.connector.available and controller.connector.open():
            return

        cl.run_source(controller.master)
        cl.run_dealer(controller)

        for stream in controller.streams.values():
            cl.run_source(stream)

    @staticmethod
    def log (**kwargs):
        """
        Create a log using **kwargs, and print info
        """
        log = programs.Log(**kwargs)
        log.save()
        log.print()

    @staticmethod
    def expected_diffusion (station, date, on_air):
        """
        Return which diffusion should be played now and is not playing
        on the given station.
        """
        r = [ programs.Diffusion.get_prev(station, date),
              programs.Diffusion.get_next(station, date) ]
        r = [ diffusion.prefetch_related('sounds')[0]
                for diffusion in r if diffusion.count() ]

        for diffusion in r:
            if diffusion.end < date:
                continue

            diffusion.playlist = [ sound.path
                                   for sound in diffusion.get_archives() ]
            if diffusion.playlist and on_air not in diffusion.playlist:
                return diffusion

    @classmethod
    def run_dealer (cl, controller):
        """
        Monitor dealer playlist (if it is time to load) and whether it is time
        to trigger the button to start a diffusion.
        """
        dealer = controller.dealer
        playlist = dealer.playlist
        on_air = dealer.current_sound
        now = tz.make_aware(tz.datetime.now())

        diff = cl.expected_diffusion(controller.station, now, on_air)
        if not diff:
            return # there is nothing we can do

        # playlist reload
        if dealer.playlist != diff.playlist:
            if not playlist or on_air == playlist[-1] or \
                on_air not in playlist:
                dealer.on = False
                dealer.playlist = diff.playlist

        # run the diff
        if dealer.playlist == diff.playlist and diff.start <= now and not dealer.on:
            dealer.on = True
            for source in controller.streams.values():
                source.skip()
            cl.log(
                source = dealer.id,
                date = now,
                comment = 'trigger the scheduled diffusion to liquidsoap; '
                          'skip all other streams',
                related_object = diff,
            )

    @classmethod
    def run_source (cl, source):
        """
        Keep trace of played sounds on the given source. For the moment we only
        keep track of known sounds.
        """
        # TODO: repetition of the same sound out of an interval of time
        last_log = programs.Log.objects.filter(
            source = source.id,
        ).prefetch_related('related_object').order_by('-date')

        on_air = source.current_sound
        if not on_air:
            return

        if last_log:
            now = tz.datetime.now()
            last_log = last_log[0]
            last_obj = last_log.related_object
            if type(last_obj) == programs.Sound and on_air == last_obj.path:
                if not last_obj.duration or \
                        now < log.date + programs_utils.to_timedelta(last_obj.duration):
                    return

        sound = programs.Sound.objects.filter(path = on_air)
        if not sound:
            return

        sound = sound[0]
        cl.log(
            source = source.id,
            date = tz.make_aware(tz.datetime.now()),
            comment = 'sound has changed',
            related_object = sound or None,
        )


class Command (BaseCommand):
    help= __doc__
    output_dir = settings.AIRCOX_LIQUIDSOAP_MEDIA

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            '-e', '--exec', action='store_true',
            help='run liquidsoap on exit'
        )

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
        group.add_argument(
            '-s', '--station', type=int,
            help='generate files for the given station'
        )
        group.add_argument(
            '-a', '--all', action='store_true',
            help='generate files for all stations'
        )
        group.add_argument(
            '-c', '--config', action='store_true',
            help='generate liquidsoap config file'
        )
        group.add_argument(
            '-S', '--streams', action='store_true',
            help='generate all stream playlists'
        )
        group.add_argument(
            '-r', '--run', action='store_true',
            help='run liquidsoap with the generated configuration'
        )

    def handle (self, *args, **options):
        stations = []
        if options.get('station'):
            stations = [ StationConfig(
                            programs.Station.objects.get(
                                id = options.get('station')
                            )) ]
        elif options.get('all') or options.get('config') or \
                options.get('streams'):
            stations = [ StationConfig(station)
                            for station in \
                                programs.Station.objects.filter(active = True)
                       ]

        run = options.get('run')
        for station in stations:
            station.handle(options)
            if run:
                station.run()

        if options.get('on_air') or options.get('monitor'):
            self.handle_monitor(options)

        if run:
            for station in stations:
                station.process.wait()


    def handle_monitor (self, options):
        controllers = [
            utils.Controller(station)
            for station in programs.Station.objects.filter(active = True)
        ]
        for controller in controllers:
            controller.update()

        if options.get('on_air'):
            for controller in controllers:
                print(controller.id, controller.on_air)
            return

        if options.get('monitor'):
            delay = options.get('delay') / 1000
            while True:
                for controller in controllers:
                    #try:
                    Monitor.run(controller)
                    #except Exception as err:
                    # print(err)
                time.sleep(delay)
            return



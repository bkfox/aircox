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
        cl.run_source(controller.dealer)

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

    @classmethod
    def __get_prev_diff(cl, source, played_sounds = True):
        diff_logs = programs.Log.get_for_related_model(programs.Diffusion) \
                        .filter(source = source.id) \
                        .order_by('-date')
        if played_sounds:
            sound_logs = programs.Log.get_for_related_model(programs.Sound) \
                            .filter(source = source.id) \
                            .order_by('-date')
        if not diff_logs:
            return

        diff = diff_logs[0].related_object
        playlist = diff.playlist
        if played_sounds:
            diff.played = [ sound.related_object.path
                            for sound in sound_logs[0:len(playlist)] ]
        return diff

    @classmethod
    def run_dealer(cl, controller):
        # - this function must recover last state in case of crash
        #   -> don't store data out of hdd
        # - construct gradually the playlist and update it if needed
        #   -> we force liquidsoap to preload tracks of next diff
        # - dealer.on while last logged diff is playing, otherwise off
        # - when next diff is now and last diff no more active, play it
        #   -> log and dealer.on
        dealer = controller.dealer
        now = tz.make_aware(tz.datetime.now())
        playlist = []

        # - the last logged diff is the last one played, it can be playing
        #   -> no sound left or the diff is not more current: dealer.off
        #   -> otherwise, ensure dealer.on
        # - played sounds are logged in run_source
        prev_diff = cl.__get_prev_diff(dealer)
        if prev_diff and prev_diff.is_date_in_my_range(now):
            playlist = [ path for path in prev_diff.playlist
                            if path not in prev_diff.played ]
            dealer.on = bool(playlist)
        else:
            playlist = []
            dealer.on = False

        # - preload next diffusion's tracks
        args = {'start__gt': prev_diff.start } if prev_diff else {}
        next_diff = programs.Diffusion \
                        .get(controller.station, now, now = True,
                             type = programs.Diffusion.Type.normal,
                             sounds__isnull = False,
                             **args) \
                        .prefetch_related('sounds')
        if next_diff:
            next_diff = next_diff[0]
            playlist += next_diff.playlist

        # playlist update
        if dealer.playlist != playlist:
            dealer.playlist = playlist

        # dealer.on when next_diff.start <= now
        if next_diff and not dealer.on and next_diff.start <= now:
            dealer.on = True
            for source in controller.streams.values():
                source.skip()
            cl.log(
                source = dealer.id,
                date = now,
                comment = 'trigger diffusion to liquidsoap; '
                          'skip other streams',
                related_object = next_diff,
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
                #if not last_obj.duration or \
                #        now < last_log.date + to_timedelta(last_obj.duration):
                return

        sound = programs.Sound.objects.filter(path = on_air)
        if not sound:
            return

        sound = sound[0]
        cl.log(
            source = source.id,
            date = tz.make_aware(tz.datetime.now()),
            comment = 'sound changed',
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

        group = parser.add_argument_group('actions')
        group.add_argument(
            '-d', '--delay', type=int,
            default=1000,
            help='time to sleep in milliseconds between two updates when we '
                 'monitor'
        )
        group.add_argument(
            '-m', '--monitor', action='store_true',
            help='run in monitor mode'
        )
        group.add_argument(
            '-o', '--on_air', action='store_true',
            help='print what is on air'
        )
        group.add_argument(
            '-r', '--run', action='store_true',
            help='run liquidsoap with the generated configuration'
        )
        group.add_argument(
            '-w', '--write', action='store_true',
            help='write configuration and playlist'
        )

        group = parser.add_argument_group('selector')
        group.add_argument(
            '-s', '--station', type=int, action='append',
            help='select station(s) with this id'
        )
        group.add_argument(
            '-a', '--all', action='store_true',
            help='select all stations'
        )

    def handle (self, *args, **options):
        # selector
        stations = []
        if options.get('all'):
            stations = programs.Station.objects.filter(active = True)
        elif options.get('station'):
            stations = programs.Station.objects.filter(
                id__in = options.get('station')
            )

        run = options.get('run')
        monitor = options.get('on_air') or options.get('monitor')
        self.controllers = [ utils.Controller(station, connector = monitor)
                                for station in stations ]

        # actions
        if options.get('write') or run:
            self.handle_write()
        if run:
            self.handle_run()
        if monitor:
            self.handle_monitor(options)

        # post
        if run:
            for controller in self.controllers:
                controller.process.wait()

    def handle_write (self):
        for controller in self.controllers:
            controller.write()

    def handle_run (self):
        for controller in self.controllers:
            controller.process = \
                subprocess.Popen(['liquidsoap', '-v', controller.config_path],
                                 stderr=subprocess.STDOUT)
            atexit.register(controller.process.terminate)

    def handle_monitor (self, options):
        for controller in self.controllers:
            controller.update()

        if options.get('on_air'):
            for controller in self.controllers:
                print(controller.id, controller.on_air)
            return

        if options.get('monitor'):
            delay = options.get('delay') / 1000
            while True:
                for controller in self.controllers:
                    #try:
                    Monitor.run(controller)
                    #except Exception as err:
                    # print(err)
                time.sleep(delay)
            return



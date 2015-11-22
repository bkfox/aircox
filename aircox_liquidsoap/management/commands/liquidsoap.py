"""
Control Liquidsoap
"""
import os
import re
import datetime
import collections
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz

import aircox_liquidsoap.settings as settings
import aircox_liquidsoap.utils as utils
import aircox_programs.models as models

class DiffusionInfo:
    date = None
    original = None
    sounds = None
    duration = 0

    def __init__ (self, diffusion):
        episode = diffusion.episode
        self.original = diffusion
        self.sounds = [ sound for sound in episode.sounds
                            if sound.type = models.Sound.Type['archive'] ]
        self.sounds.sort(key = 'path')
        self.date = diffusion.date
        self.duration = episode.get_duration()
        self.end = self.date + tz.datetime.timedelta(seconds = self.duration)

    def __eq___ (self, info):
        return self.original.id == info.original.id


class ControllerMonitor:
    current = None
    queue = None


    def get_next (self, controller):
        upcoming = models.Diffusion.get_next(
            station = controller.station,
            # diffusion__episode__not blank
            # diffusion__episode__sounds not blank
        )
        return Monitor.Info(upcoming[0]) if upcoming else None


    def playlist (self, controller):
        dealer = controller.dealer
        on_air = dealer.current_sound
        playlist = dealer.playlist

        next = self.queue[0]

        # last track: time to reload playlist
        if on_air == playlist[-1] or on_air not in playlist:
            dealer.playlist = [sound.path for sound in next.sounds]
            dealer.on = False


    def current (self, controller):
        # time to switch...
        if on_air not in self.current.sounds:
            self.current = self.queue.popleft()

        if self.current.date <= tz.datetime.now() and not dealer.on:
            dealer.on = True
            print('start ', self.current.original)

        # HERE

        upcoming = self.get_next(controller)

        if upcoming.date <= tz.datetime.now() and not self.current:
            self.current = upcoming

        if not self.upcoming or upcoming != self.upcoming:
            dealer.playlist = [sound.path for sound in upcomming.sounds]
            dealer.on = False
            self.upcoming = upcoming


class Command (BaseCommand):
    help= __doc__
    output_dir = settings.AIRCOX_LIQUIDSOAP_MEDIA

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            '-o', '--on_air', action='store_true',
            help='Print what is on air'
        )
        parser.add_argument(
            '-m', '--monitor', action='store_true',
            help='Runs in monitor mode'
        )
        parser.add_argument(
            '-s', '--sleep', type=int,
            default=1,
            help='Time to sleep before update'
        )
        # start and run liquidsoap


    def handle (self, *args, **options):
        connector = utils.Connector()
        self.monitor = utils.Monitor()
        self.monitor.update()

        if options.get('on_air'):
            for id, controller in self.monitor.controller.items():
                print(id, controller.master.current_sound())


        if options.get('monitor'):
            sleep = 



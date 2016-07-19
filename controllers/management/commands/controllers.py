"""
Main tool to work with liquidsoap. We can:
- monitor Liquidsoap's sources and do logs, print what's on air.
- generate configuration files and playlists for a given station
"""
import os
import time
import re

from argparse import RawTextHelpFormatter

from django.conf import settings as main_settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz

import aircox.programs.models as programs
from aircox.controllers.models import Log, Station
from aircox.controllers.monitor import Monitor


class Command (BaseCommand):
    help= __doc__

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        group = parser.add_argument_group('actions')
        group.add_argument(
            '-c', '--config', action='store_true',
            help='generate configuration files for the stations'
        )
        group.add_argument(
            '-m', '--monitor', action='store_true',
            help='monitor the scheduled diffusions and log what happens'
        )
        group.add_argument(
            '-r', '--run', action='store_true',
            help='run the required applications for the stations'
        )

        group = parser.add_argument_group('options')
        group.add_argument(
            '-d', '--delay', type=int,
            default=1000,
            help='time to sleep in MILLISECONDS between two updates when we '
                 'monitor'
        )
        group.add_argument(
            '-s', '--station', type=str, action='append',
            help='name of the station to monitor instead of monitoring '
                 'all stations'
        )
        group.add_argument(
            '-t', '--timeout', type=int,
            default=600,
            help='time to wait in SECONDS before canceling a diffusion that '
                 'has not been ran but should have been. If 0, does not '
                 'check'
        )

    def handle (self, *args,
                config = None, run = None, monitor = None,
                station = [], delay = 1000, timeout = 600,
                **options):

        stations = Station.objects.filter(name__in = station)[:] \
                    if station else \
                        Station.objects.all()[:]

        for station in stations:
            station.prepare()
            if config and not run: # no need to write it twice
                station.controller.push()
            if run:
                station.controller.process_run()

        if monitor:
            monitors = [
                Monitor(station, cancel_timeout = timeout)
                    for station in stations
            ]
            delay = delay / 1000
            while True:
                for monitor in monitors:
                    monitor.monitor()
                time.sleep(delay)

        if run:
            for station in stations:
                station.controller.process_wait()


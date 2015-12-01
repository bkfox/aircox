"""
Monitor Liquidsoap's sources, logs, and even print what's on air.
"""
import time
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz

import aircox.liquidsoap.settings as settings
import aircox.liquidsoap.utils as utils
import aircox.programs.models as models


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
            '-d', '--delay', type=int,
            default=1000,
            help='Time to sleep in milliseconds before update on monitor'
        )


    def handle (self, *args, **options):
        connector = utils.Connector()
        self.monitor = utils.Monitor(connector)
        self.monitor.update()

        if options.get('on_air'):
            for id, controller in self.monitor.controller.items():
                print(id, controller.on_air)

        if options.get('monitor'):
            delay = options.get('delay') / 1000
            while True:
                for controller in self.monitor.controllers.values():
                    try:
                        controller.monitor()
                    except Exception, e:
                        print(e)
                time.sleep(delay)



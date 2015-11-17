"""
Control Liquidsoap
"""
import os
import re
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.views.generic.base import View
from django.template.loader import render_to_string

import aircox_liquidsoap.settings as settings
import aircox_liquidsoap.utils as utils



class Command (BaseCommand):
    help= __doc__
    output_dir = settings.AIRCOX_LIQUIDSOAP_MEDIA

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            '-o', '--on_air', action='store_true',
            help='Print what is on air'
        )

    def handle (self, *args, **options):
        controller = utils.Controller()
        controller.get()


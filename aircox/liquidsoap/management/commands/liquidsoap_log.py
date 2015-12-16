"""
This script is used by liquidsoap in order to log a file change. It should not
be used for other purposes.
"""
import os
from argparse import RawTextHelpFormatter

from django.utils import timezone as tz
from django.core.management.base import BaseCommand, CommandError

import aircox.programs.models as programs


class Command (BaseCommand):
    help= __doc__

    @staticmethod
    def date(s):
        try:
            return tz.make_aware(tz.datetime.strptime(s, '%Y/%m/%d %H:%M:%S'))
        except ValueError:
            raise argparse.ArgumentTypeError('Invalid date format')


    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        parser.add_argument(
            '-c', '--comment', type=str,
            help='log comment'
        )
        parser.add_argument(
            '-s', '--source', type=str,
            required=True,
            help='source path'
        )
        parser.add_argument(
            '-p', '--path', type=str,
            required=True,
            help='sound path to log'
        )
        parser.add_argument(
            '-d', '--date', type=Command.date,
            help='set date instead of now (using format "%Y/%m/%d %H:%M:%S")'
        )


    def handle (self, *args, **options):
        comment = options.get('comment') or ''
        path = os.path.realpath(options.get('path'))

        sound = programs.Sound.objects.filter(path = path)
        if sound:
            sound = sound[0]
        else:
            sound = None
            comment += '\nunregistered sound: {}'.format(path)

        programs.Log(source = options.get('source'),
                     comment = comment,
                     related_object = sound).save()



"""
Handle archiving of logs in order to keep database light and fast. The
logs are archived in gzip files, per day.
"""
import logging
from argparse import RawTextHelpFormatter

from django.conf import settings as main_settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz

import aircox.settings as settings
from aircox.models import Log, Station

logger = logging.getLogger('aircox.commands')


class Command (BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        group = parser.add_argument_group('actions')
        group.add_argument(
            '-a', '--age', type=int,
            default=settings.AIRCOX_LOGS_ARCHIVES_AGE,
            help='minimal age in days of logs to archive. Default is '
                 'settings.AIRCOX_LOGS_ARCHIVES_AGE'
        )
        group.add_argument(
            '-f', '--force', action='store_true',
            help='if an archive exists yet, force it to be updated'
        )
        group.add_argument(
            '-k', '--keep', action='store_true',
            help='keep logs in database instead of deleting them'
        )

    def handle(self, *args, age, force, keep, **options):
        date = tz.now() - tz.timedelta(days=age)

        while True:
            date = date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            logger.info('archive log at date %s', date)
            for station in Station.objects.all():
                Log.objects.make_archive(
                    station, date, force=force, keep=keep
                )

            qs = Log.objects.filter(date__lt=date)
            if not qs.exists():
                break
            date = qs.order_by('-date').first().date

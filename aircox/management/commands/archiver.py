"""
Handle archiving of logs in order to keep database light and fast. The
logs are archived in gzip files, per day.
"""
from argparse import RawTextHelpFormatter
import datetime
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone as tz

import aircox.settings as settings
from aircox.models import Log, Station
from aircox.models.log import LogArchiver

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
            '-k', '--keep', action='store_true',
            help='keep logs in database instead of deleting them'
        )

    def handle(self, *args, age, keep, **options):
        date = datetime.date.today() - tz.timedelta(days=age)
        # FIXME: mysql support?
        logger.info('archive logs for %s and earlier', date)
        count = LogArchiver().archive(Log.objects.filter(date__date__lte=date))
        logger.info('total log archived %d', count)

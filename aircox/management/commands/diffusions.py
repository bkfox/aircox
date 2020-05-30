"""
Manage diffusions using schedules, to update, clean up or check diffusions.

A generated diffusion can be unconfirmed, that means that the user must confirm
it by changing its type to "normal". The behaviour is controlled using
--approval.
"""
import datetime
import logging
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone as tz

from aircox.models import Schedule, Diffusion

logger = logging.getLogger('aircox.commands')


class Actions:
    date = None

    def __init__(self, date):
        self.date = date or datetime.date.today()

    def update(self):
        episodes, diffusions = [], []
        for schedule in Schedule.objects.filter(program__active=True,
                                                initial__isnull=True):
            eps, diffs = schedule.diffusions_of_month(self.date)

            episodes += eps
            diffusions += diffs

            logger.info('[update] %s: %d episodes, %d diffusions and reruns',
                        str(schedule), len(eps), len(diffs))

        with transaction.atomic():
            logger.info('[update] save %d episodes and %d diffusions',
                        len(episodes), len(diffusions))
            for episode in episodes:
                episode.save()
            for diffusion in diffusions:
                # force episode id's update
                diffusion.episode = diffusion.episode
                diffusion.save()

    def clean(self):
        qs = Diffusion.objects.filter(type=Diffusion.TYPE_UNCONFIRMED,
                                      start__lt=self.date)
        logger.info('[clean] %d diffusions will be removed', qs.count())
        qs.delete()


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.formatter_class = RawTextHelpFormatter
        today = datetime.date.today()

        group = parser.add_argument_group('action')
        group.add_argument(
            '-u', '--update', action='store_true',
            help='generate (unconfirmed) diffusions for the given month. '
                 'These diffusions must be confirmed manually by changing '
                 'their type to "normal"'
        )
        group.add_argument(
            '-l', '--clean', action='store_true',
            help='remove unconfirmed diffusions older than the given month'
        )

        group = parser.add_argument_group('date')
        group.add_argument(
            '--year', type=int, default=today.year,
            help='used by update, default is today\'s year')
        group.add_argument(
            '--month', type=int, default=today.month,
            help='used by update, default is today\'s month')
        group.add_argument(
            '--next-month', action='store_true',
            help='set the date to the next month of given date'
                 ' (if next month from today'
        )

    def handle(self, *args, **options):
        date = datetime.date(year=options['year'], month=options['month'],
                             day=1)
        if options.get('next_month'):
            month = options.get('month')
            date += tz.timedelta(days=28)
            if date.month == month:
                date += tz.timedelta(days=28)
            date = date.replace(day=1)

        actions = Actions(date)
        if options.get('update'):
            actions.update()
        if options.get('clean'):
            actions.clean()
        if options.get('check'):
            actions.check()

"""
Manage diffusions using schedules, to update, clean up or check diffusions.

A generated diffusion can be unconfirmed, that means that the user must confirm
it by changing its type to "normal". The behaviour is controlled using
--approval.

Different actions are available:
- "update" is the process that is used to generated them using programs
schedules for the (given) month.

- "clean" will remove all diffusions that are still unconfirmed and have been
planified before the (given) month.

- "check" will remove all diffusions that are unconfirmed and have been planified
from the (given) month and later.
"""
import logging
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as tz

from aircox.models import *

logger = logging.getLogger('aircox.tools')

import time

class Actions:
    @classmethod
    def update (cl, date, mode):
        manual = (mode == 'manual')

        count = [0, 0]
        for schedule in Schedule.objects.filter(program__active = True) \
                .order_by('initial'):
            # in order to allow rerun links between diffusions, we save items
            # by schedule;
            items = schedule.diffusions_of_month(date, exclude_saved = True)
            count[0] += len(items)

            # we can't bulk create because we ned signal processing
            for item in items:
                conflicts = item.get_conflicts()
                item.type = Diffusion.Type.unconfirmed \
                                if manual or conflicts.count() else \
                            Diffusion.Type.normal
                item.save(no_check = True)
                if conflicts.count():
                    item.conflicts.set(conflicts.all())

            logger.info('[update] schedule %s: %d new diffusions',
                    str(schedule), len(items),
                 )

        logger.info('[update] %d diffusions have been created, %s', count[0],
              'do not forget manual approval' if manual else
                '{} conflicts found'.format(count[1]))

    @staticmethod
    def clean (date):
        qs = Diffusion.objects.filter(type = Diffusion.Type.unconfirmed,
                                      start__lt = date)
        logger.info('[clean] %d diffusions will be removed', qs.count())
        qs.delete()

    @staticmethod
    def check (date):
        qs = Diffusion.objects.filter(type = Diffusion.Type.unconfirmed,
                                      start__gt = date)
        items = []
        for diffusion in qs:
            schedules = Schedule.objects.filter(program = diffusion.program)
            for schedule in schedules:
                if schedule.match(diffusion.start):
                    break
            else:
                items.append(diffusion.id)

        logger.info('[check] %d diffusions will be removed', len(items))
        if len(items):
            Diffusion.objects.filter(id__in = items).delete()


class Command (BaseCommand):
    help= __doc__

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter
        now = tz.datetime.today()

        group = parser.add_argument_group('action')
        group.add_argument(
            '--update', action='store_true',
            help='generate (unconfirmed) diffusions for the given month. '
                 'These diffusions must be confirmed manually by changing '
                 'their type to "normal"'
        )
        group.add_argument(
            '--clean', action='store_true',
            help='remove unconfirmed diffusions older than the given month'
        )
        group.add_argument(
            '--check', action='store_true',
            help='check unconfirmed later diffusions from the given '
                 'date agains\'t schedule. If no schedule is found, remove '
                 'it.'
        )

        group = parser.add_argument_group('date')
        group.add_argument(
            '--year', type=int, default=now.year,
            help='used by update, default is today\'s year')
        group.add_argument(
            '--month', type=int, default=now.month,
            help='used by update, default is today\'s month')
        group.add_argument(
            '--next-month', action='store_true',
            help='set the date to the next month of given date'
                 ' (if next month from today'
        )

        group = parser.add_argument_group('options')
        group.add_argument(
            '--mode', type=str, choices=['manual', 'auto'],
            default='auto',
            help='manual means that all generated diffusions are unconfirmed, '
                 'thus must be approved manually; auto confirmes all '
                 'diffusions except those that conflicts with others'
        )

    def handle (self, *args, **options):
        date = tz.datetime(year = options.get('year'),
                                 month = options.get('month'),
                                 day = 1)
        date = tz.make_aware(date)
        if options.get('next_month'):
            month = options.get('month')
            date += tz.timedelta(days = 28)
            if date.month == month:
                date += tz.timedelta(days = 28)

            date = date.replace(day = 1)

        if options.get('update'):
            Actions.update(date, mode = options.get('mode'))
        if options.get('clean'):
            Actions.clean(date)
        if options.get('check'):
            Actions.check(date)

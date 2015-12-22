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

from aircox.programs.models import *

logger = logging.getLogger('aircox.programs.' + __name__)

class Actions:
    @staticmethod
    def __check_conflicts (item, saved_items):
        """
        Check for conflicts, and update conflictual
        items if they have been generated during this
        update.

        Return the number of conflicts
        """
        conflicts = item.get_conflicts()
        if not conflicts:
            item.type = Diffusion.Type['normal']
            return 0

        item.type = Diffusion.Type['unconfirmed']
        for conflict in conflicts:
            if conflict.pk in saved_items and \
                    conflict.type != Diffusion.Type['unconfirmed']:
                conflict.type = Diffusion.Type['unconfirmed']
                conflict.save()
        return len(conflicts)

    @classmethod
    def update (cl, date, mode):
        manual = (mode == 'manual')
        if not manual:
            saved_items = set()

        count = [0, 0]
        for schedule in Schedule.objects.filter(program__active = True) \
                .order_by('initial'):
            # in order to allow rerun links between diffusions, we save items
            # by schedule;
            items = schedule.diffusions_of_month(date, exclude_saved = True)
            count[0] += len(items)

            if manual:
                Diffusion.objects.bulk_create(items)
            else:
                for item in items:
                    count[1] += cl.__check_conflicts(item, saved_items)
                    item.save()
                    saved_items.add(item)

            logger.info('[update] {} new diffusions for schedule #{} ({})'.format(
                    len(items), schedule.id, str(schedule)
                 ))

        logger.info('[update] total of {} diffusions have been created,'.format(count[0]),
              'do not forget manual approval' if manual else
                '{} conflicts found'.format(count[1]))

    @staticmethod
    def clean (date):
        qs = Diffusion.objects.filter(type = Diffusion.Type['unconfirmed'],
                                      date__lt = date)
        logger.info('[clean] {} diffusions will be removed'.format(qs.count()))
        qs.delete()

    @staticmethod
    def check (date):
        qs = Diffusion.objects.filter(type = Diffusion.Type['unconfirmed'],
                                      date__gt = date)
        items = []
        for diffusion in qs:
            schedules = Schedule.objects.filter(program = diffusion.program)
            for schedule in schedules:
                if schedule.match(diffusion.date):
                    break
            else:
                items.append(diffusion.id)

        logger.info('[check] {} diffusions will be removed'.format(len(items)))
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
                 'their type to "normal"')
        group.add_argument(
            '--clean', action='store_true',
            help='remove unconfirmed diffusions older than the given month')

        group.add_argument(
            '--check', action='store_true',
            help='check future unconfirmed diffusions from the given date '
                 'agains\'t schedules and remove it if that do not match any '
                 'schedule')

        group = parser.add_argument_group('date')
        group.add_argument(
            '--year', type=int, default=now.year,
            help='used by update, default is today\'s year')
        group.add_argument(
            '--month', type=int, default=now.month,
            help='used by update, default is today\'s month')

        group = parser.add_argument_group('mode')
        group.add_argument(
            '--approval', type=str, choices=['manual', 'auto'],
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

        if options.get('update'):
            Actions.update(date, mode = options.get('mode'))
        elif options.get('clean'):
            Actions.clean(date)
        elif options.get('check'):
            Actions.check(date)
        else:
            raise CommandError('no action has been given')


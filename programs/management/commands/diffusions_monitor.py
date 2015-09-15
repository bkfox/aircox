from django.core.management.base    import BaseCommand, CommandError
from django.utils                   import timezone as tz
from programs.models                import *


class Actions:
    @staticmethod
    def update (date):
        items = []
        for schedule in Schedule.objects.filter(parent__active = True):
            items += schedule.diffusions_of_month(date, exclude_saved = True)
            print('> {} new diffusions for schedule #{} ({})'.format(
                    len(items), schedule.id, str(schedule)
                  ))

        print('total of {} diffusions will be created. To be used, they need '
              'manual approval.'.format(len(items)))
        print(Diffusion.objects.bulk_create(items))

    @staticmethod
    def clean (date):
        qs = Diffusion.objects.filter(type = Diffusion.Type['unconfirmed'],
                                      date__lt = date)
        print('{} diffusions will be removed'.format(qs.count()))
        qs.delete()

    @staticmethod
    def check (date):
        qs = Diffusion.objects.filter(type = Diffusion.Type['unconfirmed'],
                                      date__gt = date)
        items = []
        for diffusion in qs:
            schedules = Schedule.objects.filter(parent = diffusion.program)
            for schedule in schedules:
                if schedule.match(diffusion.date):
                    break
            else:
                print('> #{}: {}'.format(diffusion.date, str(diffusion)))
                items.append(diffusion.id)

        print('{} diffusions will be removed'.format(len(items)))
        if len(items):
            Diffusion.objects.filter(id__in = items).delete()


class Command (BaseCommand):
    help= 'Monitor diffusions'

    def add_arguments (self, parser):
        now = tz.datetime.today()

        group = parser.add_argument_group('action')
        group.add_argument(
            '--update', action='store_true',
            help = 'generate (unconfirmed) diffusions for the given month. '
                   'These diffusions must be confirmed manually by changing '
                   'their type to "normal"')
        group.add_argument(
            '--clean', action='store_true',
            help = 'remove unconfirmed diffusions older than the given month')

        group.add_argument(
            '--check', action='store_true',
            help = 'check future unconfirmed diffusions from the given date '
                   'agains\'t schedules and remove it if that do not match any '
                   'schedule')

        group = parser.add_argument_group(
            'date',
            'this information is used by the action, starting at the first (!) '
                'of the given month')
        group.add_argument('--year', type=int, default=now.year,
                            help='used by update, default is today\'s year')
        group.add_argument('--month', type=int, default=now.month,
                            help='used by update, default is today\'s month')

    def handle (self, *args, **options):
        date = tz.datetime(year = options.get('year'),
                                 month = options.get('month'),
                                 day = 1)
        date = tz.make_aware(date)

        if options.get('update'):
            Actions.update(date)
        elif options.get('clean'):
            Actions.clean(date)
        elif options.get('check'):
            Actions.check(date)
        else:
            raise CommandError('no action has been given')


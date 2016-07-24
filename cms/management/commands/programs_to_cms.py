"""
Create missing publications for diffusions and programs already existing.

We limit the creation of diffusion to the elements to those that start at least
in the last 15 days, and to the future ones.

The new publications are not published automatically.
"""
import logging
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone as tz

from aircox.programs.models import Program, Diffusion
from aircox.cms.models import WebsiteSettings, ProgramPage, DiffusionPage

logger = logging.getLogger('aircox.tools')


class Command (BaseCommand):
    help= __doc__

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter

    def handle (self, *args, **options):
        for settings in WebsiteSettings.objects.all():
            logger.info('start sync for website {}'.format(
                str(settings.site)
            ))

            if not settings.auto_create:
                logger.warning('auto_create disabled: skip')
                continue

            if not settings.default_program_parent_page:
                logger.warning('no default program page for this website: skip')
                continue

            logger.info('start syncing programs...')

            parent = settings.default_program_parent_page
            for program in Program.objects.all():
                if program.page.count():
                    continue

                logger.info('- ' + program.name)
                page = ProgramPage(
                    program = program,
                    title = program.name,
                    live = False
                )
                parent.add_child(instance = page)

            logger.info('start syncing diffusions...')

            min_date = tz.now().date() - tz.timedelta(days = 20)
            for diffusion in Diffusion.objects.filter(start__gt = min_date):
                if diffusion.page.count() or diffusion.initial:
                    continue

                if not diffusion.program.page.count():
                    if not hasattr(diffusion.program, '__logged_diff_error'):
                        logger.warning(
                            'the program {} has no page; skip the creation of '
                            'page for its diffusions'.format(
                                diffusion.program.name
                            )
                        )
                        diffusion.program.__logged_diff_error = True
                    continue

                logger.info('- ' + str(diffusion))
                try:
                    page = DiffusionPage.from_diffusion(diffusion)
                    diffusion.program.page.first().add_child(instance = page)
                except:
                    import sys
                    e = sys.exc_info()[0]
                    logger.error('Error saving', str(diffusion) + ':', e)

            logger.info('done')




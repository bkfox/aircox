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

from aircox.models import Program, Diffusion
from aircox_cms.models import WebsiteSettings, ProgramPage, DiffusionPage

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

            # programs
            logger.info('Programs...')
            parent = settings.default_programs_page
            qs = Program.objects.filter(
                active = True,
                stream__isnull = True,
                page__isnull = True,
            )
            for program in qs:
                logger.info('- ' + program.name)
                page = ProgramPage(
                    program = program,
                    title = program.name,
                    live = False,
                )
                parent.add_child(instance = page)

            # diffusions
            logger.info('Diffusions...')
            qs = Diffusion.objects.filter(
                start__gt = tz.now().date() - tz.timedelta(days = 20),
                page__isnull = True,
                initial__isnull = True
            ).exclude(type = Diffusion.Type.unconfirmed)
            for diffusion in qs:
                if not diffusion.program.page:
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
                    page = DiffusionPage.from_diffusion(
                        diffusion, live = False
                    )
                    diffusion.program.page.add_child(instance = page)
                except:
                    import sys
                    e = sys.exc_info()[0]
                    logger.error('Error saving', str(diffusion) + ':', e)

            logger.info('done')




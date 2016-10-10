"""
Analyse and check files using Sox, prints good and bad files.
"""
import sys
import logging
import re
import subprocess
from argparse import RawTextHelpFormatter

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger('aircox.tools')

class Stats:
    attributes = [
        'DC offset', 'Min level', 'Max level',
        'Pk lev dB', 'RMS lev dB', 'RMS Pk dB',
        'RMS Tr dB', 'Flat factor', 'Length s',
    ]

    def __init__ (self, path, **kwargs):
        """
        If path is given, call analyse with path and kwargs
        """
        self.values = {}
        if path:
            self.analyse(path, **kwargs)

    def get (self, attr):
        return self.values.get(attr)

    def parse (self, output):
        for attr in Stats.attributes:
            value = re.search(attr + r'\s+(?P<value>\S+)', output)
            value = value and value.groupdict()
            if value:
                try:
                    value = float(value.get('value'))
                except ValueError:
                    value = None
                self.values[attr] = value
        self.values['length'] = self.values['Length s']

    def analyse (self, path, at = None, length = None):
        """
        If at and length are given use them as excerpt to analyse.
        """
        args = ['sox', path, '-n']

        if at is not None and length is not None:
            args += ['trim', str(at), str(length) ]

        args.append('stats')

        p = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        # sox outputs to stderr (my god WHYYYY)
        out_, out = p.communicate()
        self.parse(str(out, encoding='utf-8'))


class Sound:
    path = None             # file path
    sample_length = 120     # default sample length in seconds
    stats = None            # list of samples statistics
    bad = None              # list of bad samples
    good = None             # list of good samples

    def __init__ (self, path, sample_length = None):
        self.path = path
        self.sample_length = sample_length if sample_length is not None \
                                else self.sample_length

    def get_file_stats (self):
        return self.stats and self.stats[0]

    def analyse (self):
        logger.info('complete file analysis')
        self.stats = [ Stats(self.path) ]
        position = 0
        length = self.stats[0].get('length')

        if not self.sample_length:
            return

        logger.info('start samples analysis...')
        while position < length:
            stats = Stats(self.path, at = position, length = self.sample_length)
            self.stats.append(stats)
            position += self.sample_length

    def check (self, name, min_val, max_val):
        self.good = [ index for index, stats in enumerate(self.stats)
                      if min_val <= stats.get(name) <= max_val ]
        self.bad = [ index for index, stats in enumerate(self.stats)
                      if index not in self.good ]
        self.resume()

    def resume (self):
        view = lambda array: [
            'file' if index is 0 else
            'sample {} (at {} seconds)'.format(index, (index-1) * self.sample_length)
            for index in array
        ]

        if self.good:
            logger.info(self.path + ' -> good: \033[92m%s\033[0m',
                        ', '.join(view(self.good)))
        if self.bad:
            logger.info(self.path + ' -> bad: \033[91m%s\033[0m',
                        ', '.join(view(self.bad)))

class Command (BaseCommand):
    help = __doc__
    sounds = None

    def add_arguments (self, parser):
        parser.formatter_class=RawTextHelpFormatter

        parser.add_argument(
            'files', metavar='FILE', type=str, nargs='+',
            help='file(s) to analyse'
        )
        parser.add_argument(
            '-s', '--sample_length', type=int, default=120,
            help='size of sample to analyse in seconds. If not set (or 0), does'
                 ' not analyse by sample',
        )
        parser.add_argument(
            '-a', '--attribute', type=str,
            help='attribute name to use to check, that can be:\n' + \
                 ', '.join([ '"{}"'.format(attr) for attr in Stats.attributes ])
        )
        parser.add_argument(
            '-r', '--range', type=float, nargs=2,
            help='range of minimal and maximal accepted value such as: ' \
                 '--range min max'
        )
        parser.add_argument(
            '-i', '--resume', action='store_true',
            help='print a resume of good and bad files'
        )

    def handle (self, *args, **options):
        # parameters
        minmax = options.get('range')
        if not minmax:
            raise CommandError('no range specified')

        attr = options.get('attribute')
        if not attr:
            raise CommandError('no attribute specified')

        # sound analyse and checks
        self.sounds = [ Sound(path, options.get('sample_length'))
                        for path in options.get('files') ]
        self.bad = []
        self.good = []
        for sound in self.sounds:
            logger.info('analyse ' + sound.path)
            sound.analyse()
            sound.check(attr, minmax[0], minmax[1])
            if sound.bad:
                self.bad.append(sound)
            else:
                self.good.append(sound)

        # resume
        if options.get('resume'):
            for sound in self.good:
                logger.info('\033[92m+ %s\033[0m', sound.path)
            for sound in self.bad:
                logger.info('\033[91m+ %s\033[0m', sound.path)


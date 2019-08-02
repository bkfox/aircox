from collections import OrderedDict
import atexit
import logging
import os
import re
import signal
import subprocess

import psutil
import tzlocal

from django.template.loader import render_to_string
from django.utils import timezone as tz

from . import settings
from .models import Port, Station, Sound
from .connector import Connector


# FIXME liquidsoap does not manage timezones -- we have to convert
#       'on_air' metadata we get from it into utc one in order to work
#       correctly.

local_tz = tzlocal.get_localzone()
logger = logging.getLogger('aircox')


class Streamer:
    connector = None
    process = None

    station = None
    template_name = 'aircox/scripts/station.liq'
    path = None
    """ Config path """
    sources = None
    """ List of all monitored sources """
    source = None
    """ Current source being played on air """
    # note: we disable on_air rids since we don't have use of it for the
    # moment
    # on_air = None
    # """ On-air request ids (rid) """

    def __init__(self, station):
        self.station = station
        self.id = self.station.slug.replace('-', '_')
        self.path = os.path.join(station.path, 'station.liq')
        self.connector = Connector(os.path.join(station.path, 'station.sock'))
        self.init_sources()

    @property
    def socket_path(self):
        """ Path to Unix socket file """
        return self.connector.address

    @property
    def is_ready(self):
        """
        If external program is ready to use, returns True
        """
        return self.send('list') != ''

    @property
    def is_running(self):
        if self.process is None:
            return False

        returncode = self.process.poll()
        if returncode is None:
            return True

        self.process = None
        logger.debug('process died with return code %s' % returncode)
        return False

    # FIXME: is it really needed as property?
    @property
    def inputs(self):
        """ Return input ports of the station """
        return self.station.port_set.filter(
            direction=Port.Direction.input,
            active=True
        )

    @property
    def outputs(self):
        """ Return output ports of the station """
        return self.station.port_set.filter(
            direction=Port.Direction.output,
            active=True,
        )

    # Sources and config ###############################################
    def send(self, *args, **kwargs):
        return self.connector.send(*args, **kwargs) or ''

    def init_sources(self):
        streams = self.station.program_set.filter(stream__isnull=False)
        self.dealer = QueueSource(self, 'dealer')
        self.sources = [self.dealer] + [
            PlaylistSource(self, program=program) for program in streams
        ]

    def make_config(self):
        """ Make configuration files and directory (and sync sources) """
        data = render_to_string(self.template_name, {
            'station': self.station,
            'streamer': self,
            'settings': settings,
        })
        data = re.sub('[\t ]+\n', '\n', data)
        data = re.sub('\n{3,}', '\n\n', data)

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w+') as file:
            file.write(data)

        self.sync()

    def sync(self):
        """ Sync all sources. """
        if self.process is None:
            return

        for source in self.sources:
            source.sync()

    def fetch(self):
        """ Fetch data from liquidsoap """
        if self.process is None:
            return

        for source in self.sources:
            source.fetch()

        # request.on_air is not ordered: we need to do it manually
        if self.dealer.is_playing:
            self.source = self.dealer
            return

        self.source = next((source for source in self.sources
                           if source.is_playing), None)

    # Process ##########################################################
    def get_process_args(self):
        return ['liquidsoap', '-v', self.path]

    def check_zombie_process(self):
        if not os.path.exists(self.socket_path):
            return

        conns = [conn for conn in psutil.net_connections(kind='unix')
                 if conn.laddr == self.socket_path]
        for conn in conns:
            if conn.pid is not None:
                os.kill(conn.pid, signal.SIGKILL)

    def run_process(self):
        """
        Execute the external application with corresponding informations.

        This function must make sure that all needed files have been generated.
        """
        if self.process:
            return

        args = self.get_process_args()
        if not args:
            return

        self.check_zombie_process()
        self.process = subprocess.Popen(args, stderr=subprocess.STDOUT)
        atexit.register(lambda: self.kill_process())

    def kill_process(self):
        if self.process:
            logger.debug("kill process %s: %s", self.process.pid,
                         ' '.join(self.get_process_args()))
            self.process.kill()
            self.process = None

    def wait_process(self):
        """
        Wait for the process to terminate if there is a process
        """
        if self.process:
            self.process.wait()
            self.process = None


class Source:
    controller = None
    """ parent controller """
    id = None
    """ source id """
    uri = ''
    """ source uri """
    rid = None
    """ request id """
    air_time = None
    """ on air time """
    status = None
    """ source status """
    remaining = 0.0
    """ remaining time """

    @property
    def station(self):
        return self.controller.station

    @property
    def is_playing(self):
        return self.status == 'playing'

    #@property
    #def is_on_air(self):
    #    return self.rid is not None and self.rid in self.controller.on_air

    def __init__(self, controller, id=None):
        self.controller = controller
        self.id = id

    def sync(self):
        """ Synchronize what should be synchronized """
        pass

    def fetch(self):
        data = self.controller.send(self.id, '.remaining')
        self.remaining = float(data)

        data = self.controller.send(self.id, '.get', parse=True)
        self.on_metadata(data if data and isinstance(data, dict) else {})

    def on_metadata(self, data):
        """ Update source info from provided request metadata """
        self.rid = data.get('rid') or None
        self.uri = data.get('initial_uri') or None
        self.status = data.get('status') or None

        air_time = data.get('on_air')
        if air_time:
            air_time = tz.datetime.strptime(air_time, '%Y/%m/%d %H:%M:%S')
            self.air_time = local_tz.localize(air_time)
        else:
            self.air_time = None

    def skip(self):
        """ Skip the current source sound """
        self.controller.send(self.id, '.skip')

    def restart(self):
        """ Restart current sound """
        # seek 10 hours back since there is not possibility to get current pos
        self.seek(-216000*10)

    def seek(self, n):
        """ Seeks into the sound. """
        self.controller.send(self.id, '.seek ', str(n))


class PlaylistSource(Source):
    """ Source handling playlists (program streams) """
    path = None
    """ Path to playlist """
    program = None
    """ Related program """
    playlist = None
    """ The playlist """

    def __init__(self, controller, id=None, program=None, **kwargs):
        id = program.slug.replace('-', '_') if id is None else id
        self.program = program

        super().__init__(controller, id=id, **kwargs)
        self.path = os.path.join(self.station.path, self.id + '.m3u')

    def get_sound_queryset(self):
        """ Get playlist's sounds queryset """
        return self.program.sound_set.archive()

    def load_playlist(self):
        """ Load playlist """
        self.playlist = self.get_sound_queryset().paths()

    def write_playlist(self):
        """ Write playlist file. """
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as file:
            file.write('\n'.join(self.playlist or []))

    def stream(self):
        """ Return program's stream info if any (or None) as dict. """
        # used in templates
        # TODO: multiple streams
        stream = self.program.stream_set.all().first()
        if not stream or (not stream.begin and not stream.delay):
            return

        def to_seconds(time):
            return 3600 * time.hour + 60 * time.minute + time.second

        return {
            'begin': stream.begin.strftime('%Hh%M') if stream.begin else None,
            'end': stream.end.strftime('%Hh%M') if stream.end else None,
            'delay': to_seconds(stream.delay) if stream.delay else 0
        }

    def sync(self):
        self.load_playlist()
        self.write_playlist()


class QueueSource(Source):
    queue = None
    """ Source's queue (excluded on_air request) """

    def append(self, *paths):
        """ Add the provided paths to source's play queue """
        for path in paths:
            self.controller.send(self.id, '_queue.push ', path)

    def fetch(self):
        super().fetch()
        queue = self.controller.send(self.id, '_queue.queue').split(' ')
        self.queue = queue



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

from aircox import settings
from aircox.models import Station, Sound
from aircox.utils import to_seconds

from .connector import Connector
from .models import Port


__all__ = ['BaseMetadata', 'Request', 'Streamer', 'Source',
           'PlaylistSource', 'QueueSource']

# TODO: for the moment, update in station and program names do not update the
#       related fields.

# FIXME liquidsoap does not manage timezones -- we have to convert
#       'on_air' metadata we get from it into utc one in order to work
#       correctly.

local_tz = tzlocal.get_localzone()
logger = logging.getLogger('aircox')


class BaseMetadata:
    """ Base class for handling request metadata.  """
    controller = None
    """ Controller """
    rid = None
    """ Request id """
    uri = None
    """ Request uri """
    status = None
    """ Current playing status """
    request_status = None
    """ Requests' status """
    air_time = None
    """ Launch datetime """


    def __init__(self, controller=None, rid=None, data=None):
        self.controller = controller
        self.rid = rid
        if data is not None:
            self.validate(data)

    @property
    def is_playing(self):
        return self.status == 'playing'

    def fetch(self):
        data = self.controller.send('request.metadata ', self.rid, parse=True)
        if data:
            self.validate(data)

    def validate_status(self, status):
        on_air = self.controller.source
        if on_air and status == 'playing' and (on_air == self or
                on_air.rid == self.rid):
            return 'playing'
        elif status == 'playing':
            return 'paused'
        else:
            return 'stopped'

    def validate_air_time(self, air_time):
        if air_time:
            air_time = tz.datetime.strptime(air_time, '%Y/%m/%d %H:%M:%S')
            return local_tz.localize(air_time)

    def validate(self, data):
        """
        Validate provided data and set as attribute (must already be
        declared)
        """
        for key, value in data.items():
            if hasattr(self, key) and not callable(getattr(self, key)):
                setattr(self, key, value)
        self.uri = data.get('initial_uri')

        self.air_time = self.validate_air_time(data.get('on_air'))
        self.status = self.validate_status(data.get('status'))
        self.request_status = data.get('status')


class Request(BaseMetadata):
    title = None
    artist = None


class Streamer:
    connector = None
    process = None

    station = None
    template_name = 'aircox_streamer/scripts/station.liq'
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
    inputs = None
    """ Queryset to input ports """
    outputs = None
    """ Queryset to output ports """

    def __init__(self, station, connector=None):
        self.station = station
        self.inputs = self.station.port_set.active().input()
        self.outputs = self.station.port_set.active().output()

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
        """ True if holds a running process """
        if self.process is None:
            return False

        returncode = self.process.poll()
        if returncode is None:
            return True

        self.process = None
        logger.debug('process died with return code %s' % returncode)
        return False

    @property
    def playlists(self):
        return (s for s in self.sources if isinstance(s, PlaylistSource))

    @property
    def queues(self):
        return (s for s in self.sources if isinstance(s, QueueSource))

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
        for source in self.sources:
            source.sync()

    def fetch(self):
        """ Fetch data from liquidsoap """
        for source in self.sources:
            source.fetch()

        # request.on_air is not ordered: we need to do it manually
        self.source = next(iter(sorted(
            (source for source in self.sources
                if source.request_status == 'playing' and source.air_time),
            key=lambda o: o.air_time, reverse=True
        )), None)

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


class Source(BaseMetadata):
    controller = None
    """ parent controller """
    id = None
    """ source id """
    remaining = 0.0
    """ remaining time """
    status = 'stopped'

    @property
    def station(self):
        return self.controller.station

    def __init__(self, controller=None, id=None, *args, **kwargs):
        super().__init__(controller, *args, **kwargs)
        self.id = id

    def sync(self):
        """ Synchronize what should be synchronized """

    def fetch(self):
        try:
            data = self.controller.send(self.id, '.remaining')
            if data:
                self.remaining = float(data)
        except ValueError:
            self.remaining = None

        data = self.controller.send(self.id, '.get', parse=True)
        if data:
            self.validate(data if data and isinstance(data, dict) else {})

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

    def get_playlist(self):
        """ Get playlist from db """
        return self.get_sound_queryset().paths()

    def write_playlist(self, playlist=[]):
        """ Write playlist to file. """
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as file:
            file.write('\n'.join(playlist or []))

    def stream(self):
        """ Return program's stream info if any (or None) as dict. """
        # used in templates
        # TODO: multiple streams
        stream = self.program.stream_set.all().first()
        if not stream or (not stream.begin and not stream.delay):
            return

        return {
            'begin': stream.begin.strftime('%Hh%M') if stream.begin else None,
            'end': stream.end.strftime('%Hh%M') if stream.end else None,
            'delay': to_seconds(stream.delay) if stream.delay else 0
        }

    def sync(self):
        playlist = self.get_playlist()
        self.write_playlist(playlist)


class QueueSource(Source):
    queue = None
    """ Source's queue (excluded on_air request) """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def push(self, *paths):
        """ Add the provided paths to source's play queue """
        for path in paths:
            self.controller.send(self.id, '_queue.push ', path)

    def fetch(self):
        super().fetch()
        queue = self.controller.send(self.id, '_queue.queue').strip()
        if not queue:
            self.queue = []
            return

        self.queue = queue.split(' ')

    @property
    def requests(self):
        """ Queue as requests metadata """
        requests = [Request(self.controller, rid) for rid in self.queue]
        for request in requests:
            request.fetch()
        return requests



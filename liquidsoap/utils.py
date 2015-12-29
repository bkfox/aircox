import os
import socket
import re
import json

from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz

import aircox.programs.models as programs
import aircox.liquidsoap.models as models
import aircox.liquidsoap.settings as settings


class Connector:
    """
    Telnet connector utility.

    address: a string to the unix domain socket file, or a tuple
        (host, port) for TCP/IP connection
    """
    __socket = None
    __available = False
    address = None

    @property
    def available (self):
        return self.__available

    def __init__ (self, address = None):
        if address:
            self.address = address

    def open (self):
        if self.__available:
            return

        try:
            family = socket.AF_INET if type(self.address) in (tuple, list) else \
                     socket.AF_UNIX
            self.__socket = socket.socket(family, socket.SOCK_STREAM)
            self.__socket.connect(self.address)
            self.__available = True
        except:
            # print('can not connect to liquidsoap socket {}'.format(self.address))
            self.__available = False
            return -1

    def send (self, *data, try_count = 1, parse = False, parse_json = False):
        if self.open():
            return ''
        data = bytes(''.join([str(d) for d in data]) + '\n', encoding='utf-8')

        try:
            reg = re.compile(r'(.*)\s+END\s*$')
            self.__socket.sendall(data)
            data = ''
            while not reg.search(data):
                data += self.__socket.recv(1024).decode('utf-8')

            if data:
                data = reg.sub(r'\1', data)
                data = data.strip()

                if parse:
                    data = self.parse(data)
                elif parse_json:
                    data = self.parse_json(data)
            return data
        except:
            self.__available = False
            if try_count > 0:
                return self.send(data, try_count - 1)

    def parse (self, string):
        string = string.split('\n')
        data = {}
        for line in string:
            line = re.search(r'(?P<key>[^=]+)="?(?P<value>([^"]|\\")+)"?', line)
            if not line:
                continue
            line = line.groupdict()
            data[line['key']] = line['value']
        return data

    def parse_json (self, string):
        try:
            if string[0] == '"' and string[-1] == '"':
                string = string[1:-1]
            return json.loads(string) if string else None
        except:
            return None


class Source:
    """
    A structure that holds informations about a LiquidSoap source.
    """
    controller = None
    program = None
    metadata = None

    def __init__ (self, controller = None, program = None):
        self.controller = controller
        self.program = program

    @property
    def station (self):
        """
        Proxy to self.(program|controller).station
        """
        return self.program.station if self.program else \
                self.controller.station

    @property
    def connector (self):
        """
        Proxy to self.controller.connector
        """
        return self.controller.connector

    @property
    def id (self):
        """
        Identifier for the source, scoped in the station's one
        """
        postfix = ('_stream_' + str(self.program.id)) if self.program else ''
        return self.station.slug + postfix

    @property
    def name (self):
        """
        Name of the related object (program or station)
        """
        if self.program:
            return self.program.name
        return self.station.name

    @property
    def path (self):
        """
        Path to the playlist
        """
        return os.path.join(
            settings.AIRCOX_LIQUIDSOAP_MEDIA,
            self.station.slug,
            self.id + '.m3u'
        )

    @property
    def playlist (self):
        """
        Get or set the playlist as an array, and update it into
        the corresponding file.
        """
        try:
            with open(self.path, 'r') as file:
                return file.readlines()
        except:
            return []

    @playlist.setter
    def playlist (self, sounds):
        with open(self.path, 'w') as file:
            file.write('\n'.join(sounds))


    @property
    def current_sound (self):
        self.update()
        return self.metadata.get('initial_uri') if self.metadata else {}

    def stream_info (self):
        """
        Return a dict with info related to the program's stream.
        """
        if not self.program:
            return

        stream = programs.Stream.objects.get(program = self.program)
        if not stream.begin and not stream.delay:
            return

        def to_seconds (time):
            return 3600 * time.hour + 60 * time.minute + time.second

        return {
            'begin': stream.begin.strftime('%Hh%M') if stream.begin else None,
            'end': stream.end.strftime('%Hh%M') if stream.end else None,
            'delay': to_seconds(stream.delay) if stream.delay else 0
        }

    def skip (self):
        """
        Skip a given source. If no source, use master.
        """
        self.connector.send(self.id, '.skip')

    def update (self, metadata = None):
        """
        Update metadata with the given metadata dict or request them to
        liquidsoap if nothing is given.

        Return -1 in case no update happened
        """
        if metadata is not None:
            source = metadata.get('source') or ''
            if self.program and not source.startswith(self.id):
                return -1
            self.metadata = metadata
            return

        # r = self.connector.send('var.get ', self.id + '_meta', parse_json=True)
        r = self.connector.send(self.id, '.get', parse=True)
        return self.update(metadata = r or {})


class Master (Source):
    """
    A master Source
    """
    def update (self, metadata = None):
        if metadata is not None:
            return super().update(metadata)

        r = self.connector.send('request.on_air')
        r = self.connector.send('request.metadata ', r, parse = True)
        return self.update(metadata = r or {})


class Dealer (Source):
    """
    The Dealer source is a source that is used for scheduled diffusions and
    manual sound diffusion.

    Since we need to cache buffers for the scheduled track, we use an on-off
    switch in order to have no latency and enable preload.
    """
    name = _('Dealer')

    @property
    def id (self):
        return self.station.slug + '_dealer'

    def stream_info (self):
        pass

    @property
    def on (self):
        """
        Switch on-off;
        """
        r = self.connector.send('var.get ', self.id, '_on')
        return (r == 'true')

    @on.setter
    def on (self, value):
        return self.connector.send('var.set ', self.id, '_on',
                                    '=', 'true' if value else 'false')

class Controller:
    """
    Main class controller for station and sources (streams and dealer)
    """
    connector = None
    station = None      # the related station
    master = None       # master source (station's source)
    dealer = None       # dealer source
    streams = None      # streams streams

    @property
    def on_air (self):
        return self.master

    @property
    def id (self):
        return self.master and self.master.id

    @property
    def name (self):
        return self.master and self.master.name

    @property
    def path (self):
        """
        Directory path where all station's related files are put.
        """
        return os.path.join(settings.AIRCOX_LIQUIDSOAP_MEDIA,
                            self.station.slug)

    @property
    def socket_path (self):
        """
        Connector's socket path
        """
        return os.path.join(self.path, 'station.sock')

    @property
    def config_path (self):
        """
        Connector's socket path
        """
        return os.path.join(self.path, 'station.liq')

    def __init__ (self, station, connector = True, update = False):
        """
        Params:
        - station: managed station
        - connector: if true, create a connector, else do not

        Initialize a master, a dealer and all streams that are connected
        to the given station; We ensure the existence of the controller's
        files dir.
        """
        self.station = station
        self.station.controller = self
        self.outputs = models.Output.objects.filter(station = station)

        self.connector = connector and Connector(self.socket_path)

        self.master = Master(self)
        self.dealer = Dealer(self)
        self.streams = {
            source.id : source
            for source in [
                Source(self, program)
                for program in programs.Program.objects.filter(station = station,
                                                             active = True)
                if program.stream_set.count()
            ]
        }

        if update:
            self.update()

    def get (self, source_id):
        """
        Get a source by its id
        """
        if source_id == self.master.id:
            return self.master
        if source_id == self.dealer.id:
            return self.dealer
        return self.streams.get(source_id)


    def update (self):
        """
        Fetch and update all streams metadata.
        """
        self.master.update()
        self.dealer.update()
        for source in self.streams.values():
            source.update()


class Monitor:
    """
    Monitor multiple controllers.
    """
    controllers = None

    def __init__ (self):
        self.controllers = {
            controller.id : controller
            for controller in [
                Controller(station, True)
                for station in programs.Station.objects.filter(active = True)
            ]
        }

    def update (self):
        for controller in self.controllers.values():
            controller.update()



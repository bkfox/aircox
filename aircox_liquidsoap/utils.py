import os
import socket
import re
import json

from django.utils.translation import ugettext as _, ugettext_lazy

import aircox_programs.models as models
import aircox_liquidsoap.settings as settings


class Connector:
    """
    Telnet connector utility.

    address: a string to the unix domain socket file, or a tuple
        (host, port) for TCP/IP connection
    """
    __socket = None
    __available = False
    address = settings.AIRCOX_LIQUIDSOAP_SOCKET

    @property
    def available (self):
        return self.__available

    def __init__ (self, address = None):
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
            print('can not connect to liquidsoap socket {}'.format(self.address))
            self.__available = False
            return -1

    def send (self, *data, try_count = 1, parse = False, parse_json = False):
        if self.open():
            return ''
        data = bytes(''.join([str(d) for d in data]) + '\n', encoding='utf-8')

        try:
            reg = re.compile('(.*)[\n\r]+END[\n\r]*$')
            self.__socket.sendall(data)
            data = ''
            while not reg.match(data):
                data += self.__socket.recv(1024).decode('unicode_escape')

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
            self.id + '.m3u'
        )

    @property
    def playlist (self):
        """
        The playlist as an array
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
            self.connector.send(self.name, '_playlist.reload')

    def stream_info (self):
        """
        Return a dict with info related to the program's stream
        """
        if not self.program:
            return

        stream = models.Stream.objects.get(program = self.program)
        if not stream.begin and not stream.delay:
            return

        def to_seconds (time):
            return 3600 * time.hour + 60 * time.minute + time.second

        return {
            'begin': stream.begin.strftime('%Hh%M') if stream.begin else None,
            'end': stream.end.strftime('%Hh%M') if stream.end else None,
            'delay': to_seconds(stream.delay) if stream.delay else None
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
        if metadata:
            source = metadata.get('source') or ''
            if self.program and not source.startswith(self.id):
                return -1
            self.metadata = metadata
            return

        r = self.connector.send('var.get ', self.id + '_meta', parse_json=True)
        return self.update(metadata = r) if r else -1


class Dealer (Source):
    """
    The Dealer source is a source that is used for scheduled diffusions and
    manual sound diffusion.
    """
    name = _('Dealer')

    @property
    def id (self):
        return self.station.name + '_dealer'

    def stream_info (self):
        pass

    def get_next_diffusion (self):
        diffusions = models.Diffusion.get_next(self.station)
        if not diffusions.count():
            return

        diffusion = diffusions[0]
        return diffusion

    def on_air (self, value = True):
        pass

    @property
    def playlist (self):
        try:
            with open(self.path, 'r') as file:
                return file.readlines()
        except:
            return []

    @playlist.setter
    def playlist (self, sounds):
        with open(self.path, 'w') as file:
            file.write('\n'.join(sounds))


class Controller:
    connector = None
    station = None      # the related station
    master = None       # master source (station's source)
    dealer = None       # dealer source
    streams = None      # streams sources

    @property
    def on_air (self):
        return self.master

    @property
    def id (self):
        return self.master and self.master.id

    @property
    def name (self):
        return self.master and self.master.name

    def __init__ (self, station, connector = None):
        """
        use_connector: avoids the creation of a Connector, in case it is not needed
        """
        self.connector = connector
        self.station = station
        self.station.controller = self

        self.master = Source(self)
        self.dealer = Dealer(self)
        self.streams = {
            source.id : source
            for source in [
                Source(self, program)
                for program in models.Program.objects.filter(station = station,
                                                             active = True)
                if program.stream_set.count()
            ]
        }

    def get (self, source_id):
        """
        Get a source by its id
        """
        if source_id == self.master.id:
            return self.master
        if source_id == self.dealer.id:
            return self.dealer
        return self.streams.get(source_id)

    def next_diffusions (self, count = 5):
        """
        Return a list of the count next diffusions
        """
        return models.Diffusion.get_next(self.station)[:count]

    def update_all (self):
        """
        Fetch and update all sources metadata.
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

    def __init__ (self, connector = None):
        self.controllers = {
            controller.id : controller
            for controller in [
                Controller(station, connector)
                for station in models.Station.objects.filter(active = True)
            ]
        }

    def update (self):
        for controller in self.controllers.values():
            controller.update_all()



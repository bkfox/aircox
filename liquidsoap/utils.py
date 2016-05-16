import os
import socket
import re
import json
import subprocess

from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz
from django.conf import settings as main_settings
from django.template.loader import render_to_string

import aircox.programs.models as programs
import aircox.programs.settings as programs_settings
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
    def available(self):
        return self.__available

    def __init__(self, address = None):
        if address:
            self.address = address

    def open(self):
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

    def send(self, *data, try_count = 1, parse = False, parse_json = False):
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

    def parse(self, string):
        string = string.split('\n')
        data = {}
        for line in string:
            line = re.search(r'(?P<key>[^=]+)="?(?P<value>([^"]|\\")+)"?', line)
            if not line:
                continue
            line = line.groupdict()
            data[line['key']] = line['value']
        return data

    def parse_json(self, string):
        try:
            if string[0] == '"' and string[-1] == '"':
                string = string[1:-1]
            return json.loads(string) if string else None
        except:
            return None


class Playlist(list):
    path = None

    def __init__(self, path = None, items = None, program = None):
        self.path = path
        self.program = program
        if program:
            self.load_from_db()
        elif path:
            self.load()
        elif items:
            self.extend(items)

    def save(self):
        """
        Save data to the playlist file
        """
        os.makedirs(os.path.dirname(self.path), exist_ok = True)
        with open(self.path, 'w') as file:
            file.write('\n'.join(self))

    def load(self):
        """
        Load data from playlist file
        """
        if not os.path.exists(self.path):
            return
        with open(self.path, 'r') as file:
            self.clear()
            self.extend(file.readlines())

    def load_from_db(self, clear = True):
        """
        Update content from the database using the given program
        If clear is True, clear older items, otherwise append to the
        current playlist.
        If save is True, save the playlist to the playlist file
        """
        sounds = programs.Sound.objects.filter(
            type = programs.Sound.Type['archive'],
            path__startswith = os.path.join(
                programs_settings.AIRCOX_SOUND_ARCHIVES_SUBDIR,
                self.program.path
            ),
            # good_quality = True
            removed = False
        )
        self.clear()
        self.extend([sound.path for sound in sounds])

class BaseSource:
    id = None
    name = None
    controller = None
    metadata = None

    def __init__(self, controller, id, name):
        self.id = id
        self.name = name
        self.controller = controller

    def _send(self, *args, **kwargs):
        self.controller.connector.send(*args, **kwargs)

    @property
    def current_sound(self):
        self.update()
        return self.metadata.get('initial_uri') if self.metadata else {}

    def skip(self):
        """
        Skip a given source. If no source, use master.
        """
        self._send(self.id, '.skip')

    def update(self, metadata = None):
        """
        Update metadata with the given metadata dict or request them to
        liquidsoap if nothing is given.

        Return -1 in case no update happened
        """
        if metadata is None:
            r = self._send(self.id, '.get', parse=True)
            return self.update(metadata = r or {})

        source = metadata.get('source') or ''
        # FIXME: self.program
        if hasattr(self, 'program') and self.program \
                and not source.startswith(self.id):
            return -1
        self.metadata = metadata
        return


class Source(BaseSource):
    playlist = None     # playlist file
    program = None      # related program (if given)
    is_dealer = False   # Source is a dealer
    metadata = None

    def __init__(self, controller, program = None, is_dealer = None):
        station = controller.station
        if is_dealer:
            id, name = '{}_dealer'.format(station.slug), \
                       'Dealer'
            self.is_dealer = True
        else:
            id, name = '{}_stream_{}'.format(station.slug, program.id), \
                       program.name

        super().__init__(controller, id, name)

        path = os.path.join(settings.AIRCOX_LIQUIDSOAP_MEDIA,
                            station.slug,
                            self.id + '.m3u')
        self.playlist = Playlist(path, program = program)

    @property
    def on(self):
        """
        Switch on-off;
        """
        if not self.is_dealer:
            raise RuntimeError('only dealers can do that')
        r = self._send('var.get ', self.id, '_on')
        return (r == 'true')

    @on.setter
    def on(self, value):
        if not self.is_dealer:
            raise RuntimeError('only dealers can do that')
        return self._send('var.set ', self.id, '_on', '=',
                           'true' if value else 'false')

    def stream_info(self):
        """
        Return a dict with info related to the program's stream.
        """
        if not self.program:
            return

        stream = programs.Stream.objects.get(program = self.program)
        if not stream.begin and not stream.delay:
            return

        def to_seconds(time):
            return 3600 * time.hour + 60 * time.minute + time.second

        return {
            'begin': stream.begin.strftime('%Hh%M') if stream.begin else None,
            'end': stream.end.strftime('%Hh%M') if stream.end else None,
            'delay': to_seconds(stream.delay) if stream.delay else 0
        }


class Master (BaseSource):
    """
    A master Source based on a given station
    """
    def __init__(self, controller):
        station = controller.station
        super().__init__(controller, station.slug, station.name)

    def update(self, metadata = None):
        if metadata is not None:
            return super().update(metadata)

        r = self._send('request.on_air')
        r = self._send('request.metadata ', r, parse = True)
        return self.update(metadata = r or {})


class Controller:
    """
    Main class controller for station and sources (streams and dealer)
    """
    id = None
    name = None
    path = None

    connector = None
    station = None      # the related station
    master = None       # master source (station's source)
    dealer = None       # dealer source
    streams = None      # streams streams

    # FIXME: used nowhere except in liquidsoap cli to get on air item but is not
    #       correctly
    @property
    def on_air(self):
        return self.master

    @property
    def socket_path(self):
        """
        Connector's socket path
        """
        return os.path.join(self.path, 'station.sock')

    @property
    def config_path(self):
        """
        Connector's socket path
        """
        return os.path.join(self.path, 'station.liq')

    def __init__(self, station, connector = True, update = False):
        """
        Params:
        - station: managed station
        - connector: if true, create a connector, else do not

        Initialize a master, a dealer and all streams that are connected
        to the given station; We ensure the existence of the controller's
        files dir.
        """
        self.id = station.slug
        self.name = station.name
        self.path = os.path.join(settings.AIRCOX_LIQUIDSOAP_MEDIA, station.slug)

        self.station = station
        self.station.controller = self
        self.outputs = models.Output.objects.filter(station = station)

        self.connector = connector and Connector(self.socket_path)

        self.master = Master(self)
        self.dealer = Source(self, is_dealer = True)
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

    def get(self, source_id):
        """
        Get a source by its id
        """
        if source_id == self.master.id:
            return self.master
        if source_id == self.dealer.id:
            return self.dealer
        return self.streams.get(source_id)

    def update(self):
        """
        Fetch and update all streams metadata.
        """
        self.master.update()
        self.dealer.update()
        for source in self.streams.values():
            source.update()

    def write_data(self, playlist = True, config = True):
        """
        Write stream's playlists, and config
        """
        os.makedirs(self.path, exist_ok = True)
        if playlist:
            for source in self.streams.values():
                source.playlist.save()
            self.dealer.playlist.save()

        if not config:
            return

        log_script = main_settings.BASE_DIR \
                     if hasattr(main_settings, 'BASE_DIR') else \
                     main_settings.PROJECT_ROOT
        log_script = os.path.join(log_script, 'manage.py') + \
                        ' liquidsoap_log'

        context = {
            'controller': self,
            'settings': settings,
            'log_script': log_script,
        }

        data = render_to_string('aircox/liquidsoap/station.liq', context)
        data = re.sub(r'\s*\\\n', r'#\\n#', data)
        data = data.replace('\n', '')
        data = re.sub(r'#\\n#', '\n', data)
        with open(self.config_path, 'w+') as file:
            file.write(data)


class Monitor:
    """
    Monitor multiple controllers.
    """
    controllers = None

    def __init__(self):
        self.controllers = {
            controller.id : controller
            for controller in [
                Controller(station, True)
                for station in programs.Station.objects.filter(active = True)
            ]
        }

    def update(self):
        for controller in self.controllers.values():
            controller.update()



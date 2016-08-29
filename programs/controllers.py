import os
import re
import subprocess
import atexit

from django.template.loader import render_to_string

import aircox.programs.models as models
import aircox.programs.settings as settings

from aircox.programs.connector import Connector


class Streamer:
    """
    Audio controller of a Station.
    """
    station = None
    """
    Related station
    """
    template_name = 'aircox/controllers/liquidsoap.liq'
    """
    If set, use this template in order to generated the configuration
    file in self.path file
    """
    path = None
    """
    Path of the configuration file.
    """
    current_sound = ''
    """
    Current sound being played (retrieved by fetch)
    """
    current_source = None
    """
    Current source object that is responsible of self.current_sound
    """
    process = None
    """
    Application's process if ran from Streamer
    """

    socket_path = ''
    """
    Path to the connector's socket
    """
    connector = None
    """
    Connector to Liquidsoap server
    """

    def __init__(self, station, **kwargs):
        self.station = station
        self.path = os.path.join(station.path, 'station.liq')
        self.socket_path = os.path.join(station.path, 'station.sock')
        self.connector = Connector(self.socket_path)
        self.__dict__.update(kwargs)

    @property
    def id(self):
        """
        Streamer identifier common in both external app and here
        """
        return self.station.slug

    #
    # RPC
    #
    def _send(self, *args, **kwargs):
        return self.connector.send(*args, **kwargs)

    def fetch(self):
        """
        Fetch data of the children and so on

        The base function just execute the function of all children
        sources. The plugin must implement the other extra part
        """
        sources = self.station.sources
        for source in sources:
            source.fetch()

        rid = self._send('request.on_air').split(' ')[0]
        if ' ' in rid:
            rid = rid[:rid.index(' ')]
        if not rid:
            return

        data = self._send('request.metadata ', rid, parse = True)
        if not data:
            return

        self.current_sound = data.get('initial_uri')
        try:
            self.current_source = next(
                source for source in self.station.sources
                if source.rid == rid
            )
        except:
            self.current_source = None

    def push(self, config = True):
        """
        Update configuration and children's info.

        The base function just execute the function of all children
        sources. The plugin must implement the other extra part
        """
        sources = self.station.sources
        for source in sources:
            source.push()

        if config and self.path and self.template_name:
            data = render_to_string(self.template_name, {
                'station': self.station,
                'streamer': self,
                'settings': settings,
            })
            data = re.sub('[\t ]+\n', '\n', data)
            data = re.sub('\n{3,}', '\n\n', data)

            os.makedirs(os.path.dirname(self.path), exist_ok = True)
            with open(self.path, 'w+') as file:
                file.write(data)

    def skip(self):
        """
        Skip a given source. If no source, use master.
        """
        if self.current_source:
            self.current_source.skip()
        else:
            self._send(self.id, '.skip')

    #
    # Process management
    #
    def __get_process_args(self):
        """
        Get arguments for the executed application. Called by exec, to be
        used as subprocess.Popen(__get_process_args()).
        If no value is returned, abort the execution.
        """
        return ['liquidsoap', '-v', self.path]

    def process_run(self):
        """
        Execute the external application with corresponding informations.

        This function must make sure that all needed files have been generated.
        """
        if self.process:
            return

        self.push()

        args = self.__get_process_args()
        if not args:
            return
        self.process = subprocess.Popen(args, stderr=subprocess.STDOUT)
        atexit.register(self.process.terminate)

    def process_terminate(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def process_wait(self):
        """
        Wait for the process to terminate if there is a process
        """
        if self.process:
            self.process.wait()
            self.process = None

    def ready(self):
        """
        If external program is ready to use, returns True
        """
        return self._send('var.list') != ''


class Source:
    """
    Controller of a Source. Value are usually updated directly on the
    external side.
    """
    program = None
    """
    Related source
    """
    path = ''
    """
    Path to the Source's playlist file. Optional.
    """
    active = True
    """
    Source is available. May be different from the containing Source,
    e.g. dealer and liquidsoap.
    """
    current_sound = ''
    """
    Current sound being played (retrieved by fetch)
    """
    current_source = None
    """
    Current source being responsible of the current sound
    """

    rid = None
    """
    Current request id of the source in LiquidSoap
    """
    connector = None
    """
    Connector to Liquidsoap server
    """

    @property
    def id(self):
        return self.program.slug if self.program else 'dealer'

    def __init__(self, station, **kwargs):
        self.station = station
        self.connector = self.station.streamer.connector
        self.__dict__.update(kwargs)
        self.__init_playlist()

    #
    # Playlist
    #
    __playlist = None

    def __init_playlist(self):
        self.__playlist = []
        if not self.path:
            self.path = os.path.join(self.station.path,
                                     self.id + '.m3u')
            self.from_file()

        if not self.__playlist:
            self.from_db()

    @property
    def playlist(self):
        """
        Current playlist on the Source, list of paths to play
        """
        self.fetch()
        return self.__playlist

    @playlist.setter
    def playlist(self, value):
        value = sorted(value)
        if value != self.__playlist:
            self.__playlist = value
            self.push()

    def from_db(self, diffusion = None, program = None):
        """
        Load a playlist to the controller from the database. If diffusion or
        program is given use it, otherwise, try with self.program if exists, or
        (if URI, self.url).

        A playlist from a program uses all its available archives.
        """
        if diffusion:
            self.playlist = diffusion.playlist
            return

        program = program or self.program
        if program:
            self.playlist = [ sound.path for sound in
                models.Sound.objects.filter(
                    type = models.Sound.Type.archive,
                    program = program,
                )
            ]
            return

    def from_file(self, path = None):
        """
        Load a playlist from the given file (if not, use the
        controller's one
        """
        path = path or self.path
        if not os.path.exists(path):
            return

        with open(path, 'r') as file:
            self.__playlist = file.read()
            self.__playlist = self.__playlist.split('\n') \
                                if self.__playlist else []

    #
    # RPC
    #
    def _send(self, *args, **kwargs):
        return self.connector.send(*args, **kwargs)

    @property
    def active(self):
        return self._send('var.get ', self.id, '_active') == 'true'

    @active.setter
    def active(self, value):
        self._send('var.set ', self.id, '_active', '=',
                   'true' if value else 'false')

    def fetch(self):
        """
        Get the source information
        """
        data = self._send(self.id, '.get', parse = True)
        if not data or type(data) != dict:
            return

        self.rid = data.get('rid')
        self.current_sound = data.get('initial_uri')

    def push(self):
        """
        Update data relative to the source on the external program.
        By default write the playlist.
        """
        os.makedirs(os.path.dirname(self.path), exist_ok = True)
        with open(self.path, 'w') as file:
            file.write('\n'.join(self.__playlist or []))

    def skip(self):
        """
        Skip the current sound in the source
        """
        self._send(self.id, '.skip')

    def stream(self):
        """
        Return a dict with stream info for a Stream program, or None if there
        is not. Used in the template.
        """
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


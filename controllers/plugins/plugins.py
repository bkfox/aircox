import os
import re
import subprocess
import atexit

from django.template.loader import render_to_string

class Plugins(type):
    registry = {}

    def __new__(cls, name, bases, attrs):
        cl = super().__new__(cls, name, bases, attrs)
        if name != 'Plugin':
            if not cl.name:
                cl.name = name.lower()
            cls.registry[cl.name] = cl
        return cl

    @classmethod
    def discover(cls):
        """
        Discover plugins -- needed because of the import traps
        """
        import aircox.controllers.plugins.liquidsoap


class Plugin(metaclass=Plugins):
    name = ''

    def init_station(self, station):
        pass

    def init_source(self, source):
        pass


class StationController:
    """
    Controller of a Station.
    """
    station = None
    """
    Related station
    """
    template_name = ''
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

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def fetch(self):
        """
        Fetch data of the children and so on

        The base function just execute the function of all children
        sources. The plugin must implement the other extra part
        """
        sources = self.station.get_sources(dealer = True)
        for source in sources:
            source.prepare()
            if source.controller:
                source.controller.fetch()

    def __get_process_args(self):
        """
        Get arguments for the executed application. Called by exec, to be
        used as subprocess.Popen(__get_process_args()).
        If no value is returned, abort the execution.

        Must be implemented by the plugin
        """
        return []

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

    def push(self, config = True):
        """
        Update configuration and children's info.

        The base function just execute the function of all children
        sources. The plugin must implement the other extra part
        """
        sources = self.station.get_sources(dealer = True)
        for source in sources:
            source.prepare()
            if source.controller:
                source.controller.push()

        if config and self.path and self.template_name:
            import aircox.controllers.settings as settings

            data = render_to_string(self.template_name, {
                'station': self.station,
                'settings': settings,
            })
            data = re.sub('[\t ]+\n', '\n', data)
            data = re.sub('\n{3,}', '\n\n', data)

            os.makedirs(os.path.dirname(self.path), exist_ok = True)
            with open(self.path, 'w+') as file:
                file.write(data)


    def skip(self):
        """
        Skip the current sound on the station
        """
        pass


class SourceController:
    """
    Controller of a Source. Value are usually updated directly on the
    external side.
    """
    source = None
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

    __playlist = None

    @property
    def playlist(self):
        """
        Current playlist on the Source, list of paths to play
        """
        return self.__playlist

    @playlist.setter
    def playlist(self, value):
        self.__playlist = value
        self.push()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.__playlist = []
        if not self.path:
            self.path = os.path.join(self.source.station.path,
                                     self.source.slug + '.m3u')

    def skip(self):
        """
        Skip the current sound in the source
        """
        pass

    def fetch(self):
        """
        Get the source information
        """
        pass

    def push(self):
        """
        Update data relative to the source on the external program.
        By default write the playlist.
        """
        os.makedirs(os.path.dirname(self.path), exist_ok = True)
        with open(self.path, 'w') as file:
            file.write('\n'.join(self.playlist or []))

    def activate(self, value = True):
        """
        Activate/Deactivate current source. May be different from the
        containing Source.
        """
        pass


class Monitor:
    station = None



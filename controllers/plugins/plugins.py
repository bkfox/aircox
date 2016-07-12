import os
import re

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

    @property
    def id(self):
        return '{station.slug}_{station.pk}'.format(station = self.station)

    # TODO: add function to launch external program?

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def fetch(self):
        """
        Fetch data of the children and so on

        The base function just execute the function of all children
        sources. The plugin must implement the other extra part
        """
        sources = self.station.get_sources()
        for source in sources:
            if source.controller:
                source.controller.fetch()

    def push(self, config = True):
        """
        Update configuration and children's info.

        The base function just execute the function of all children
        sources. The plugin must implement the other extra part
        """
        sources = self.station.get_sources()
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

    @property
    def id(self):
        return '{source.station.slug}_{source.slug}'.format(source = self.source)

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



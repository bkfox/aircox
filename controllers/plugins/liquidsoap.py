import os

import aircox.controllers.plugins.plugins as plugins
from aircox.controllers.plugins.connector import Connector


class LiquidSoap(plugins.Plugin):
    @staticmethod
    def init_station(station):
        return StationController(station = station)

    @staticmethod
    def init_source(source):
        return SourceController(source = source)


class StationController(plugins.StationController):
    template_name = 'aircox/controllers/liquidsoap.liq'
    socket_path = ''
    connector = None

    def __init__(self, station, **kwargs):
        super().__init__(
            station = station,
            path = os.path.join(station.path, 'station.liq'),
            socket_path = os.path.join(station.path, 'station.sock'),
            **kwargs
        )
        self.connector = Connector(self.socket_path)

    def _send(self, *args, **kwargs):
        self.connector.send(*args, **kwargs)

    def fetch(self):
        super().fetch()

        data = self._send('request.on_air')
        if not data:
            return

        data = self._send('request.metadata', data, parse = True)
        if not data:
            return

        self.current_sound = data.get('initial_uri')
        # FIXME: point to the Source object
        self.current_source = data.get('source')


class SourceController(plugins.SourceController):
    connector = None

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.connector = self.source.station.controller.connector

    def _send(self, *args, **kwargs):
        self.connector.send(*args, **kwargs)

    @property
    def active(self):
        return self._send('var.get ', self.source.slug, '_active') == 'true'

    @active.setter
    def active(self, value):
        return self._send('var.set ', self.source.slug, '_active', '=',
                           'true' if value else 'false')

    def skip(self):
        """
        Skip a given source. If no source, use master.
        """
        self._send(self.source.slug, '.skip')

    def fetch(self):
        data = self._send(self.source.slug, '.get', parse = True)
        if not data:
            return

        # FIXME: still usefull? originally tested only if there ass self.program
        source = data.get('source') or ''
        if not source.startswith(self.id):
            return
        self.current_sound = data.get('initial_uri')

    def stream(self):
        """
        Return a dict with stream info for a Stream program, or None if there
        is not. Used in the template.
        """
        stream = self.source.stream
        if not stream or (not stream.begin and not stream.delay):
            return

        def to_seconds(time):
            return 3600 * time.hour + 60 * time.minute + time.second

        return {
            'begin': stream.begin.strftime('%Hh%M') if stream.begin else None,
            'end': stream.end.strftime('%Hh%M') if stream.end else None,
            'delay': to_seconds(stream.delay) if stream.delay else 0
        }




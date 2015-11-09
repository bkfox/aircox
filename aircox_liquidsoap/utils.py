import socket
import re

import aircox_liquidsoap.settings as settings

class Controller:
    socket = None
    available = False

    def __init__ (self):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def open (self):
        if self.available:
            return

        address = settings.AIRCOX_LIQUIDSOAP_SOCKET
        try:
            self.socket.connect(address)
            self.available = True
        except:
            print('can not connect to liquidsoap socket {}'.format(address))
            self.available = False
            return -1

    def send (self, data):
        if self.open():
            return ''
        data = bytes(data + '\n', encoding='utf-8')
        self.socket.sendall(data)
        return self.socket.recv(10240).decode('utf-8')

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

    def get (self, station, source = None):
        if source:
            r = self.send('{}_{}.get'.format(station.get_slug_name(), source))
        else:
            r = self.send('{}.get'.format(station.get_slug_name()))
        return self.parse(r) if r else None


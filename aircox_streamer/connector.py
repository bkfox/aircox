import socket
import re
import json


response_re = re.compile(r'(.*)\s+END\s*$')
key_val_re = re.compile(r'(?P<key>[^=]+)="?(?P<value>([^"]|\\")+)"?')


class Connector:
    """
    Connection to AF_UNIX or AF_INET, get and send data. Received
    data can be parsed from list of `key=value` or JSON.
    """
    socket = None
    """ The socket """
    address = None
    """
    String to a Unix domain socket file, or a tuple (host, port) for
    TCP/IP connection
    """

    @property
    def is_open(self):
        return self.socket is not None

    def __init__(self, address=None):
        if address:
            self.address = address

    def open(self):
        if self.is_open:
            return

        family = socket.AF_UNIX if isinstance(self.address, str) else \
            socket.AF_INET
        try:
            self.socket = socket.socket(family, socket.SOCK_STREAM)
            self.socket.connect(self.address)
        except:
            self.close()
            return -1

    def close(self):
        self.socket.close()
        self.socket = None

    # FIXME: return None on failed
    def send(self, *data, try_count=1, parse=False, parse_json=False):
        if self.open():
            return None

        data = bytes(''.join([str(d) for d in data]) + '\n', encoding='utf-8')
        try:
            self.socket.sendall(data)
            data = ''
            while not response_re.search(data):
                data += self.socket.recv(1024).decode('utf-8')

            if data:
                data = response_re.sub(r'\1', data).strip()
                data = self.parse(data) if parse else \
                    self.parse_json(data) if parse_json else data
            return data
        except:
            self.close()
            if try_count > 0:
                return self.send(data, try_count - 1)

    def parse(self, value):
        return {
            line.groupdict()['key']: line.groupdict()['value']
            for line in (key_val_re.search(line) for line in value.split('\n'))
            if line
        }

    def parse_json(self, value):
        try:
            if value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            return json.loads(value) if value else None
        except:
            return None

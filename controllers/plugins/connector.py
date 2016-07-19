import os
import socket
import re
import json


class Connector:
    """
    Simple connector class that retrieve/send data through a unix
    domain socket file or a TCP/IP connection

    It is able to parse list of `key=value`, and JSON data.
    """
    __socket = None
    __available = False
    address = None
    """
    a string to the unix domain socket file, or a tuple (host, port) for
    TCP/IP connection
    """

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





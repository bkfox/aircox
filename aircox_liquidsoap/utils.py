import socket
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
            return -1
        data = bytes(data + '\n', encoding='utf-8')
        self.socket.sendall(data)
        return self.socket.recv(10240).decode('utf-8')

    def get (self, stream = None):
        print(self.send('station.get'))



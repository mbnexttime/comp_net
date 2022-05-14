import socket
import datetime
import PySimpleGUI as gui
from threading import Thread


class View:
    def __init__(self):
        self.listeners = []

    def show(self):
        pass

    def hide(self):
        pass

    def subscribe_on_event(self, listener):
        self.listeners.append(listener)


class SimpleGuiView(View):
    def __init__(self, window_name):
        super().__init__()
        self.is_shown = False
        self.looper = None
        self.window_name = window_name

    def show(self):
        if self.looper is not None:
            self.looper.join()

        if self.is_shown:
            return

        layout = [
            [gui.Text('Введите IP.', size=(40, 1)), gui.InputText('127.0.0.1', key='host')],
            [gui.Text('Введите порт.', size=(40, 1)), gui.InputText('11481', key='port')],
            [gui.Text('Введите число пакетов.', size=(40, 1)), gui.InputText('10', key='messages')],
            [gui.Button('Отправить.')],
        ]

        self.window = gui.Window(self.window_name, layout)

        self.looper = Thread(target=self.loop)
        self.is_shown = True
        self.looper.run()

    def loop(self):
        while True:
            if not self.is_shown:
                return
            event, values = self.window.read()

            if event in (None, 'Exit'):
                self.hide()
                return

            try:
                host, port, number_of_messages = values['host'], int(values['port']), int(values['messages'])
            except Exception as _:
                continue

            for l in self.listeners:
                l.on_event((host, port, number_of_messages))

    def hide(self):
        self.is_shown = False


class SenderController:

    def __init__(self, view, sender):
        self.view = view
        self.sender = sender

        view.subscribe_on_event(type("listener", (), {
            "on_event": lambda values: self.on_event(values)
        }))

    def on_event(self, values):
        self.sender.send(values)

    def show(self):
        self.view.show()


class Sender:
    def send(self, values):
        pass


class TCPSender(Sender):
    def __init__(self, packet_size):
        self.packet_size = packet_size

    def send(self, values):
        (host, port, number_of_messages) = values
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((host, port))
            msg = str(number_of_messages) + ';'
            tcp_socket.sendall((msg + ''.join('0' for _ in range(self.packet_size - len(msg)))).encode())
            for i in range(number_of_messages):
                time = datetime.datetime.now()
                message = f'{int(time.timestamp() * 1000)};'
                message += ''.join('0' for _ in range(self.packet_size - len(message)))
                tcp_socket.sendall(message.encode())
            tcp_socket.close()
        except Exception as _:
            return


class UDPSender(Sender):
    def __init__(self, packet_size):
        self.packet_size = packet_size
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.settimeout(1)

    def send(self, values):
        (host, port, number_of_messages) = values
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((host, port))
            msg = str(number_of_messages) + ';'
            tcp_socket.sendall((msg + ''.join('0' for _ in range(self.packet_size - len(msg)))).encode())
            tcp_socket.close()
            for i in range(number_of_messages):
                time = datetime.datetime.now()
                message = f'{int(time.timestamp() * 1000)};'
                message += ''.join('0' for _ in range(self.packet_size - len(message)))
                self.udp_socket.sendto(message.encode(), (host, port))
        except Exception as e:
            return


view = SimpleGuiView("TCP speed test")
sender = TCPSender(2048)
client = SenderController(view, sender)

client.show()

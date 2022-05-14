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

    def set_data(self, data):
        pass

    def reset(self):
        pass


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
            [gui.Text('Как пользоваться: вводите IP и порт на сервере и клиенте (они должны совпадать). Затем фиксируете хост и порт на сервере. Затем отправляете пакеты с клиента. Затем рассчитываете скорость на сервере.', size=(100, 3))],
            [gui.Text('Введите IP.', size=(40, 1)), gui.InputText('127.0.0.1', key='host')],
            [gui.Text('Введите порт.', size=(40, 1)), gui.InputText('11481', key='port')],
            [gui.Text('Пакетов получено:', size=(40, 1)), gui.Text(key='messages')],
            [gui.Text('Скорость передачи:', size=(40, 1)), gui.Text(key='speed')],
            [gui.Button('Зафиксировать порт и хост.')], [gui.Button('Рассчитать скорость.')],
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
                host, port = values['host'], int(values['port'])
            except Exception as _:
                continue

            if event == 'Зафиксировать порт и хост.':
                for l in self.listeners:
                    l.on_port_fixed((host, port))

            if event == 'Рассчитать скорость.':
                for l in self.listeners:
                    l.on_event((host, port))

    def hide(self):
        self.is_shown = False

    def set_data(self, data):
        window = self.window
        if not window:
            return
        (speed, msg_received, msg_all) = data
        window['speed'].Update(f'{speed} KByte/s')
        window['messages'].Update(f'{msg_received}/{msg_all}')

    def reset(self):
        self.set_data((0, 0, 0))


class ReceiverController:

    def __init__(self, view, receiver):
        self.view = view
        self.receiver = receiver

        view.subscribe_on_event(type("listener", (), {
            "on_event": lambda values: self.on_event(values),
            "on_port_fixed": lambda values: self.on_port_fixed(values)
        }))

    def on_event(self, values):
        self.view.reset()
        data = self.receiver.receive(values)
        self.view.set_data(data)

    def on_port_fixed(self, values):
        self.receiver.on_port_fixed(values)

    def show(self):
        self.view.show()
        self.view.reset()


class Receiver:
    def receive(self, values):
        pass

    def on_port_fixed(self, values):
        pass


class TCPReceiver(Receiver):
    def __init__(self, packet_size):
        self.packet_size = packet_size
        self.tcp_socket = None

    def receive(self, values):
        if not self.tcp_socket:
            return None
        received, _ = self.tcp_socket.accept()
        [all_messages, _] = received.recv(self.packet_size).decode().split(';')
        all_messages = int(all_messages)
        msg_got, first_timing = 0, None
        for i in range(all_messages):
            try:
                msg_time_ms, _ = received.recv(self.packet_size).decode().split(';')
                msg_got += 1
                if not first_timing:
                    first_timing = int(msg_time_ms)
            except Exception as _:
                pass
        received.close()
        last_timing = round(datetime.datetime.now().timestamp() * 1000)
        if not first_timing:
            return 0, msg_got, all_messages
        total = last_timing - first_timing
        return self.packet_size * (msg_got + 1) / total, msg_got, all_messages

    def on_port_fixed(self, values):
        (host, port) = values
        if self.tcp_socket:
            self.tcp_socket.close()
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((host, port))
        self.tcp_socket.listen(1)


class UDPReceiver(Receiver):
    def __init__(self, packet_size):
        self.packet_size = packet_size
        self.tcp_socket = None
        self.udp_socket = None

    def receive(self, values):
        if not self.tcp_socket:
            return None
        if not self.udp_socket:
            return None

        received_tcp, _ = self.tcp_socket.accept()
        [all_messages, _] = received_tcp.recv(self.packet_size).decode().split(';')
        all_messages = int(all_messages)
        received_tcp.close()
        msg_got, first_timing = 0, None
        print(all_messages)
        for i in range(all_messages):
            try:
                msg, _ = self.udp_socket.recvfrom(self.packet_size)
                [msg_time_ms, _] = msg.decode().split(';')
                msg_got += 1
                if not first_timing:
                    first_timing = int(msg_time_ms)
            except Exception as e:
                print(e)
                pass
        last_timing = round(datetime.datetime.now().timestamp() * 1000)
        if not first_timing:
            return 0, msg_got, all_messages
        total = last_timing - first_timing
        return self.packet_size * (msg_got + 1) / total, msg_got, all_messages

    def on_port_fixed(self, values):
        (host, port) = values
        if self.tcp_socket:
            self.tcp_socket.close()
        if self.udp_socket:
            self.udp_socket.close()

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.settimeout(1)
        self.udp_socket.bind((host, port))

        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((host, port))
        self.tcp_socket.listen(1)


view = SimpleGuiView("TCP speed test server")
receiver = TCPReceiver(2048)
client = ReceiverController(view, receiver)

client.show()

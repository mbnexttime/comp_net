import socket
import datetime
import PySimpleGUI as gui
from scapy.layers.l2 import ARP
from scapy.layers.l2 import Ether
import scapy.all as scapy
from threading import Thread
import sys


class View:
    def __init__(self):
        self.listeners = []

    def show(self):
        pass

    def hide(self):
        pass

    def subscribe_on_event(self, listener):
        self.listeners.append(listener)

    def set_clients_count(self, clients):
        pass

    def print(self, text, flush):
        print(text, flush=flush)

    def inc_looked(self):
        pass


class SimpleGuiView(View):
    def __init__(self, window_name):
        super().__init__()
        self.is_shown = False
        self.looper = None
        self.window = None
        self.window_name = window_name
        self.clients_count = 1
        self.count = 0

    def show(self):
        if self.looper is not None:
            self.looper.join()

        if self.is_shown:
            return

        layout = [
            [gui.Text("Прогресс.")],
            [gui.ProgressBar(self.clients_count, orientation='h', size=(50, 20), key="progress_bar")],
            [gui.Output(size=(100, 20), font=('Arial', 14))],
            [gui.Submit('Найти.')],
        ]

        self.window = gui.Window(self.window_name, layout)

        self.looper = Thread(target=self.loop)
        self.is_shown = True
        self.looper.run()

    def loop(self):
        while True:
            if not self.is_shown:
                return
            event, value = self.window.read()
            progress_bar = self.window['progress_bar']
            progress_bar.UpdateBar(self.count, self.clients_count)

            if event in (None, 'Exit'):
                self.hide()
                return

            if event == "Найти.":
                for l in self.listeners:
                    l.on_event()

    def hide(self):
        self.is_shown = False

    def set_clients_count(self, clients):
        self.clients_count = clients

    def inc_looked(self):
        self.count = self.count + 1
        progress_bar = self.window['progress_bar']
        progress_bar.UpdateBar(self.count, self.clients_count)


class Scanner:
    def __init__(self):
        self.progress_listeners = []

    def add_listener(self, l):
        self.progress_listeners.append(l)

    def scan(self):
        pass

    def get_scan_in_progress(self):
        pass


# IMPORTANT!!! WORKS ONLY WITH SUDO
class ScapyScanner(Scanner):
    def __init__(self, home_ip, network_ip, home_mac, home_host):
        super().__init__()
        self.home_ip = home_ip
        self.network_ip = network_ip
        self.home_mac = home_mac
        self.home_host = home_host
        self.scan_in_progress = False

    def scan(self):
        self.scan_in_progress = True

        node = scapy.srp(
            Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=f'{self.network_ip}/24'),
            timeout=1,
            verbose=True
        )[0]

        for l in self.progress_listeners:
            l.on_clients_discovered(len(node))
            l.on_progress((self.home_ip, self.home_mac, self.home_host))

        for i, info in enumerate(node):
            ip, mac = info[1].psrc, info[1].hwsrc
            if ip == self.home_ip:
                continue
            else:
                try:
                    host_name = socket.gethostbyaddr(ip)[0]
                except Exception:
                    host_name = "Имя не найдено."
            for l in self.progress_listeners:
                l.on_progress((ip, mac, host_name))
        self.scan_in_progress = False

    def get_scan_in_progress(self):
        return self.scan_in_progress


class ScannerController:

    def __init__(self, view, scanner):
        self.view = view
        self.scanner = scanner

        view.subscribe_on_event(type("listener", (), {
            "on_event": lambda: self.on_event()
        }))

        scanner.add_listener(type("listener", (), {
            "on_progress": lambda data: self.on_progress(data),
            "on_clients_discovered": lambda count: self.view.set_clients_count(count)
        }))

    def on_event(self):
        if not self.scanner.get_scan_in_progress():
            try:
                self.scanner.scan()
            except Exception:
                print(sys.exc_info()[0])
                pass

    def show(self):
        self.view.show()


    def on_progress(self, data):
        (ip, mac, name) = data
        self.view.print(f'{str(ip):25}{mac:25}{name:25}', False)
        self.view.inc_looked()


view = SimpleGuiView("Scanner")
scanner = ScapyScanner("192.168.88.229", "192.168.88.0", "5C-E4-2A-FD-CD-39", socket.gethostbyaddr("192.168.88.229")[0])
client = ScannerController(view, scanner)

client.show()

import datetime
import queue
import socket
import requests
import argparse
from threading import Thread


class Logger:
    def __init__(self, filename, console=True):
        self.console = console
        self.log_file = open(filename, 'wt')

    def __del__(self):
        self.log_file.close()

    def log(self, message):
        now = datetime.datetime.now()
        log_message = f'{now}: {message}\n'
        if self.console:
            print(log_message)
        self.log_file.write(log_message)
        self.log_file.flush()


class Pool:

    def __init__(self, n, target):
        self.n = n
        self.target = target
        self.queue = queue.Queue(n)
        self.running = False
        self.threads = [
            Thread(target=self.internal_target) for _ in range(n)
        ]

    def go(self):
        self.running = True
        for thread in self.threads:
            thread.start()

    def push(self, args):
        self.queue.put(args)

    def stop(self):
        self.queue.join()
        self.running = False
        for thread in self.threads:
            thread.join()

    def internal_target(self):
        while self.running:
            try:
                args = self.queue.get(block=True, timeout=1)
            except Exception:
                continue
            self.target(*args)
            self.queue.task_done()


class Server:

    def __init__(self, logger, n, port):
        self.logger = logger
        self.n = n
        self.socket = None
        self.port = port

    def handle(self, socket, address):
        self.logger.log(f'connected to {address}')

        try:
            request = self.read_socket(socket)
            splited = request.split(' ')
            api_method = splited[0]
            url = splited[1][1:]

            self.logger.log(f'url {url}')

            if '\r\n\r\n' in request:
                body = request[request.index('\r\n\r\n') + 2]
                self.logger.log(f'body {body}')
            else:
                body = None
                self.logger.log(f'with no body')
            response = requests.request(api_method, url, data=body)
            self.logger.log(f'{api_method} {url} {body} has response code {response.status_code}')
            decoded = response.content.decode(response.encoding)
            socket.send(self.ok_response(decoded))

        except Exception as e:
            self.logger.log(e)
            socket.send(self.bad_response())

    def read_socket(self, socket):
        batch_size = 1024
        result = []
        while True:
            batch = socket.recv(batch_size)
            result.extend(batch)
            if len(batch) < batch_size:
                break
        return bytes(result).decode('utf-8')

    def bad_response(self):
        return b'HTTP/1.1 400 Bad Request\r\n\r\n'

    def not_found_response(self):
        return b'HTTP/1.1 404 Not Found\r\n\r\n'

    def ok_response(self, content):
        return bytes(f'HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n{content}', 'utf-8')

    def start(self):
        self.pool = Pool(self.n, self.handle)
        self.pool.go()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', self.port))
        self.socket.listen(1)
        self.logger.log("server started")

        while True:
            try:
                self.pool.push(self.socket.accept())
            except Exception:
                break
        self.logger.log('server stopped')
        self.pool.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('n', nargs='?', const=1, type=int, default=1)
    args = parser.parse_args()
    server = Server(Logger('server.log'), args.n, 11481)
    server.start()

# Должно работать и для POST метода, но я как то не могу найти сервер, куда можно было бы послать POST запрос без
# предварительных авторизационных токенов и etc.
#
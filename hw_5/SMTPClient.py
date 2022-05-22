import ssl
import socket
import base64


class SMTPClient:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = ssl.wrap_socket(self.socket, ssl_version=ssl.PROTOCOL_SSLv23)
        self.socket.connect(('smtp.mail.ru', 465))

    def __del__(self):
        self.socket.close()

    def send_str(self, msg=None, wait_response=True):
        if msg:
            msg = bytes(msg, encoding='utf-8')
        return self.send_raw(msg, wait_response)

    def read_socket(self, socket):
        batch_size = 1024
        result = []
        while True:
            batch = socket.recv(batch_size)
            result.extend(batch)
            if len(batch) < batch_size:
                break
        return bytes(result).decode('utf-8')

    def send_raw(self, raw=None, wait_response=True):
        if raw:
            self.socket.send(raw)
        if wait_response:
            r = self.read_socket(self.socket)
            print(r)
            return r
        else:
            return None

    def auth(self, mail_from, mail_from_psw):
        self.send_str()
        self.send_str(f'HELO {mail_from.split("@")[0]}\r\n')
        creds = ('\x00' + mail_from + '\x00' + mail_from_psw).encode()
        raw = 'AUTH PLAIN '.encode() + base64.b64encode(creds) + '\r\n'.encode()
        self.send_raw(raw)

    def send_meta(self, mail_from, mail_to, subject, t):
        self.send_str(f'MAIL FROM: {mail_from}\r\n')
        self.send_str(f'RCPT TO: {mail_to}\r\n')
        self.send_str('DATA\r\n')
        self.send_str(
            f'From: {mail_from}\r\n'f'To: {mail_to}\r\n'f'Subject: {subject}\r\n'f'Content-Type: {t}\r\n',
            wait_response=False
        )

    def send_text_msg(self, textfile, credsfile, mail_to, subject):
        body = self.read_from_file(textfile)
        [login, pswd] = self.read_from_file(credsfile).split(' ')
        self.auth(login, pswd)
        self.send_meta(login, mail_to, subject, 'text/plain')
        self.send_str(f'{body}\r\n', wait_response=False)
        self.send_str('.\r\n')

    def send_html_msg(self, textfile, credsfile, mail_to, subject):
        body = self.read_from_file(textfile)
        [login, pswd] = self.read_from_file(credsfile).split(' ')
        self.auth(login, pswd)
        self.send_meta(login, mail_to, subject, 'text/html')
        self.send_str(f'{body}\r\n', wait_response=False)
        self.send_str('.\r\n')

    def send_bin(self, file, credsfile, mail_to, subject):
        body = self.read_from_bin(file)
        [login, pswd] = self.read_from_file(credsfile).split(' ')
        self.auth(login, pswd)
        self.send_meta(login, mail_to, subject, f'image/gif')
        self.send_str(f'Content-Transfer-Encoding: base64\r\n', wait_response=False)
        self.send_raw(body + '\r\n'.encode(), wait_response=False)
        self.send_str('.\r\n')

    def read_from_file(self, path):
        with open(path, 'rt') as file:
            return file.read()

    def read_from_bin(self, path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read())


client = SMTPClient()

client.send_bin('photo_2022-05-08_21-49-12.jpg', 'creds.txt', 'cgawrilowapple10@gmail.com', 'lalalala')


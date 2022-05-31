from ftplib import FTP


class FTPClient:

    def __init__(self, login, pswrd, server_name):
        self.ftp = FTP(server_name)
        self.ftp.connect()
        self.ftp.login(login, pswrd)

    def get_all_dirs(self):
        result = [self.ftp.pwd()]
        for file in self.ftp.mlsd():
            name, meta = file
            type = meta.get('type')
            if type == 'dir':
                self.ftp.cwd(name)
                result += self.get_all_dirs()
                self.ftp.cwd('..')

    def upload_file(self, path):
        with open(path, "rb") as file:
            self.ftp.storbinary(f"STOR {path}", file)

    def download_file(self, path):
        with open(path, "wb") as file:
            self.ftp.retrbinary(f"RETR {path}", file.write)

import socket
import cv2
import numpy as np


class ServerConfig:
    def __init__(
            self,
            image_width,
            image_height,
            host,
            port,
            drawing_color,
            drawing_thickness,
            window_name
    ):
        self.image_width = image_width
        self.image_height = image_height
        self.host = host
        self.port = port
        self.drawing_color = drawing_color
        self.drawing_thickness = drawing_thickness
        self.window_name = window_name


class DrawingServer:

    def __init__(self, config):
        self.config = config
        self.img = None
        self.socket = None
        self.is_drawing = None
        self.is_initialized = False

    def initialize(self):
        self.img = np.zeros(shape=[self.config.image_height, self.config.image_width, 3], dtype=np.uint8)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_initialized = True

    def draw_line(self, from_x, from_y, x, y):
        cv2.line(self.img, (from_x, from_y), (x, y), self.config.drawing_color, self.config.drawing_thickness)

    def loop(self):
        if not self.is_initialized:
            raise RuntimeWarning("Not initialized")

        cv2.imshow(self.config.window_name, self.img)
        self.socket.bind((self.config.host, self.config.port))
        self.socket.listen()
        connection, _ = self.socket.accept()

        while True:
            cv2.imshow(self.config.window_name, self.img),

            if cv2.waitKey(10) == 27:
                break

            data = connection.recv(500)

            if data != b'':
                for line in data.decode('ascii').split('.'):
                    if line == '':
                        break
                    from_x, from_y, to_x, to_y = map(int, line.split())
                    self.draw_line(from_x, from_y, to_x, to_y)

        connection.close()
        cv2.destroyAllWindows()


config = ServerConfig(512, 512, "127.0.0.1", 11460, (123, 123, 123), 6, "Server")

server = DrawingServer(config)
server.initialize()
server.loop()

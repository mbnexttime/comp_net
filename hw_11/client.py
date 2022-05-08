import socket
import cv2
import numpy as np


class ClientConfig:
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


class DrawingClient:

    def __init__(self, config):
        self.config = config
        self.img = None
        self.current_x = None
        self.current_y = None
        self.socket = None
        self.is_drawing = None
        self.is_initialized = False

    def initialize(self):
        self.img = np.zeros(shape=[self.config.image_height, self.config.image_width, 3], dtype=np.uint8)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.config.host, self.config.port))
        self.is_initialized = True

    def on_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.is_drawing = True
            self.current_x = x
            self.current_y = y

        if event == cv2.EVENT_MOUSEMOVE:
            if self.is_drawing:
                self.draw_line(x, y)
                self.current_x = x
                self.current_y = y

        if event == cv2.EVENT_LBUTTONUP:
            self.draw_line(x, y)
            self.is_drawing = False
            self.current_x = None
            self.current_y = None

    def draw_line(self, x, y):
        cv2.line(self.img, (self.current_x, self.current_y), (x, y), self.config.drawing_color, self.config.drawing_thickness)
        self.socket.send(f'{self.current_x} {self.current_y} {x} {y}.'.encode('ascii'))

    def loop(self):
        if not self.is_initialized:
            raise RuntimeWarning("Not initialized")

        cv2.namedWindow(winname = self.config.window_name)
        cv2.setMouseCallback(self.config.window_name, self.on_event)

        while True:
            cv2.imshow(self.config.window_name, self.img)
            if cv2.waitKey(10) == 27:
                break

        cv2.destroyAllWindows()


config = ClientConfig(512, 512, "127.0.0.1", 11460, (123, 123, 123), 6, "Client")

client = DrawingClient(config)
client.initialize()
client.loop()

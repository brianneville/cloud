# this class will be used to set up a user server and handle client

import socket
import time
import threading
from server import ServerClass


class ClientHandler(threading.Thread):

    def __init__(self, ip, port_num):
        super(ClientHandler, self).__init__()
        self.HOST_IP = ip
        self.PORT_NUM = port_num

    def run(self):
        # do things here when the class is started

        # wait for server to be set up:
        print("sleeping to allow server to startup")
        time.sleep(0.1)
        # continue now that server has been set up
        pass

    def send(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 'with' statement will close connection when finished
            s.connect((self.HOST_IP, self.PORT_NUM))
            message = message.encode()
            s.sendall(message)
            data = s.recv(1024)
            return data.decode()


class User:
    HOST_IP = '127.0.0.1'
    SERVER_PORT_NUM = 40400
    CLIENT_PORT_NUM = SERVER_PORT_NUM
    CLOSE_STRING = "close"  # close the server to the client
    server_running = False

    def begin_serv(self):
        self.server_running = True
        s = ServerClass(self.HOST_IP, self.SERVER_PORT_NUM, self.CLOSE_STRING)
        s.begin_server()

    def start_both(self):
        c = ClientHandler(self.HOST_IP, self.CLIENT_PORT_NUM).start()
        if not self.server_running:
            self.begin_serv()
        print("server has finished blocking main loop")
        self.server_running = False
        c.join()

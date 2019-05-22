# this class will be used to set up a user server and handle client

import socket
import sys
import time
import threading
from queue import Queue
import ui

from server import ServerClass


def send(DEST_IP, PORT_NUM, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 'with' statement will close connection when finished
        s.connect((DEST_IP, PORT_NUM))

        message = message.encode()
        s.sendall(message)
        print("\u001b[34m" + f"client sent: {message} \u001b[0m")
        data = s.recv(1024)
        print("\u001b[34m " + f"client recv: {data} \u001b[0m")
        return data.decode()


class ClientHandler(threading.Thread):

    def __init__(self, ip, port_num, q, cond):
        super(ClientHandler, self).__init__()
        self.DEST_IP = ip               # TODO: this will have to be removed. dest_ip and port num will be
        self.PORT_NUM = port_num        # found by reading the messages from the queue: Format is "DEST_IP PORT_NUM msg"
        self.q = q      # this queue will have messages
        self.cond = cond

    def run(self):
        global app_instance
        # continue now that server has been set up
        # consume arguments from queue

        while True:
            print("getting from queue")
            self.cond.acquire()     # lock mutex
            while True:
                item = self.q.get()
                if item is not None:
                    break
                self.cond.wait()    # sleep until receive signal that queue is not empty
                # #TODO: this somehow gets signalled from somewhere
            self.cond.release()     # release mutex
            # process message from queue
            print("processing message")
            # TODO: DEST_IP, PORT_NUM, msg = parse(item)
            recv_msg = send(self.DEST_IP, self.PORT_NUM, item)
            app_instance.update_files(f'{recv_msg}')


class User:

    def __init__(self, msg_queue):
        self. HOST_IP = '127.0.0.1'
        self.SERVER_PORT_NUM = 40400
        self.CLIENT_PORT_NUM = self.SERVER_PORT_NUM     # for testing, see TODO above
        self.DEST_IP = self.HOST_IP
        self.CLOSE_STRING = "close"  # close the server to the client
        self.q = msg_queue
        self.cond = threading.Condition()

    def start_both(self):
        # start server
        s = ServerClass(self.HOST_IP, self.SERVER_PORT_NUM, self.CLOSE_STRING)
        s.daemon = True     # run as daemon to allow main thread to close and shut off server and client
        s.start()

        # start client
        c = ClientHandler(self.HOST_IP, self.CLIENT_PORT_NUM, self.q, self.cond)
        c.daemon = True
        c.start()
        return s, c


msg_q = Queue()
user = User(msg_queue=msg_q)
user_s, user_c = user.start_both()

# give the ui a message queue to feed into
ui.msg_q = msg_q
app_instance = ui.AppClass()

app_instance.run()

print("exiting sys")
sys.exit()


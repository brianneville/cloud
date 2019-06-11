# this class will be used to set up a user server and handle client

import socket
import sys
import threading
from messaging import *
from queue import Queue
# import ui
from DFSbackend import DFShandler, DO_NOT_CHANGE_CURRDIR
from colors import color_dict
from server import ServerClass

CLOSE_STRING = "close"


def send(DEST_IP, DEST_PORT, message, recieve) ->str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 'with' statement will close connection when finished
        try:
            s.connect((DEST_IP, int(DEST_PORT)))
        except ConnectionRefusedError:
            return f'NO CONNECTION TO THIS ({DEST_IP}, {DEST_PORT})'
        message = message.encode()
        s.sendall(message)
        recv_data = None
        print(color_dict['blue']+ f"client sent: {message}" + color_dict['reset'])
        if recieve:
            data = s.recv(1024)
            print(color_dict['blue'] + f"client recv: {data}" + color_dict['reset'])
            recv_data = data.decode()
        s.shutdown(socket.SHUT_RDWR)
        s.close()

        return recv_data  # return nothing if the message is being sent but not recieved

def processing(item):
    # process the message. try to extract keywords from it
    # if there is no proper format to it, then it has come from the app_instance.
    # if from app_instance, then put it into the DFS_backend to parse
    # if it specifies a dest_ip that is different from the clients own IP, then send it,
    # if it specifies a dest_ip that is the same as the clients own IP,then this is a msg that we had wanted to recieve
    global app_instance, user
    USER_UID = 101
    if item is not ' ':
        if item.find('IP:') >= 0 and item.find('PORT:') >= 0 and item.find('MSG:') >= 0:
            # recieving items from remote
            UID, IP, PORT, recv_msg = extract(item)
            change_dir, output = getchangedir_op(recv_msg)
            app_instance.update_files(f'{output}')
            if change_dir is not DO_NOT_CHANGE_CURRDIR:
                app_instance.update_curr_dir(change_dir)
        elif item == CLOSE_STRING:
            # shut off user server when closing. if this is not here, then the CLOSE_STRING will be sent to remote,
            # and remote will shutdown when user closes their ui terminal
            send(user.HOST_IP, user.SERVER_PORTNUM,
                 formatmsg(uid=USER_UID, host_ip=user.HOST_IP, host_portnum=user.SERVER_PORTNUM, item=item),
                 recieve=False)

        else:
            # user entered something, format this item, and send to remote
            send(user.DEST_IP, user.REMOTE_PORTNUM,
                 formatmsg(uid=USER_UID, host_ip=user.HOST_IP, host_portnum=user.SERVER_PORTNUM, item=item),
                 recieve=False)


class ClientHandler(threading.Thread):

    def __init__(self, ip, port_num, q, cond, processing_func):
        super(ClientHandler, self).__init__()
        self.DEST_IP = ip               # TODO: this will have to be removed. dest_ip and port num will be
        self.DEST_PORT = port_num       # found by reading the messages from the queue: Format is "DEST_IP PORT_NUM msg"
        self.q = q      # this queue will have messages
        self.cond = cond
        self.processing_func = processing_func

    def run(self) ->None:
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
                # #TODO: this somehow gets signalled from somewhere?
            self.cond.release()     # release mutex
            # process message from queue
            print(f"processing message: {item}")
            self.processing_func(item)


class User:

    def __init__(self, client_q, serv_q, HOST_IP, SERVER_PORTNUM, DEST_IP, REMOTE_PORTNUM, proc_func):
        self. HOST_IP = HOST_IP
        self.SERVER_PORTNUM = SERVER_PORTNUM        # the port number that user is hosting a server on
        self.REMOTE_PORTNUM = REMOTE_PORTNUM      # the port number that the seperate server is using
        self.DEST_IP = DEST_IP
        self.CLOSE_STRING = CLOSE_STRING  # close the server to the client
        self.client_q = client_q
        self.serv_q = serv_q
        self.cond = threading.Condition()
        self.proc_func = proc_func

    def start_both(self) ->(threading.Thread, threading.Thread):
        # start server
        if 'server' in sys.modules:
            s = ServerClass(self.HOST_IP, self.SERVER_PORTNUM, self.CLOSE_STRING, msg_q=self.serv_q)
            s.daemon = True     # run as daemon to allow main thread to close and shut off server and client
            s.start()
        else:
            s = None
        # start client
        c = ClientHandler(self.HOST_IP, self.REMOTE_PORTNUM, self.client_q, self.cond, self.proc_func)
        c.daemon = True
        c.start()
        return s, c


def main():
    global app_instance, user_s, user_c, user
    msg_q = Queue()
    # server doesnt need to send items to the client q
    user = User(serv_q=msg_q, client_q=msg_q, HOST_IP='127.0.0.1', SERVER_PORTNUM=9001, DEST_IP='127.0.0.1',
                REMOTE_PORTNUM=12001, proc_func=processing)
    user_s, user_c = user.start_both()

    # give the ui a message queue to feed into
    ui.msg_q = msg_q
    app_instance = ui.AppClass()
    app_instance.run()

    print("exiting sys")
    sys.exit()


if __name__ == '__main__':
    import ui
    main()


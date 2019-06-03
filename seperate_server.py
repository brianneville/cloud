from user import User
from queue import Queue
from colors import color_dict
from user import send, extract, formatmsg
DEFAULT_UID = 1401


def server_send(DEST_IP, PORT_NUM, item):
    pass


def server_save(item):
    pass


def serv_processing(item):
    global seperate_server
    print(color_dict['red'] + f"server processing item : {item}" + color_dict['reset'])
    remote_ip, remote_port, msg = extract(item)
    recv_msg = send(remote_ip, int(remote_port),
                    formatmsg(host_portnum=seperate_server.SERVER_PORTNUM,
                              host_ip=seperate_server.HOST_IP,
                              item='serv_processed: ' + msg),
                    recieve=False)
    if item.find('get'):
       # server_send(dest_ip, port_num, item)
        pass
    if item.find('up'):
        # server_save(item)
        pass


def main():
    global seperate_server
    msg_q = Queue()
    seperate_server = User(client_q=msg_q, serv_q=msg_q, HOST_IP='127.0.0.1', SERVER_PORTNUM=12001, DEST_IP='127.0.0.1',
                           REMOTE_PORTNUM=9001, proc_func=serv_processing)
    serv_s, serv_c = seperate_server.start_both()
    serv_s.join()


if __name__ == '__main__':
    main()



'''
class ClientHandler(threading.Thread):

    def __init__(self, ip, port_num, q, cond, processing_func):
        super(ClientHandler, self).__init__()
        self.DEST_IP = ip               # TODO: this will have to be removed. dest_ip and port num will be
        self.PORT_NUM = port_num        # found by reading the messages from the queue: Format is "DEST_IP PORT_NUM msg"
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
                # #TODO: this somehow gets signalled from somewhere
            self.cond.release()     # release mutex
            # process message from queue
            print("processing message")
            self.processing_func(item)



class SeperateServer:

    def __init__(self, msg_queue, HOST_IP, SERV_PORTNUM, DEST_IP, CLIENT_PORTNUM):
        self.HOST_IP = HOST_IP
        self.SERVER_PORT_NUM = SERV_PORTNUM
        self.CLIENT_PORT_NUM = CLIENT_PORTNUM  # for testing, see TODO above
        self.DEST_IP = DEST_IP
        self.CLOSE_STRING = "close"  # close the server to the client
        self.q = msg_queue
        self.cond = threading.Condition()

    def start_both(self) ->(threading.Thread, threading.Thread):
        # start server
        if 'server' in sys.modules:
            s = ServerClass(self.HOST_IP, self.SERVER_PORT_NUM, self.CLOSE_STRING, msg_q=self.q)
            s.daemon = True     # run as daemon to allow main thread to close and shut off server and client
            s.start()
        else:
            s = None
        # start client
        c = ClientHandler(self.HOST_IP, self.CLIENT_PORT_NUM, self.q, self.cond)
        c.daemon = True
        c.start()
        return s, c#
        
        
        from main import all* 
'''
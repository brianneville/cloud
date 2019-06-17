# asynchronous server
import asyncio
import threading
from colors import color_dict


class ServerClass(threading.Thread):

    async def handle_echo(self, reader, writer):
        # this function called when starting the server will recieve a pair of arguments
        # of type StreamReader and StreamWriter
        data = await reader.read()   # read up to 1000 bytes    # currently reading up to EOF
        message = data.decode()         # decode byte object

        if self.msq_q is not None:      # for the seperate servers , we need to pass the message back to the client to
            #                             process
            # (color_dict['blue'] + "server is putting message in queue for client to deal with" +
            #      color_dict['reset'])
            self.msq_q.put(message)
        await writer.drain()        # block if the send buffer is reached its maximum, until the other side has recieved
        # and the buffer is no full
        # ^not needed, no writing is done
        writer.close()
        if message[message.find('MSG:')+len('MSG:'):] == self.CLOSE_STRING:
            print("server setting future")
            self.fut.set_result(0)       # set the future with a result and therefore the connection can close

    def begin_server(self):
        print("beginning server")
        # self.loop = asyncio.get_event_loop()
        self.loop = asyncio.new_event_loop()    # new event loop for this thread
        asyncio.set_event_loop(self.loop)
        self.fut = asyncio.Future()
        self.server_coro = asyncio.start_server(self.handle_echo, self.HOST_IP, self.PORT_NUM, loop=self.loop)
        self.server = self.loop.run_until_complete(asyncio.gather(self.server_coro, self.fut))
        # the server_coro coroutine has stopped running before the fut value is set
        # this means that the server will always already be closed?
        self.loop.close()
        print('server loop closed')

    def __init__(self, ip, port_num, close_string, msg_q):
        super(ServerClass, self).__init__()
        self.HOST_IP = ip
        self.PORT_NUM = port_num
        self.CLOSE_STRING = close_string
        self.server, self.server_coro, self.loop, self.server, self.fut = None, None, None, None, None
        self.msq_q = msg_q

    def run(self):
        self.begin_server()


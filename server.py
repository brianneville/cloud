# asynchronous server
import asyncio


class ServerClass:

    async def handle_echo(self, reader, writer):
        # this function called when starting the server will recieve a pair of arguments
        # of type StreamReader and StreamWriter
        global last_data
        data = await reader.read(100)   # read up to 100 bytes
        message = data.decode()         # decode byte object
        last_data = message
        addr = writer.get_extra_info('peername')
        print(f"client message is: {message}\n client address is: {addr}")

        print(f"Send: {message}")   # echo the message back
        writer.write(data)          # immediately send the original data back
        await writer.drain()        # block if the send buffer is reached its maximum, until the other side has recieved
        # and the buffer is no full

        print("Close client socket")
        writer.close()
        if message == self.CLOSE_STRING:
            print("server setting future")
            self.fut.set_result(0)       # set the future with a result and therefore the connection can close

    def begin_server(self):
        print("beginning server")
        self.loop = asyncio.get_event_loop()
        self.fut = asyncio.Future()
        self.server_coro = asyncio.start_server(self.handle_echo, self.HOST_IP, self.PORT_NUM, loop=self.loop)
        self.server = self.loop.run_until_complete(asyncio.gather(self.server_coro, self.fut))
        # the server_coro coroutine has stopped running before the fut value is set
        # this means that the server will always already be closed?
        self.loop.close()

    def __init__(self,  ip, port_num, close_string):
        self.last_data = None
        self.HOST_IP = ip
        self.PORT_NUM = port_num
        self.CLOSE_STRING = close_string
        self.server, self.server_coro, self.loop, self.server, self.fut = None, None, None, None, None



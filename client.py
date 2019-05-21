'''
import asyncio




    async def tcp_echo_client(self, message, loop):
        reader, writer = await asyncio.open_connection(self.HOST_IP, self.PORT_NUM, loop=loop)
        print('Send: %r' % message)
        writer.write(message.encode())

        data = await reader.read(100)
        print('Received: %r' % data.decode())

        print('Close the socket')
        writer.close()

    def __init__(self, ip, port_num):
        self.HOST_IP = ip
        self.PORT_NUM = port_num

    def send(self, message):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.tcp_echo_client(message, loop))
        loop.close()
'''

import socket


class ClientClass:

    def __init__(self, ip, port_num):
        # super(ClientClass, self).__init__()
        self.HOST_IP = ip
        self.PORT_NUM = port_num
        self.proc = None    # process used to print out on console

    def send(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 'with' statement will close connection when finished
            s.connect((self.HOST_IP, self.PORT_NUM))
            message = message.encode()
            s.sendall(message)
            data = s.recv(1024)
            # self.print_newterm(f'Received {data.decode()}')
            return data.decode()


'''
    def run(self):
        if self.pre_serv:
            print("sleeping to allow server to startup")
            time.sleep(0.1)
        print("running")
        self.send(self.message)
'''

'''
    def print_newterm(self, msg):
        # open
        if platform.system() == "Windows":
            new_window_command = "cmd.exe /c start".split()
        else:
            new_window_command = "x-terminal-emulator -e".split()
        echo = [sys.executable, "-c",
                "import sys; print('testing');print(sys.argv[1]); input('press any key')"]
        try:
            self.proc.kill()
        except AttributeError:
            pass
        self.proc = Popen(new_window_command + echo + [msg])
        # echo = [sys.executable, "-c", self.wrapper(msg)]
        # process = Popen(new_window_command + echo)
        self.proc.wait()
'''


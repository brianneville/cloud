'''

import socket

HOST_IP = '127.0.0.1'
PORT_NUM = 40400

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # 'with' statement will close connection when finished
    s.connect((HOST_IP, PORT_NUM))
    s.sendall(b'Hello, world')
    data = s.recv(1024)

print('Received', repr(data))
'''

import asyncio
HOST_IP = '127.0.0.1'
PORT_NUM = 40400

async def tcp_echo_client(message, loop):
    reader, writer = await asyncio.open_connection(HOST_IP, PORT_NUM, loop=loop)

    print('Send: %r' % message)
    writer.write(message.encode())

    data = await reader.read(100)
    print('Received: %r' % data.decode())

    print('Close the socket')
    writer.close()


message = 'close'
loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_echo_client(message=message, loop=loop))
loop.close()


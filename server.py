''' standard server
import socket

HOST_IP = '127.0.0.1'
PORT_NUM = 40400

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST_IP, PORT_NUM))
    s.listen()
    connection, address = s.accept()
    with connection:
        # 'with' statement means that connection will be closed once statement has been exited
        print('Connected by', address)
        while True:
            data = connection.recv(1024)
            if not data:
                break
            connection.sendall(data)
'''

# asynchronous server
import asyncio

HOST_IP = '127.0.0.1'
PORT_NUM = 40400

last_data = None


async def handle_echo(reader, writer):
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
    if message == 'close':
        fut.set_result(0)       # set the future with a result and therefore the connection can close

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    fut = asyncio.Future()
    server_coro = asyncio.start_server(handle_echo, HOST_IP, PORT_NUM, loop=loop)
    server = loop.run_until_complete(asyncio.gather(server_coro, fut))
    # server = loop.run_until_complete(server_coro)
    # Close the server
    # these lines are not needed, the server_coro coroutine has stopped running before the fut value is set
    # this means that the server will always already be closed?
    # server.close()
    # loop.run_until_complete(server.wait_closed())
    loop.close()



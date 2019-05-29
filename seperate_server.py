from server import ServerClass

HOST_IP = '127.0.0.1'
SERVER_PORT_NUM = 40400
CLOSE_STRING = "close"  # close the server to the client

s = ServerClass(HOST_IP, SERVER_PORT_NUM, CLOSE_STRING)
# s.daemon = True  # run as daemon to allow main thread to close and shut off server and client
s.start()

s.join()
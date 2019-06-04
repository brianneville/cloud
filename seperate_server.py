from user import User
import os
from queue import Queue
from colors import color_dict
from user import send, extract, formatmsg, split_dirtext, CLOSE_STRING, format_diroutput
from DFSbackend import DFShandler


def serv_processing(item):
    global seperate_server, FOLDER_PATH, dfs_handler
    print(color_dict['red'] + f"server processing item : {item}" + color_dict['reset'])
    remote_ip, remote_port, msg = extract(item)
    if msg == CLOSE_STRING:
        recv_msg = send(remote_ip, int(remote_port),
                        formatmsg(host_ip=remote_ip, host_portnum=remote_port, item=CLOSE_STRING),
                        recieve=False)
        return
    curr_dir, text = split_dirtext(msg)
    dir_to_change, output = dfs_handler.parse(current_dirpath=curr_dir, msg=text)

    recv_msg = send(remote_ip, int(remote_port),
                   formatmsg(host_portnum=seperate_server.SERVER_PORTNUM,
                             host_ip=seperate_server.HOST_IP,
                             item=format_diroutput(dir_to_change, output)),
                    recieve=False)


def main():
    global seperate_server, dfs_handler, FOLDER_PATH
    DEFAULT_UID = 1401
    dfs_handler = DFShandler(DEFAULT_UID)
    FOLDER_PATH = os.getcwd() + '/' + str(DEFAULT_UID) + "_folder/"
    if not os.path.isdir(FOLDER_PATH):
        os.mkdir(FOLDER_PATH)
    msg_q = Queue()
    seperate_server = User(client_q=msg_q, serv_q=msg_q, HOST_IP='127.0.0.1', SERVER_PORTNUM=12001, DEST_IP='127.0.0.1',
                           REMOTE_PORTNUM=9001, proc_func=serv_processing)
    serv_s, serv_c = seperate_server.start_both()
    serv_s.join()


if __name__ == '__main__':
    main()



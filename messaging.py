

# format the item for sending to its destination.
# send the host ip and portnum so the desination knows how to send the item back
def formatmsg(uid, host_ip, host_portnum,item)->str:
    item = f'UID:{uid}SRCIP:{host_ip}PORT:{host_portnum}MSG:{item}'
    return item


def extract(item)->(str, str, str, str):
    # format is either IP:IP, PORT:PORT, MSG:msg or just msg ( if the message is from the app_instance
    # e.g. IP:127.0.0.1PORT:30120MSG: this is a message that the client is recieving from the server
    # IP and PORT are the IP and port of the server for the client that sent the message
    #  i.e. the ip, port that the server should respond to
    uid_str, ip_str, port_str, msg_str = 'UID:', 'SRCIP:', 'PORT:', 'MSG:'
    uid_start = item.find(uid_str)
    ip_start = item.find(ip_str)
    port_start = item.find(port_str)
    msg_start = item.find(msg_str)

    uid = item[uid_start+len(uid_str):ip_start]
    ip = item[ip_start+len(ip_str):port_start]
    port = item[port_start+len(port_str):msg_start]
    msg = item[msg_start+len(msg_str):]

    return uid, ip, port, msg


# used in the UI to combine the current directory and user-entered text
def combine_dirtext(curr_dir, input_text) -> str:
    return "dir:" + curr_dir + "cmd:" + input_text


# split the item into
def split_dirtext(msg) ->(str, str):
    dir_str, text_str = 'dir:', 'cmd:'
    dir_start = msg.find(dir_str)
    text_start = msg.find(text_str)

    cdir = msg[dir_start+len(dir_str):text_start]
    text = msg[text_start+len(text_str):]
    return cdir, text

# print(extract('IP:127.0.0.1PORT:30120MSG: this is a message that the client is recieving from the server'))


# these functions are used to return the new dir and output for the users terminal to display
def format_diroutput(dir_to_change, output) -> str:
    print("dir change, op = ",dir_to_change, output)
    return "!dircng:" + dir_to_change + "!Outp:" + output


def getchangedir_op(text) ->(str, str):
    dir_str, text_str = '!dircng:', '!Outp:'
    dir_start = text.find(dir_str)
    text_start = text.find(text_str)

    chngdir = text[dir_start+len(dir_str):text_start]
    op = text[text_start+len(text_str):]
    return chngdir, op

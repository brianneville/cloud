import mmh3
import os

import asyncio

import _pickle


# def generate_key(password):
#   return mmh3.hash128(password, 123)

'''
def parsedcommand(func):

    def wrapping_test(*args, **kwargs):  # start returns a function of the coroutine that has progressed to
        print(args)                     # args contains the self DFS object
        #                               kwargs will contain a dictionary of specified arguments
        print(kwargs)
        initialised = func(*args, kwargs['file_path'])
        return initialised

    return wrapping_test
'''


def pickle_obj(fname, graph) ->None:
    # saves the client graph that is being used for the filesystem
    fname = fname
    with open(fname, 'wb') as save_file:
        _pickle.dump(graph, save_file)


def unpickle_obj(fname) ->dict:
    # client opens a pickled object containing a dictionary with their directory structure in it
    fname = fname
    with open(fname, 'rb') as save_file:
        o = _pickle.load(save_file)
    return o


async def tcp_echo_client(send_msg, event_loop) ->None:
    reader, writer = await asyncio.open_connection('127.0.0.1', 40400, loop=event_loop)
    writer.write(send_msg.encode())
    data = await reader.read(100)
    print("data= " + data.decode())
    writer.close()


def parsedcommand(func):
    def wrapper(*args, **kwargs):
        if kwargs['use_open_dir'] == -1:
            initialised = func(*args, kwargs['full_path'])
        else:
            initialised = func(*args, kwargs['current_dirpath'], kwargs['full_path'])
        return initialised

    return wrapper



class DFShandler:

    def __init__(self, uid):
        self.servers_available = None   # the amount of servers avaiable for the client to distribute files on
        self.uid = uid
        self.graph = {
            './': []         # home directory : ["path/folder_x", "path/folder_y" "path/file.txt" etc ]
            #                 format=  dir: [list of files and directories at this location]
        }
        fname = "graph_"+str(uid)
        try:
            self.graph = unpickle_obj(fname)
        except FileNotFoundError:
            pickle_obj(fname, self.graph)

        self.parseoptions = {
            'cd': self.open_dir,
            'home': self.open_dir,
            'back': self.open_dir,
            'get': self.get_file,
            'up': self.upload_file

        }

    def divide_into_chunks(self, filepath) ->(str, list):
        flen = os.path.getsize(filepath)
        pos = filepath.__len__() - filepath[::-1].find('/')
        ext_pos = filepath.find('.')
        fname = filepath[pos:ext_pos]
        ext_type = filepath[ext_pos:]
        chunks_size = round(flen/self.servers_available)
        client_chunks = []
        count, file_indx = 0, 0   # set count to the max chunks size
        new_path = os.getcwd().replace("\\", "/") + f"/user_{self.uid}/"     # put all user chunks into the uid folder
        if not os.path.isdir(new_path):
            os.mkdir(new_path, 0o777)

        with open(filepath, 'rb') as srcfile:
            fbyte = srcfile.read(1)
            while fbyte != b'':
                print(fbyte)
                if not count:
                    count = chunks_size
                    try:
                        opfile.close()
                    except UnboundLocalError:
                        print("unbound local error caught, file was not created ")
                    client_chunks.append( new_path + "/" + fname + str(file_indx) + ext_type)
                    opfile = open(client_chunks[file_indx], 'wb')
                    file_indx += 1

                opfile.write(fbyte)
                count -= 1
                fbyte = srcfile.read(1)
                print(count, chunks_size)
        opfile.close()
        return fname, client_chunks

    async def send_chunks(self, fname, client_chunks):
        pass

    @parsedcommand
    async def upload_file(self, filepath):
        #   asynchronously upload all files to server
        fname, client_chunks = self.divide_into_chunks(filepath)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_chunks(fname, client_chunks))  # ?
        loop.close()

    @parsedcommand
    def open_dir(self, new_dir_path):
        return self.graph[new_dir_path] # dir_path has values eg: "./" or "./folder1/folder2/" or "./diffolder1/"

    @parsedcommand
    def get_file(self, file_path):
        # retrieve file from servers online
        print(f"file patth recieved!! {file_path}")
        pass

    @parsedcommand
    def add_to_folder(self, dirpath, filepath):     # dir path of parent folder
        curr = self.graph[dirpath]
        curr.append(filepath)
        self.graph[dirpath] = curr
        # TODO: upload_file

    @parsedcommand
    def remove_from_folder(self, dirpath, filepath):
        curr = self.graph[dirpath]
        curr.remove(filepath)
        self.graph[dirpath] = curr
        # TODO: send delete message to servers


    def parse(self, msg, current_dirpath):
        # parses an item from the queue
        # format guide:
        # msg example: cd subfolder_1
        # home - go back to the . directory (home)
        # cd - change directory to a sub directory
        # back - return to the parent directory unless at home
        # get - downlaod a file from a directory
        # up - upload a file from your pc to the servers
        full_path = None    # full path is the entire path for the file or dir to be used for indexing the graph dict
        space_pos = msg.find(' ')
        subject = msg[space_pos+1:] if space_pos >= 0 else None     # ex subfolder1
        command = msg[:space_pos] if space_pos >= 0 else msg        # ex cd
        if command == 'cd':
            space_pos = -1      # use this to signify that we just want to open a directory and not change any files
        if msg[-1:] == '/' or (subject is not None and subject.find('.') >= 0):
            full_path = current_dirpath + subject

        self.parseoptions[command](use_open_dir=space_pos, current_dirpath=current_dirpath, full_path=full_path)

        print(space_pos, command, subject, full_path)


dfs = DFShandler(uid=1234)
dfs.servers_available = 3
# dfs.divide_into_chunks('D:/Users/Brian/PycharmProjects/dfs/undivided.txt')
dfs.parse('cd sub1/', './parent/')

# dfs.get_file(file_path='./f1/f2/', testing= 1)
# dump_client_graph( str(dfs.uid),graph0)
# graph2 = load_client_graph(str(dfs.uid))
# print(graph2)

# TODO: things to do for distributed file system:
# 1. generate secure private key to encyrpt user data
#       - generate public
# 2. chunk = key XOR data_segment   - this is used to encrypt the data so that it can be distributed safely
#       make segment size =  65535 - 20 bytes = 65515 bytes (max payload of ipv4 header)
# 3. track which users/servers are going to be sent the chunk
#       - keep a dictionary of {chunk_id, [(uid_1002), (uid_2321), (uid_78) ... (uid_34) ]}
#       - keep another dictionary mapping each of these uid numbers to IP and PORT numbers
#       - first try downloaded from uid_1002; if no connection to user, then the user offline; retry with uid_2332, etc
























# TODO: things to do for torrenting and distributed filesystem:
# goal: make a distributed file system where files are torrented between users
# 1. generate secure private key to encyrpt user data
#       - generate public
# 2. chunk = key XOR data_segment   - this is used to encrypt the data so that it can be distributed safely
#       make segment size =  65535 - 20 bytes = 65515 bytes (max payload of ipv4 header)
# 3. track which users are going to be sent the chunk
#       - keep a dictionary of {chunk_id, [(uid_1002), (uid_2321), (uid_78) ... (uid_34) ]}
#       - keep another dictionary mapping each of these uid numbers to IP and PORT numbers
#       - first try downloaded from uid_1002; if no connection to user, then the user offline; retry with uid_2332, etc
# 4. goal would be to send each chunk to p users:
#       where p is the probability that any user will be online at any time
# 5. to download file again:
#       - go through virtual file system to locate the file you want to open
#           - parse input from ui to distinguish between opening files and traversing directories
#       - this can be done by traversing a linked list?
#       - select a file to open
#       - go through dictionaries to find the IP addresses and port numbers and request chunks
#
# how to handle churn:
# send out the files to groups of users. (pods). when a pod is assigned, a twin-pod is also created
# when a member of the pod is closing the application, it should notify the other members of its pod.
# upon notification, the


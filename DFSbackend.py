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

HOME_DIR_NAME = '_/'


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

open_dir_args = ['full_path','back_dirpath','home']


def parsedcommand(func):
    def wrapper(*args, **kwargs):
        if kwargs['open_dir_choice'] >= 0:
            chosen_arg = open_dir_args[kwargs['open_dir_choice']]
            print(chosen_arg)
            initialised = func(*args, kwargs[chosen_arg])

        else:
            initialised = func(*args, kwargs['current_dirpath'], kwargs['full_path'])
        return initialised

    return wrapper


def get_backpath(command) ->str:
    command = command[:-1:]
    end = command.rfind('/')
    return command[:end + 1:]


class DFShandler:

    def __init__(self, uid):
        self.servers_available = None   # the amount of servers avaiable for the client to distribute files on
        self.uid = uid
        self.graph = {
            HOME_DIR_NAME: []         # home directory : ["path/folder_x", "path/folder_y" "path/file.txt" etc ]
            #                 format=  dir: [list of files and directories at this location]
        }
        fname = "graph_"+str(uid)
        try:
            self.graph = unpickle_obj(fname)
        except FileNotFoundError:
            pickle_obj(fname, self.graph)

        self.parseoptions = {       # 'key':
            'cd': self.open_dir,
            'home': self.open_dir,
            'back': self.open_dir,
            'get': self.get_file,
            'up': self.upload_file,
            'fnew': self.add_to_folder,
            'fdel': self.remove_from_folder
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
        print(f'new dir to open={new_dir_path}')

        # return self.graph[new_dir_path] # dir_path has values eg: "./" or "./folder1/folder2/" or "./diffolder1/"

    @parsedcommand
    def get_file(self, file_path):
        # retrieve file from servers online
        print(f"file to get: {file_path}")

    @parsedcommand
    def add_to_folder(self, dirpath, filepath):     # dir path of parent folder
        # add an item to a parent folder
        print(f"parent folder {dirpath}, new file name = {filepath}")
        pass
        curr = self.graph[dirpath]
        curr.append(filepath)
        self.graph[dirpath] = curr
        # TODO: upload_file

    @parsedcommand
    def remove_from_folder(self, dirpath, filepath):
        # remove an item from a parent folder
        print(f"parent folder {dirpath}, file to remove name = {filepath}")
        pass
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
        # fnew - create a new folder
        # fdel - delete a folder
        full_path = None    # full path is the entire path for the file or dir to be used for indexing the graph dict
        space_pos = msg.find(' ')
        subject = msg[space_pos+1:] if space_pos >= 0 else None     # ex subfolder1
        command = msg[:space_pos] if space_pos >= 0 else msg        # ex cd
        if msg[-1:] == '/' or (subject is not None and subject.find('.') >= 0):
            full_path = current_dirpath + subject

        # when using open dir commands, 0 is open sub dir, 1 is back, 2 is home
        use_cur_dir = msg.find('cd')
        use_cur_dir = 1 if not msg.find('back') else use_cur_dir    # 'if not find' will be true if back is at the start
        use_cur_dir = 2 if not msg.find('home') else use_cur_dir        # of the msg
        # default value for none of these commads found is -1

        self.parseoptions[command](
            open_dir_choice=use_cur_dir,
            current_dirpath=current_dirpath,
            home=HOME_DIR_NAME,
            back_dirpath=None if command != 'back' else get_backpath(current_dirpath),
            full_path=full_path
        )
        # yeah i know this might not be incredibly efficient/perfect but i just wanted to use decorators


dfs = DFShandler(uid=1234)
dfs.servers_available = 3
# dfs.divide_into_chunks('D:/Users/Brian/PycharmProjects/dfs/undivided.txt')
# dfs.parse('cd sub2/', '_/parent/sub1/')
# dfs.parse('home', '_/parent/sub1/')
# dfs.parse('back', '_/parent/sub1/')
# dfs.parse('get filena.dat', './parent/sub1/')
# dfs.parse('up c:/users/brn/filex.txt', './parent/sub1/')

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


import os
import asyncio
import _pickle
from colors import color_dict

HOME_DIR_NAME = '_/'
DO_NOT_CHANGE_CURRDIR = '~'


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


def parsedcommand(func)->object:
    def wrapper(*args, **kwargs):
        d = []
        relevant_ones = kwargs['relevant_kwargs']
        for k in relevant_ones:
            d.append(kwargs[k])
        return func(args[0], *d)       # flatten out list

    return wrapper


def get_backpath(command) ->str:
    command = command[:-1:]
    end = command.rfind('/')
    return command[:end + 1:]


def getfiles_frompaths(flist)->str:
    files_str = ''
    for path in flist:
        path = path[:-1:]  # get the last part of the path
        path = path[path.rfind('/') + 1:] + '/' + '\n'
        files_str += path
    return files_str

class DFShandler:

    def __init__(self, uid):
        self.servers_available = None   # the amount of servers avaiable for the client to distribute files on
        self.uid = uid
        self.graph = {
            HOME_DIR_NAME: []         # home directory : ["path/folder_x", "path/folder_y" "path/file.txt" etc ]
            #                 format=  dir: [list of files and directories at this location]
        }
        self.fname = "graph_"+str(uid)
        try:
            self.graph = unpickle_obj(self.fname)
            pass
        except FileNotFoundError:
            pickle_obj(self.fname, self.graph)

        self.parseoptions = {       # 'key': (function, kwargs)
            'cd': (self.open_dir, ['full_path']),
            'home': (self.open_dir, ['home']),
            'back': (self.open_dir, ['back_dirpath']),
            'get': (self.get_file, ['full_path']),
            'up': (self.upload_file, ['subject']),
            'fnew': (self.add_folder, ['current_dirpath', 'full_path']),
            'fdel': (self.remove_folder, ['current_dirpath', 'full_path']),
            'help': (self.display_help, [])
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
    def upload_file(self, filepath):        # make this async def if needed ?
        #   asynchronously upload all files to server
        print(f'new file to uplaod from user={filepath}')
        pass
        '''
        fname, client_chunks = self.divide_into_chunks(filepath)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_chunks(fname, client_chunks))  # ?
        loop.close()
        '''

    @parsedcommand
    def get_file(self, file_path):
        # retrieve file from servers online
        print(f"file to get: {file_path}")


    @parsedcommand
    def open_dir(self, new_dir_path):
        print(f'new dir to open={new_dir_path}')
        if new_dir_path[len(new_dir_path)-1] != '/':
            new_dir_path += '/'
        flist_here = self.graph[new_dir_path]
        if not flist_here:
            return new_dir_path, 'This folder is empty'
        else:
            return new_dir_path, getfiles_frompaths(flist_here)


        # return self.graph[new_dir_path] # dir_path has values eg: "./" or "./folder1/folder2/" or "./diffolder1/"
    @parsedcommand
    def add_folder(self, dirpath, folderpath):     # dir path of parent folder
        # add an item to a parent folder
        print(f"parent folder {dirpath}, new file path = {folderpath}")   # file can also be a f
        if folderpath == '~':
            print(color_dict['cyan'] + "this folder could not be created" + color_dict['reset'])
            return DO_NOT_CHANGE_CURRDIR, "please retry making the folder. e.g. fnew myfolder/"
        curr_parent_files = self.graph[dirpath]
        curr_parent_files.append(folderpath)
        self.graph[folderpath] = []
        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)  # save the new directory structure
        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)


    @parsedcommand
    def remove_folder(self, dirpath, folderpath):
        # remove an item from a parent folder
        print(f"parent folder {dirpath}, file to remove path = {folderpath}")
        if folderpath == '~':
            print(color_dict['cyan'] + "this folder could not be created" + color_dict['reset'])
            return DO_NOT_CHANGE_CURRDIR, "please retry deleting the folder. e.g. fdel myfolder/"
        curr_parent_files = self.graph[dirpath]
        curr_parent_files.remove(folderpath)
        self.graph.pop(folderpath)
        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)          # save the new directory structure
        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)
        # TODO: send delete message to servers

    @parsedcommand
    def display_help(self):      # returns:  'directory to change current dir to if any' , output
        return DO_NOT_CHANGE_CURRDIR, """                              
    _________format guide_________________________
    msg example: cd subfolder_1     
    home - go back to the _/ directory (home)        
    cd - change directory to a sub directory         
    back - return to the parent directory           
    get - downlaod a file from a directory          
    up - upload a file from your pc to a folder   
    fnew - create a new folder                       
    fdel - delete a folder                           
    
    __examples____________
    home
    cd subfolder_1
    back
    get file.txt
    up c:/users/u/file.dat
    fnew myfolder
    fdel myfolder
        """

    def parse(self, msg, current_dirpath) ->(str, str):
        # parses an item from the queue
        # format guide:
        # msg example: cd subfolder_1
        # home - go back to the _/ directory (home)
        # cd - change directory to a sub directory
        # back - return to the parent directory unless at home
        # get - downlaod a file from a directory
        # up - upload a file from your pc to the servers
        # fnew - create a new folder
        # fdel - delete a folder
        full_path = DO_NOT_CHANGE_CURRDIR
        # full path is the entire path for the file or dir to be used for indexing the graph dict
        space_pos = msg.find(' ')
        subject = msg[space_pos+1:] if space_pos >= 0 else None     # ex subfolder1
        command = msg[:space_pos] if space_pos >= 0 else msg        # ex cd
        if msg[-1:] == '/' or (subject is not None and subject.find('.') >= 0):
            full_path = current_dirpath + subject
        try:
            func, args = self.parseoptions[command]

            output = func(
                relevant_kwargs=args,
                current_dirpath=current_dirpath,
                home=HOME_DIR_NAME,
                back_dirpath=None if command != 'back' else get_backpath(current_dirpath),
                full_path=full_path,
                subject=subject
            )
            return output[0], output[1]
        except KeyError:
            return DO_NOT_CHANGE_CURRDIR, "INVALID ARG [type: 'help' to see commands]"
        # yeah i know this might not be incredibly efficient/perfect? but i just wanted to use decorators

"""
dfs = DFShandler(uid=1234)
dfs.servers_available = 3
# dfs.divide_into_chunks('D:/Users/Brian/PycharmProjects/dfs/undivided.txt')

# testing the file parsing
dfs.parse('cd sub2/', '_/parent/sub1/')
dfs.parse('home', '_/parent/sub1/')
dfs.parse('back', '_/parent/sub1/')
dfs.parse('get filena.dat', './parent/sub1/')
dfs.parse('up c:/users/brn/filex.txt', './parent/sub1/')
dfs.parse('fnew folder101/', './parent/sub1/')
dfs.parse('fdel folder101/', './parent/sub1/')

"""


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


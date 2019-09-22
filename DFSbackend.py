import asyncio
import _pickle
import os
import shutil

from colors import color_dict
from messaging import extract_uploadfile, LOGIN_FAIL, LOGIN_PASS


HOME_DIR_NAME = '_/'
DO_NOT_CHANGE_CURRDIR = '~'

back_string = '\n\n use the back command to return to the previous screen'


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
    # print("data= " + data.decode())
    writer.close()


def parsedcommand(func)->object:
    def wrapper(*args, **kwargs):
        d = []
        relevant_ones = kwargs['relevant_kwargs']
        for k in relevant_ones:
            d.append(kwargs[k])
        return func(args[0], *d)       # unzip list

    return wrapper


def get_backpath(command) ->str:
    command = command[:-1:]
    end = command.rfind('/')
    return command[:end + 1:]


def getfiles_frompaths(flist)->str:
    files_str = ''
    for path in flist:
        if path.find('.') < 0:
            # then we know that the path is a directory
            path = path[:-1:]  # get the last part of the path
            path = path[path.rfind('/') + 1:] + '/'
        path += '\n'
        files_str += path
    return files_str


def add_str(base, dir)->str:
    # allow the user to do the logical thing and enter 'back' to get out of help/popups
    return base+'/' if dir[-1:] == '/' else '--' + base + '/'


def removechildren(graph, curr_vals_list, popdirs, folderpath, uidfolderpath):
    for v in curr_vals_list:
        if v in graph:
            # print(color_dict['cyan'] + f'v is {v}' + color_dict['reset'])
            # then v is the path of a subfolder. remove its subfolders
            removechildren(graph, graph[v], popdirs, v, uidfolderpath)
            if popdirs:
                # print(f'popping the graph entry at {v}')
                graph.pop(v)
        elif not popdirs:
            # print(f"removing the file {v} from dir: {folderpath}. "
                # f"removing: {uidfolderpath + folderpath.replace('/', '¿') + v}")

            # value has no key in graph. therefore it is file. remove and delete
            filepath = uidfolderpath + folderpath.replace('/', '¿') + v
            # print(color_dict['cyan']+f'removing filepath {filepath}' + color_dict['reset'])
            os.remove(filepath)


class DFShandler:

    def __init__(self, uid, FOLDER_PATH):
        self.servers_available = None   # the amount of servers avaiable for the client to distribute files on
        self.uid = uid
        self.graph = {
            HOME_DIR_NAME: []         # home directory : ["path/folder_x", "path/folder_y" "path/file.txt" etc ]
            #                 format=  dir: [list of files and directories at this location]
        }
        self.folder_path = FOLDER_PATH
        self.fname = FOLDER_PATH + "graph_"+str(uid)
        try:
            self.graph = unpickle_obj(self.fname)
            pass
        except FileNotFoundError:
            pickle_obj(self.fname, self.graph)

        self.parseoptions = {       # 'key': (function, kwargs)
            'login': (self.login, ['subject']),
            'home': (self.open_dir, ['home']),
            'cd': (self.open_dir, ['full_path']),
            'back': (self.open_dir, ['back_dirpath']),
            'get': (self.get_file, ['current_dirpath', 'full_path']),
            'up': (self.upload_file, ['current_dirpath', 'subject']),
            'sv': (self.save_file, ['current_dirpath', 'subject']),
            'new': (self.new_file, ['current_dirpath', 'subject']),
            'del': (self.delete_file, ['current_dirpath', 'subject']),
            'fnew': (self.add_folder, ['current_dirpath', 'full_path']),
            'fdel': (self.remove_folder, ['current_dirpath', 'full_path']),
            'SELF-DELETE': (self.self_delete, []),
            'help': (self.display_help, ['current_dirpath'])

        }
    @parsedcommand
    def login(self, subject):
        # subject is password in hashed form
        login_folderpath = self.folder_path + '/login/'
        login_filepath = login_folderpath + 'login.txt'
        if not os.path.isdir(login_folderpath):
            # initially making account - create folder, initialise with password hash
            os.mkdir(login_folderpath, 0o777)
            with open(login_filepath, 'w+') as f_init:
                f_init.write(subject)
                return DO_NOT_CHANGE_CURRDIR, LOGIN_PASS
        else:
            with open(login_filepath, 'r') as f_compare:
                if f_compare.readline() == subject:
                    return DO_NOT_CHANGE_CURRDIR, LOGIN_PASS
                else:
                    return DO_NOT_CHANGE_CURRDIR, LOGIN_FAIL

    @parsedcommand
    def upload_file(self, dirpath, subject):        # make this async def if needed ?
        #   asynchronously upload all files to server
        # print(f'new file to uplaod from user is {subject} upload into current dir: {dirpath}')
        fname, contents = extract_uploadfile(subject)

        curr_parent_files = self.graph[dirpath]
        curr_parent_files.append(fname)

        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)  # save the new directory structure

        # replace so that new subfolders dont have to be created
        full_name = dirpath.replace("/", "¿") + fname
        server_fname = self.folder_path + full_name
        with open(server_fname, 'w+') as fout:
            for line in contents:
                fout.write(line)

        '''
        fname, client_chunks = self.divide_into_chunks(filepath)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_chunks(fname, client_chunks))  # ?
        loop.close()
        '''
        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)

    @parsedcommand
    def get_file(self, dirpath, file_path):     # here filepath is full path
        # retrieve file from servers online and display it in the output box on the terminal
        if file_path == '':
            return
        serv_filepath = self.folder_path + file_path.replace("/", "¿")
        output = ''
        if os.path.exists(serv_filepath):
            with open(serv_filepath, 'r') as fin:
                for line in fin:
                    output += line
            return file_path, output
        return dirpath+add_str('404', dirpath), 'File not found' + back_string

    @parsedcommand
    def save_file(self, filepath, subject):
        # user wants to save the string 'subject' into the file at dirpath.replace("/", "¿")
        serv_filepath = self.folder_path + filepath.replace("/", "¿")
        if os.path.exists(serv_filepath):
            with open(serv_filepath, 'w') as fout:
                for line in subject:
                    fout.write(line)
        else:
            return filepath+add_str('sv', filepath), 'unable to save, please open a file using the get command' \
                   + back_string
        return filepath, subject

    @parsedcommand
    def open_dir(self, new_dir_path):
        # print(f'new dir to open={new_dir_path}')
        if new_dir_path == '':
            return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(self.graph[HOME_DIR_NAME])
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
        # print(f"parent folder {dirpath}, new file path = {folderpath}")   # file can also be a f
        if folderpath == '~':
            # print(color_dict['cyan'] + "this folder could not be created" + color_dict['reset'])
            return dirpath + add_str('fnew', dirpath), "please retry making the folder. e.g. fnew myfolder/" \
                   + back_string
        curr_parent_files = self.graph[dirpath]
        curr_parent_files.append(folderpath)
        self.graph[folderpath] = []
        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)  # save the new directory structure
        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)

    @parsedcommand
    def remove_folder(self, dirpath, folderpath):
        if folderpath == '~':
            # print(color_dict['cyan'] + "this folder could not be deleted" + color_dict['reset'])
            return dirpath + add_str('fdel', dirpath), "please retry deleting the folder. e.g. fdel myfolder/"\
                   +back_string
        curr_parent_files = self.graph[dirpath]
        if folderpath not in curr_parent_files:
            return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files) + "\n\n Please retry deleting" \
                                         " the folder, Ensuring to spell the folder name correctly.\n " \
                                         " Note: use the del command to delete files, and fdel to delete folders " \
                    + back_string

        removechildren(self.graph, self.graph[folderpath], False, folderpath, self.folder_path) # delete the files
        removechildren(self.graph, self.graph[folderpath], True, folderpath, self.folder_path) # pop the folders

        curr_parent_files.remove(folderpath)
        self.graph.pop(folderpath)
        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)          # save the new directory structure

        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)

    @parsedcommand
    def new_file(self, dirpath, subject):
        # add a new txt file to the parent folder
        if subject.find('.txt') < 0:
            subject += '.txt'
        curr_parent_files = self.graph[dirpath]
        curr_parent_files.append(subject)
        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)  # save the new directory structure

        # create a new empty file
        serv_filepath = self.folder_path + dirpath.replace("/", "¿") + subject
        with open(serv_filepath, 'w+'):
            pass

        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)

    @parsedcommand
    def delete_file(self, dirpath, filepath):
        if filepath == '~':
            # print(color_dict['cyan'] + "this file could not be deleted" + color_dict['reset'])
            return dirpath + add_str('del', dirpath), "please retry deleting the file. e.g. del myfile.txt"
        curr_parent_files = self.graph[dirpath]
        try:
            curr_parent_files.remove(filepath)
        except ValueError:
            return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files) + "\n\n Please retry deleting" \
                " the file, Ensuring to spell the filename correctly.\n " \
                " Note: use the del command to delete files, and fdel to delete folders " \
                + back_string
        self.graph[dirpath] = curr_parent_files
        pickle_obj(self.fname, self.graph)          # save the new directory structure
        serv_filepath = (dirpath+ filepath).replace("/", "¿")
        os.remove(self.folder_path + serv_filepath)
        return DO_NOT_CHANGE_CURRDIR, getfiles_frompaths(curr_parent_files)

    @parsedcommand
    def self_delete(self):
        if os.path.exists(self.folder_path):
            shutil.rmtree(self.folder_path)
            self.graph.clear()
        return DO_NOT_CHANGE_CURRDIR, 'account deleted, please make a new one and login to home again'

    @parsedcommand
    def display_help(self, dirpath):      # returns:  'directory to change current dir to if any' , output#
        #     msg example: cd subfolder_1

        return dirpath + add_str('help', dirpath), """                              
    _________format guide_________________________
    home - go back to the _/ directory (home)        
    cd - change directory to a sub directory         
    back - return to the parent directory           
    get - downlaod a file from a directory          
    up - upload a file from your pc to a folder
    new - create a new text file 
    sv - save changes to an open text file
    del - delete a file   
    fnew - create a new folder                       
    fdel - delete a folder                           
    SELF-DELETE - irrevesibly delete an account 
        (all user data will be deleted)    
    
    __examples____________
    home
    cd subfolder_1
    back
    get file.txt
    up c:/users/u/file.dat
    new myfile
    del myfile.txt
    sv 
    fnew myfolder
    fdel myfolder
    SELF-DELETE
        """

    def parse(self, msg, current_dirpath) ->(str, str):
        # parses an item from the queue
        full_path = DO_NOT_CHANGE_CURRDIR
        # full path is the entire path for the file or dir to be used for indexing the graph dict
        space_pos = msg.find(' ')
        subject = msg[space_pos+1:] if space_pos >= 0 else ''     # ex subfolder1
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
            return current_dirpath + add_str('help', current_dirpath), "INVALID ARG [type: 'help' to see commands]"
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

'''
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
                client_chunks.append(new_path + "/" + fname + str(file_indx) + ext_type)
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
'''
# yes i know this is a confusing/irrelevant for a classname
# ( i was orininally planning on making this system fully distributed, hence the name)

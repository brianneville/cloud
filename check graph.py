# jus used for chcking that a foder has been entirely recursively deleted

import _pickle


def unpickle_obj(fname) ->dict:
    # client opens a pickled object containing a dictionary with their directory structure in it
    fname = fname
    with open(fname, 'rb') as save_file:
        o = _pickle.load(save_file)
    return o


print(unpickle_obj('D:/Users/Brian/PycharmProjects/dfs/a_folder/graph_a'))
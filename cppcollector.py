
import os, sys
from os import path

cpp_exts = ['cpp', 'cxx', 'c', 'cc', 'c++']
o_exts = ['o']

def get_files(dirpath, allowed_exts):
    def allowedfile(f):
        ext = f.split(path.extsep)[-1]
        return ext in allowed_exts

    dirpath = path.normpath(dirpath) # on windows replace '/' by '\\'
    dirpath = path.abspath(dirpath)
    if not path.exists(dirpath): raise Exception("target directory \"{}\" does not exist!".format(dirpath))

    allf = [path.join(dp, f) for dp, dn, fn in os.walk(dirpath) for f in fn]
    return list(filter(allowedfile, allf))

if __name__ == '__main__':
    srcdir = sys.argv[1]
    files = get_files(srcdir)
    for f in files: print(f)
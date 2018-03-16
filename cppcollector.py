
import os, sys
from os import path

allowed_ext = ['cpp', 'cxx', 'c']
def is_file_cpp(f):
    ext = f.split(path.extsep)[-1]
    return ext in allowed_ext
def get_files(dirpath):
    allf = [path.join(dp, f) for dp, dn, fn in os.walk(dirpath) for f in fn]
    return list(filter(is_file_cpp, allf))

if __name__ == '__main__':
    srcdir = sys.argv[1]
    srcdir = path.normpath(srcdir) # on windows replace '/' by '\\'
    srcdir = path.abspath(srcdir)
    
    files = get_files(srcdir)
    for f in files: print(f)
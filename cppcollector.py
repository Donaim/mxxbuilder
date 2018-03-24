
import os, sys
from os import path

cpp_exts = ['cpp', 'cxx', 'c', 'cc', 'c++']
h_exts = ['h', 'hh', 'tcc', 'txx'] # +templates
o_exts = ['o']

def get_endswith(dirpath, endings):
    def filt(f):
        for e in endings:
            if f.endswith(e): return True
        return False
    return get_filtered(dirpath, filt)
def get_files(dirpath, allowed_exts):
    def filt(f):
        ext = f.split(path.extsep)[-1]
        return ext in allowed_exts
    return list(get_filtered(dirpath, filt))
def get_filtered(dirpath, allowed_filter):
    dirpath = path.normpath(dirpath) # on windows replace '/' by '\\'
    dirpath = path.abspath(dirpath)
    
    allf = [path.join(dp, f) for dp, dn, fn in os.walk(dirpath) for f in fn]
    return filter(allowed_filter, allf)

if __name__ == '__main__':
    srcdir = sys.argv[1]
    files = get_files(srcdir)
    for f in files: print(f)
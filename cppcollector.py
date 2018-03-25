
import os, sys
from os import path

cpp_exts = ['cpp', 'cxx', 'c', 'cc', 'c++']
h_exts = ['h', 'hh', 'tcc', 'txx'] # +templates
o_exts = ['o']

def endswith_rule(f, endings):
    for e in endings:
        if f.endswith(e): return True
    return False
def get_endswith(dirpath, endings):
    def filt(f): return endswith_rule(f, endings)
    return get_filtered(dirpath, filt)

def extension_rule(f, allowed_exts):
    ext = f.split(path.extsep)[-1]
    return ext in allowed_exts
def get_files(dirpath, allowed_exts):
    def filt(f): return extension_rule(f, allowed_exts)
    return list(get_filtered(dirpath, filt))
    
def get_filtered(dirpath, allowed_filter):
    dirpath = path.normpath(dirpath) # on windows replace '/' by '\\'
    dirpath = path.abspath(dirpath)
    
    return filter(allowed_filter, get_all(dirpath))
def get_all(dirpath):
    return [path.join(dp, f) for dp, dn, fn in os.walk(dirpath) for f in fn]

if __name__ == '__main__':
    srcdir = sys.argv[1]
    files = get_files(srcdir)
    for f in files: print(f)
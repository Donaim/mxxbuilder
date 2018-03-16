
import sys, os
from os import path

import cppcollector

class cxxbuilder(object):
    def __init__(self, targetdir):
        targetdir = path.abspath(path.normpath(targetdir))
        self.sourcedir = targetdir
        self.rootdir = path.normpath(path.join(self.sourcedir, '..')) # one up
        self.builddir = path.join(self.rootdir, 'build')
        if not path.exists(self.builddir): os.makedirs(self.builddir)

        self.sources = cppcollector.get_files(self.sourcedir, cppcollector.cpp_exts)

        self.newsources = list(filter(self.is_file_new, self.sources))

    def get_target_o_path(self, src_file):
        relpath     = path.relpath(src_file, self.sourcedir)
        targetpath  = path.join(self.builddir, relpath)
        curr_ext    = targetpath.split(path.extsep)[-1]
        new_ext     = 'o'
        targetpath  = (targetpath[:-len(curr_ext)]) + new_ext
        
        targetdir = path.dirname(targetpath)
        if not path.exists(targetdir): os.makedirs(targetdir)
        
        return targetpath
    def is_file_new(self, src_file):
        '''
        if .cpp source file needs to be recompiled -> True \n
        else                                       -> False
        '''

        targeto = self.get_target_o_path(src_file)

        if not path.exists(targeto): return True
        
        # Check if .cpp file was modified after .o file
        if path.getmtime(src_file) > path.getmtime(targeto): return True
        
        return False

if __name__ == '__main__':
    targetdir = sys.argv[1]
    cxx = cxxbuilder(targetdir)
    # print(cxx.sources)
    # targets = map(cxx.get_target_o_path, cxx.sources)
    # print(list(targets))
    newf = cxx.newsources
    print(newf)

    print("END")

import sys, os
from os import path
import subprocess
import time

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

    def get_reltoroot_path(self, src_file):
        return path.relpath(src_file, self.rootdir)
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
    def compile_new(self):
        print("compilation::start")
        start_time = time.process_time()

        for f in self.newsources:
            targeto = self.get_target_o_path(f)
            print("{} -> {}".format(self.get_reltoroot_path(f), self.get_reltoroot_path(targeto)))
            subprocess.check_call(['g++', '-c', f, '-o', targeto])

        print("compilation::finish in {}s with {} files\n".format(time.process_time() - start_time, len(self.newsources)))
    def linkall(self):
        outputs = cppcollector.get_files(self.builddir, cppcollector.o_exts)
        output_exe_path = path.join(self.builddir, "a.exe")
        
        command = ['g++'] + ['-o', output_exe_path] + outputs
        print("linking::start with \"{}\"".format(' '.join(map(lambda f: self.get_reltoroot_path(f) if path.isabs(f) else f, command))))
        start_time = time.process_time()
        
        subprocess.check_call(command)

        print("linking::end in {}s with output in {}\n".format(time.process_time() - start_time, output_exe_path))

if __name__ == '__main__':
    targetdir = sys.argv[1]
    cxx = cxxbuilder(targetdir)
    cxx.compile_new()
    cxx.linkall()

    print("cxxbuild::end")
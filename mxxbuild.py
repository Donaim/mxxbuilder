
import sys, os
from os import path
import subprocess
import time
import argparse

import cppcollector

class mxxbuilder(object):
    def __init__(self, targetdir):
        targetdir = path.abspath(path.normpath(targetdir))
        self.sourcedir = targetdir
        if not path.exists(self.sourcedir): raise Exception("targetdir \"{}\" does not exist!".format(self.sourcedir))
  
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
    def get_output_exe_path(self):
        return path.join(self.builddir, "a.exe")
    def is_file_new(self, src_file):
        '''
        if .cpp file needs to be recompiled -> True \n
        else                                -> False
        '''

        targeto = self.get_target_o_path(src_file)

        if not path.exists(targeto): return True
        
        # Check if .cpp file was modified after .o file
        if path.getmtime(src_file) > path.getmtime(targeto): return True
        
        return False
    def compile_new(self, options):
        if options is None: options = []

        print("compilation::start{}".format('' if len(options) < 1 else ' with options={}'.format(options)))
        start_time = time.process_time()

        for f in self.newsources:
            targeto = self.get_target_o_path(f)
            print("\t{} -> {}".format(self.get_reltoroot_path(f), self.get_reltoroot_path(targeto)))
            subprocess.check_call(['g++'] + options + ['-c', f, '-o', targeto])

        print("compilation::finish in {}s with {} files\n".format(time.process_time() - start_time, len(self.newsources)))
    def linkall(self, options = None):
        if options is None: options = []

        outputs = cppcollector.get_files(self.builddir, cppcollector.o_exts)
        output_exe_path = self.get_output_exe_path()
        
        command = ['g++'] + options + ['-o', output_exe_path] + outputs
        print("linking::start with \"{}\"".format(' '.join(map(lambda f: self.get_reltoroot_path(f) if path.isabs(f) else f, command))))
        start_time = time.process_time()
        
        subprocess.check_call(command)

        print("linking::end in {}s with output in {}\n".format(time.process_time() - start_time, output_exe_path))
    def runexe(self):
        subprocess.call(self.get_output_exe_path())

def parse_args():
    parser = argparse.ArgumentParser(prefix_chars='+')
    parser.add_argument('targetdir')
    parser.add_argument('++copts', help='compiler options', nargs='+')
    parser.add_argument('++lopts', help='linker options', nargs='+')


    parser.add_argument('++compile', dest='compile', action='store_true')
    parser.add_argument('++no-compile', dest='compile', action='store_false')
    parser.set_defaults(compile=True)
    parser.add_argument('++link', dest='link', action='store_true')
    parser.add_argument('++no-link', dest='link', action='store_false')
    parser.set_defaults(link=True)

    parser.add_argument('++autorun', dest='autorun', action='store_true')
    parser.set_defaults(autorun=False)

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    mxx = mxxbuilder(args.targetdir)

    if args.compile:
        mxx.compile_new(args.copts)
    
    if args.link:
        mxx.linkall(args.lopts)

    print("mxxbuild::end")

    if args.autorun:
        mxx.runexe()
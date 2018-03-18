
import os
path = os.path

import subprocess
import time
import argparse

import cppcollector

class mxxbuilder(object):
    def __init__(self, args):
        self.args = args
        self.out = args.out

        self.exclude = list( map(lambda f: path.normpath(f), args.exclude) )

        self.targetpath = path.abspath(path.normpath(args.targetpath))
        if not path.exists(self.targetpath): raise Exception("targetpath \"{}\" does not exist!".format(self.targetpath))
        if path.isdir(self.targetpath):
            self.targetdir = self.targetpath
        else:
            self.targetdir = path.dirname(self.targetpath)

        self.rootdir = path.normpath(path.join(self.targetdir, '..')) # one up
        self.builddir = path.join(self.rootdir, 'build')

    def init_build_dir(self):
        if not path.exists(self.builddir): os.makedirs(self.builddir)
    def get_reltoroot_path(self, src_file):
        return path.relpath(src_file, self.rootdir)
    def get_target_o_path(self, src_file):
        curr_ext    = src_file.split(path.extsep)[-1]
        if curr_ext == 'h':
            return src_file + '.gch'
        else:
            relpath     = path.relpath(src_file, self.targetdir)
            targetpath  = path.join(self.builddir, relpath)
        
            new_ext     = 'o'
            targetpath  = (targetpath[:-len(curr_ext)]) + new_ext
            
            targetdir = path.dirname(targetpath)
            if not path.exists(targetdir): os.makedirs(targetdir)
            
            return targetpath
    def get_output_exe_path(self):
        if self.out is None: 
            return path.join(self.builddir, "a.exe")
        else:
            return self.out
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
    def get_target_files(self):
        if path.isdir(self.targetpath):
            sources = cppcollector.get_files(self.targetpath, cppcollector.cpp_exts)
            sources = filter(lambda f: not path.relpath(f, self.targetpath) in self.exclude, sources) # filter excluded
            return list(filter(self.is_file_new, sources))
        else:
            return [self.targetpath]
    def compile_stdafx(self, options):
        src_file = path.join(self.targetdir, 'stdafx.h')
        if not path.exists(src_file): return
        if not self.is_file_new(src_file): return

        print("compilation::stdafx")
        start_time = time.time()
        targeto = self.get_target_o_path(src_file)
        subprocess.check_call(['g++'] + options + ['-c', src_file, '-o', targeto])
        print("compilation::stdafx::finish in {:.2f}s with output size = {:.2f} Mb".format(time.time() - start_time, path.getsize(targeto) / 1024.0 / 1024.0))

    def compile(self, options):
        self.init_build_dir()

        if self.args.stdafx:
            self.compile_stdafx(options)

        newsources = self.get_target_files()

        print("compilation::start{}".format('' if len(options) < 1 else ' with options={}'.format(options)))
        start_time = time.time()

        for f in newsources:
            targeto = self.get_target_o_path(f)
            print("\t{} -> {}".format(self.get_reltoroot_path(f), self.get_reltoroot_path(targeto)))
            subprocess.check_call(['g++'] + options + ['-c', f, '-o', targeto])

        print("compilation::finish in {:.2f}s with {} files".format(time.time() - start_time, len(newsources)))
    def linkall(self, options = None):
        self.init_build_dir()

        def linker_sort(val):
            if path.basename(val).startswith("main"): return 0
            else: return 1
        
        outputs = cppcollector.get_files(self.builddir, cppcollector.o_exts)
        outputs = filter(lambda f: not path.relpath(f, self.builddir) in self.exclude, outputs) # filter excluded
        outputs = sorted(outputs, key=linker_sort)
        outputs = list(outputs)
        output_exe_path = self.get_output_exe_path()

        command = ['g++'] + options + ['-o', output_exe_path] + outputs
        print("linking::start with \"{}\"".format(' '.join(map(lambda f: self.get_reltoroot_path(f) if path.isabs(f) else f, command))))
        start_time = time.time()
        
        subprocess.check_call(command)

        print("linking::end in {:.2f}s with output in {}".format(time.time() - start_time, output_exe_path))
    def runexe(self):
        subprocess.call(self.get_output_exe_path())

def parse_args():
    parser = argparse.ArgumentParser(prefix_chars='+')

    parser.add_argument('targetpath')
    parser.add_argument('++out', help='output file', nargs='?', const=None)

    parser.add_argument('++compile', dest='compile', action='store_true')
    parser.add_argument('++no-compile', dest='compile', action='store_false')
    parser.set_defaults(compile=True)
    parser.add_argument('++link', dest='link', action='store_true')
    parser.add_argument('++no-link', dest='link', action='store_false')
    parser.set_defaults(link=True)
    parser.add_argument('++stdafx', dest='stdafx', action='store_true')
    parser.add_argument('++no-stdafx', dest='stdafx', action='store_false')
    parser.set_defaults(stdafx=True)

    parser.add_argument('++clean', dest='clean', action='store_true')
    parser.set_defaults(clean=False)

    parser.add_argument('++autorun', dest='autorun', action='store_true')
    parser.set_defaults(autorun=False)

 
    parser.add_argument('++copts', help='compiler options', nargs='+')
    parser.set_defaults(copts=[])
    parser.add_argument('++lopts', help='linker options', nargs='+')
    parser.set_defaults(lopts=[])
    parser.add_argument('++exclude', help='ignore these file names relative to root of search dir (/src or /build)', nargs='+')
    parser.set_defaults(exclude=[])

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    mxx = mxxbuilder(args)

    if args.clean:
        import shutil
        try: shutil.rmtree(mxx.builddir)
        except: pass

    if args.compile:
        mxx.compile(args.copts)
    
    if args.link:
        mxx.linkall(args.lopts)

    if args.autorun:
        print('Running {}\n'.format(mxx.get_output_exe_path()))
        mxx.runexe()
    else:
        print("mxxbuild::end\n")

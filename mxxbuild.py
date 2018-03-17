
import os
path = os.path

import subprocess
import time
import argparse

import cppcollector

class mxxbuilder(object):
    def __init__(self, args):
        self.out = args.out

        self.exclude = list( map(lambda f: path.normpath(f), args.exclude) )

        self.sourcedir = path.abspath(path.normpath(args.targetdir))
        if not path.exists(self.sourcedir): raise Exception("targetdir \"{}\" does not exist!".format(self.sourcedir))
  
        self.rootdir = path.normpath(path.join(self.sourcedir, '..')) # one up
        self.builddir = path.join(self.rootdir, 'build')
        if not path.exists(self.builddir): os.makedirs(self.builddir)

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
    def compile_new(self, options):
        sources = cppcollector.get_files(self.sourcedir, cppcollector.cpp_exts)
        sources = filter(lambda f: not path.relpath(f, self.sourcedir) in self.exclude, sources) # filter excluded
        newsources = list(filter(self.is_file_new, sources))

        print("compilation::start{}".format('' if len(options) < 1 else ' with options={}'.format(options)))
        start_time = time.time()

        for f in newsources:
            targeto = self.get_target_o_path(f)
            print("\t{} -> {}".format(self.get_reltoroot_path(f), self.get_reltoroot_path(targeto)))
            subprocess.check_call(['g++'] + options + ['-c', f, '-o', targeto])

        print("compilation::finish in {:.2f}s with {} files".format(time.time() - start_time, len(newsources)))
    def linkall(self, options = None):
        outputs = cppcollector.get_files(self.builddir, cppcollector.o_exts)
        outputs = filter(lambda f: not path.relpath(f, self.builddir) in self.exclude, outputs) # filter excluded
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

    parser.add_argument('targetdir')
    parser.add_argument('++out', help='output file', nargs='?', const=None)

    parser.add_argument('++compile', dest='compile', action='store_true')
    parser.add_argument('++no-compile', dest='compile', action='store_false')
    parser.set_defaults(compile=True)
    parser.add_argument('++link', dest='link', action='store_true')
    parser.add_argument('++no-link', dest='link', action='store_false')
    parser.set_defaults(link=True)

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
        mxx.compile_new(args.copts)
    
    if args.link:
        mxx.linkall(args.lopts)

    if args.autorun:
        print('Running {}\n'.format(mxx.get_output_exe_path()))
        mxx.runexe()
    else:
        print("mxxbuild::end\n")

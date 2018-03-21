
import sys
import os
path = os.path

import subprocess
import time
import argparse

import cppcollector

class Log(object):
    def __init__(self, level):
        self.level = level
    def writeln(self, text, level = 1):
        if self.level >= level:
            print(text)
    def error(self, text):
        if self.level >= 0:
            print(text, file=sys.stderr)
    def throw(self, mess):
        if self.level >= 0:
            raise Exception(mess)
        else:
            os._exit(2)
            
class mxxbuilder(object):
    def __init__(self, args):
        self.args = args
        self.log = Log(args.verbose)

        self.args.exclude = list( map(lambda f: path.normpath(f), args.exclude) )

        self.targetpath = path.abspath(path.normpath(args.targetpath))
        if not path.exists(self.targetpath): self.log.throw("targetpath \"{}\" does not exist!".format(self.targetpath))
        if path.isdir(self.targetpath):
            self.targetdir = self.targetpath
        else:
            self.targetdir = path.dirname(self.targetpath)

        self.rootdir = path.normpath(path.join(self.targetdir, '..')) # one up

        if not path.isabs(self.args.build):
            self.args.build = path.join(self.rootdir, self.args.build)
        self.builddir = self.args.build
        if self.builddir[-1] != path.sep: self.builddir += path.sep # builddir always ends with /

        if self.args.out is None:
            self.args.out = path.join(self.builddir, 'a.exe')
        elif not path.isabs(self.args.out):
            self.args.out = path.join(self.rootdir, self.args.out)

        if self.args.clean:
            self.clean_build_dir()
    def clean_build_dir(self):
        import shutil
        try: shutil.rmtree(self.builddir)
        except: pass
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
    def __unpack_dirs(self, sources: list, allowed_exts: list):
        for o in sources:
            if path.isdir(o):
                content = cppcollector.get_files(o, allowed_exts)
                content = filter(lambda f: not path.relpath(f, o) in self.args.exclude, content) # filter excluded
                for f in content: yield f
            else:
                yield o
    def compile_stdafx(self):
        src_file = path.join(self.targetdir, 'stdafx.h')
        if not path.exists(src_file): return
        if not self.is_file_new(src_file): return

        self.log.writeln("compilation::stdafx")
        start_time = time.time()
        targeto = self.get_target_o_path(src_file)
        subprocess.check_call(['g++'] + self.args.copts + ['-c', src_file, '-o', targeto])
        self.log.writeln("compilation::stdafx::finish in {:.2f}s with output size = {:.2f} Mb".format(time.time() - start_time, path.getsize(targeto) / 1024.0 / 1024.0))

    def __compile_async(self, newsources):
        from threading import Thread
        import multiprocessing 
   
        ns_len = len(newsources)
        self.curr_running = 0
        self.error_during_compile = False

        def compile_one(f):
            targeto = self.get_target_o_path(f)
            try: 
                subprocess.check_call(['g++'] + self.args.copts + ['-c', f, '-o', targeto])
                self.log.writeln("\t{} -> {}".format(self.get_reltoroot_path(f), self.get_reltoroot_path(targeto)))
                self.curr_running -= 1
            except:
                self.error_during_compile = True
                self.curr_running = -1
  
        def run_thread(f):
            if self.error_during_compile:
                if __name__ == '__main__':
                    self.log.error("compilation::failed")
                    os._exit(1)
                else:
                    self.log.throw("compilation::failed")

            thread = Thread(target = compile_one, args = (f, ))
            thread.start()
            self.curr_running += 1

        if self.args.max_threads < 1:
            max_threads = multiprocessing.cpu_count()
        else:
            max_threads = self.args.max_threads
        self.log.writeln('compilation::using {} cores'.format(max_threads))

        for f in newsources:
            while self.curr_running >= max_threads:
                time.sleep(0.01)
            run_thread(f)
        while self.curr_running > 0:
            time.sleep(0.01)
    def compile_some(self, sources: list):
        outputs = list(self.__unpack_dirs(sources, cppcollector.cpp_exts))
        self.__compile_async(outputs)
    def compile_new(self, sources: list):
        start_time = time.time()

        outputs = self.__unpack_dirs(sources, cppcollector.cpp_exts)
        outputs = filter(lambda f: self.is_file_new(f), outputs)
        outputs = list(outputs)

        self.log.writeln("compilation::collected {} files in {:.2f}s".format(len(outputs), time.time() - start_time))
        
        self.__compile_async(outputs)
    def compile(self):
        self.init_build_dir()

        if self.args.stdafx:
            self.compile_stdafx()

        self.log.writeln("compilation::start{}".format('' if len(self.args.copts) < 1 else ' with options:\n\t{}'.format('\n\t'.join(self.args.copts))))
        start_time = time.time()

        self.compile_new([self.targetdir])
        self.log.writeln("compilation::finish in {:.2f}s".format(time.time() - start_time))
    def link_chosen(self, outputs: list):
        def linker_sort(val):
            if path.basename(val).startswith("main"): return 0
            else: return 1
 
        outputs = sorted(outputs, key=linker_sort)
        outputs = list(outputs)

        output_exe_path = self.args.out

        command = ['g++'] + self.args.lopts + ['-o', output_exe_path] + outputs
        self.log.writeln("linking::start with \"{}\"".format(' '.join(map(lambda f: self.get_reltoroot_path(f) if path.isabs(f) else f, command))))
        start_time = time.time()
        
        subprocess.check_call(command)

        self.log.writeln("linking::end in {:.2f}s with output in {}".format(time.time() - start_time, output_exe_path))
    def link_some(self, sources: list):
        outputs = list(self.__unpack_dirs(sources, cppcollector.o_exts))
        self.link_chosen(outputs)
    def linkall(self):
        self.init_build_dir()
        self.link_some([self.builddir])
    def runexe(self):
        self.log.writeln('mxx::running {}\n'.format(self.args.out))
        subprocess.call(self.args.out)

def parse_args(argv: list):
    parser = argparse.ArgumentParser(prefix_chars='+')
    parser.epilog = '''You need to use "++" instead of "--" because argparse treats '-' as its own option, therefore it's problematic to pass <copts>, <lopts> to g++'''

    parser.add_argument('targetpath', help='directory with all source files')
    parser.add_argument('++build', nargs='?', help='build directory. contains all the .o files')
    parser.set_defaults(build='build')
    parser.add_argument('++out', nargs='?', const=None, help='output .exe path. can be relative to ++build directory or absolute')

    parser.add_argument('++compile', dest='compile', action='store_true', help='do compilation')
    parser.add_argument('++no-compile', dest='compile', action='store_false', help='dont compile .cpp\'s')
    parser.set_defaults(compile=True)
    parser.add_argument('++link', dest='link', action='store_true', help='link .o files')
    parser.add_argument('++no-link', dest='link', action='store_false', help='dont link .o files')
    parser.set_defaults(link=True)
    parser.add_argument('++stdafx', dest='stdafx', action='store_true', help='compile stdafx.h')
    parser.add_argument('++no-stdafx', dest='stdafx', action='store_false', help='do not compile stdafx.h')
    parser.set_defaults(stdafx=True)


    parser.add_argument('++clean', dest='clean', action='store_true', help='remove ++build directory')
    parser.set_defaults(clean=False)

    parser.add_argument('++autorun', dest='autorun', action='store_true', help='run .exe after linking, or just run if exists')
    parser.set_defaults(autorun=False)

    parser.add_argument('++max-threads', dest='max_threads', nargs='?', type=int, help="maximum available threads during compilation")
    parser.set_defaults(max_threads=-1)
    parser.add_argument('++verbose', dest='verbose', nargs='?', type=int, help='verbosity level. Default is 1, if less than 0, erros will also be ignored')
    parser.set_defaults(verbose=1)
 
    parser.add_argument('++copts', nargs='+', help='compiler options')
    parser.set_defaults(copts=[])
    parser.add_argument('++lopts', nargs='+', help='linker options')
    parser.set_defaults(lopts=[])
    parser.add_argument('++exclude', nargs='+', help='ignore these file names relative to root of search dir (/src or /build)')
    parser.set_defaults(exclude=[])

    return parser.parse_args(argv)

def main(argv):
    args = parse_args(argv)
    mxx = mxxbuilder(args)

    if args.compile:
        mxx.compile()
    
    if args.link:
        mxx.linkall()

    if args.autorun:
        mxx.runexe()
    else:
        mxx.log.writeln("mxxbuild::end\n")

if __name__ == '__main__':
    main(sys.argv[1:])
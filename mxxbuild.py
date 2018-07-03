
import sys
import os
path = os.path

import subprocess
import time
import argparse

import cppcollector
import buildmethods as bm

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
    
    def compile_stdafx(self):
        self.log.writeln("compilation::stdafx")
        start_time = time.time()
        
        all_precompiled = bm.find_stdafxes(self.targetdir)
        new_precompiled = filter(lambda f: bm.is_file_new(self.rootdir, self.targetdir, f), all_precompiled) 
        bm.compile_some(new_precompiled, self.rootdir, self.builddir, self.args.copts, self.args.max_threads, self.log)
        self.log.writeln("compilation::stdafx::finish in {:.2f}s ".format(time.time() - start_time))

    def compile(self):
        if self.args.stdafx:
            self.compile_stdafx()

        self.log.writeln("compilation::start{}".format('' if len(self.args.copts) < 1 else ' with options:\n\t{}'.format('\n\t'.join(self.args.copts))))
        start_time = time.time()
        self.init_build_dir()

        new = list(bm.get_new_cpps(self.targetdir, self.rootdir, self.builddir, self.args.exclude))
        self.log.writeln("compilation::collected {} files in {:.2f}s".format(len(new), time.time() - start_time))

        bm.compile_async(new, self.rootdir, self.builddir, self.args.copts, self.args.max_threads, self.log)
        
        self.log.writeln("compilation::finish in {:.2f}s".format(time.time() - start_time))
    def link(self):
        bm.linkall(self.builddir, self.args.out, self.args.lopts, self.log, self.args.exclude)
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
    parser.add_argument('++cname', dest='cname', nargs='?', type=str, help='compiler name. Default is "g++"')
    parser.set_defaults(cname='g++')
 
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
    bm.compiler_name = args.cname

    if args.compile:
        mxx.compile()
    
    if args.link:
        mxx.link()

    if args.autorun:
        mxx.runexe()
    else:
        mxx.log.writeln("mxxbuild::end\n")

if __name__ == '__main__':
    main(sys.argv[1:])
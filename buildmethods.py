import os
path = os.path
import subprocess
import time

import cppcollector

def get_reltoroot_path(rootdir, src_file):
    return path.relpath(src_file, rootdir)
def get_target_o_path(rootdir, builddir, src_file):
    curr_ext    = src_file.split(path.extsep)[-1]
    if curr_ext == 'h':
        return src_file + '.gch'
    else:
        relpath     = path.relpath(src_file, rootdir)
        targetpath  = path.join(builddir, relpath)
    
        new_ext     = 'o'
        targetpath  = (targetpath[:-len(curr_ext)]) + new_ext
        
        targetdir = path.dirname(targetpath)
        if not path.exists(targetdir): os.makedirs(targetdir)
        
        return targetpath
def is_file_new(rootdir, builddir, src_file):
    '''
    if .cpp file needs to be recompiled -> True \n
    else                                -> False
    '''

    targeto = get_target_o_path(rootdir, builddir, src_file)

    if not path.exists(targeto): return True
    
    # Check if .cpp file was modified after .o file
    if path.getmtime(src_file) > path.getmtime(targeto): return True
    
    return False
def __unpack_dirs_ruled(sources: list, rule):
    for o in sources:
        if path.isdir(o):
            content = cppcollector.get_filtered(o, rule)
            for f in content: yield f
        else:
            yield o
def __unpack_dirs(sources: list, exclude: list, allowed_exts: list):
    def rule(f): return cppcollector.extension_rule(f, allowed_exts) and (not f in exclude)
    return __unpack_dirs_ruled(sources, rule)
def find_stdafxes(dirpath):
    return cppcollector.get_endswith(dirpath, ['stdafx.h'])
class AsyncCompiler(object):
    from threading import Thread
    def __init__(self, newsources: list, rootdir: str, builddir: str, copts: list, max_threads: int, log):
        self.curr_running = 0
        self.sources = newsources
        self.error_during_compile = False
        self.rootdir = rootdir
        self.builddir = builddir
        self.copts = copts
        self.log = log

        import multiprocessing

        if max_threads < 1:
            self.max_threads = multiprocessing.cpu_count()
        else:
            self.max_threads = max_threads
        self.log.writeln('compilation::using {} cores'.format(self.max_threads))

        for f in newsources:
            while self.curr_running >= self.max_threads:
                time.sleep(0.01)
            self.run_thread(f)
        while self.curr_running > 0:
            time.sleep(0.01)
    def compile_one(self, f):
        targeto = get_target_o_path(self.rootdir, self.builddir, f)
        try: 
            subprocess.check_call(['g++'] + self.copts + ['-c', f, '-o', targeto])
            self.log.writeln("\t{} -> {}".format(get_reltoroot_path(self.rootdir, f), get_reltoroot_path(self.rootdir, targeto)))
            self.curr_running -= 1
        except:
            raise
            self.error_during_compile = True
            self.curr_running = -1

    def run_thread(self, f):
        if self.error_during_compile:
            if __name__ == '__main__':
                self.log.error("compilation::failed")
                os._exit(1)
            else:
                self.log.throw("compilation::failed")

        thread = AsyncCompiler.Thread(target = self.compile_one, args = (f, ))
        thread.start()
        self.curr_running += 1
def compile_async(newsources: list, rootdir: str, builddir: str, copts: list, max_threads: int, log):
    AsyncCompiler(newsources, rootdir, builddir, copts, max_threads, log)
def compile_some(sources: list, rootdir: str, builddir: str, copts: list, max_threads: int, log):
    outputs = __unpack_dirs(sources, exclude=[], allowed_exts=cppcollector.cpp_exts)
    compile_async(outputs, rootdir, builddir, copts, max_threads, log)
def get_new_cpps(dirpath, rootdir, builddir, exclude=[]):
    outputs = __unpack_dirs([dirpath], exclude, cppcollector.cpp_exts)
    outputs = filter(lambda f: is_file_new(rootdir, builddir, f), outputs)
    return outputs

def get_link_chosen_command(outputs: list, output_exe_path: str):
    def linker_sort(val):
        if path.basename(val).startswith("main"): return 0
        else: return 1

    outputs = sorted(outputs, key=linker_sort)
    outputs = list(outputs)

    return ['g++', '-o', output_exe_path] + outputs
    # self.log.writeln("linking::start with \"{}\"".format(' '.join(map(lambda f: get_reltoroot_path(f) if path.isabs(f) else f, command))))
    # start_time = time.time()
    
    # subprocess.check_call(command)

    # self.log.writeln("linking::end in {:.2f}s with output in {}".format(time.time() - start_time, output_exe_path))
def get_link_some_command(sources: list, output_exe_path: str, exclude = []):
    outputs = __unpack_dirs(sources, exclude, cppcollector.o_exts)
    return get_link_chosen_command(outputs, output_exe_path)
def linkall(dirpath: str, output_exe_path: str, lopts: list, log, exclude = []):
    command = get_link_some_command([dirpath], output_exe_path, exclude=exclude)
    command = command + lopts

    start_time = time.time()
    log.writeln("linking::start with \"{}\"".format(' '.join(map(lambda f: get_reltoroot_path(dirpath, f) if path.isabs(f) else f, command))))
    subprocess.check_call(command)
    log.writeln("linking::end in {:.2f}s with output in {}".format(time.time() - start_time, output_exe_path))
    
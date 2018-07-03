import os
path = os.path
import subprocess
import time

import cppcollector

compiler_name = 'g++'

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
            for f in __unpack_dirs_ruled(content, rule):
                yield f
        else:
            if rule(o): yield o
def __unpack_dirs(sources: list, exclude: list, allowed_exts: list):
    if exclude is None: exclude = []
    def rule(f): return cppcollector.extension_rule(f, allowed_exts) and (not f in exclude)
    return __unpack_dirs_ruled(sources, rule)
def find_stdafxes(dirpath):
    return cppcollector.get_endswith(dirpath, ['stdafx.h'])
class AsyncCompiler(object):
    from threading import Thread
    def __init__(self, newsources: list, rootdir: str, builddir: str, copts: list, max_threads: int, log):
        self.curr_running = 0
        self.sources = newsources
        self.compilation_ok = True
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

    def compile_one(self, f, targeto):
        if not self.compilation_ok:
            return
        try:
            subprocess.check_call([compiler_name] + self.copts + ['-c', f, '-o', targeto])
            self.log.writeln("\t{} -> {}".format(path.relpath(f, self.rootdir), path.relpath(targeto, self.rootdir)))
            self.curr_running -= 1
        except:
            self.compilation_ok = False
            self.curr_running = -1
            self.log.error("compilation::failed")

    def run_thread(self, f):
        targeto = get_target_o_path(self.rootdir, self.builddir, f)
        thread = AsyncCompiler.Thread(target = self.compile_one, args = (f, targeto, ))
        self.curr_running += 1
        thread.start()
def compile_async(newsources: list, rootdir: str, builddir: str, copts: list, max_threads: int, log) -> bool:
    ac = AsyncCompiler(newsources, rootdir, builddir, copts, max_threads, log)
    return ac.compilation_ok
def compile_some(sources: list, rootdir: str, builddir: str, allowed_exts: list, exclude: list, copts: list, max_threads: int, log) -> bool:
    outputs = __unpack_dirs(sources, exclude=exclude, allowed_exts=allowed_exts)
    return compile_async(outputs, rootdir, builddir, copts, max_threads, log)
def get_new_sources(sources: list, rootdir, builddir, exclude, allowed_exts):
    outputs = __unpack_dirs(sources, exclude=exclude, allowed_exts=allowed_exts)
    outputs = filter(lambda f: is_file_new(rootdir, builddir, f), outputs)
    return outputs

def get_link_chosen_command(outputs: list, output_exe_path: str):
    return [compiler_name, '-o', output_exe_path] + list(outputs)
def get_link_some_command(sources: list, output_exe_path: str, exclude = []):
    outputs = __unpack_dirs(sources, exclude, cppcollector.o_exts)
    return get_link_chosen_command(outputs, output_exe_path)
def linkall(dirpath: str, output_exe_path: str, lopts: list, log, exclude = []) -> bool:
    command = get_link_some_command([dirpath], output_exe_path, exclude=exclude)
    command = command + lopts

    start_time = time.time()
    log.writeln("linking::start with \"{}\"".format(' '.join(map(lambda f: path.relpath(f, dirpath) if path.isabs(f) else f, command))))
    try: 
        subprocess.check_call(command)
        log.writeln("linking::end in {:.2f}s with output in {}".format(time.time() - start_time, output_exe_path))
        return True
    except: 
        log.error("linking::error")
        return False
    

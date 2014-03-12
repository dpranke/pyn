import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time


class Host(object):
    stderr = sys.stderr
    stdout = sys.stdout
    python_interpreter = sys.executable

    def abspath(self, *comps):
        return os.path.abspath(self.join(*comps))

    def call(self, cmd_str):
        proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr

    def chdir(self, *comps):
        return os.chdir(self.join(*comps))

    def cpu_count(self):
        return multiprocessing.cpu_count()

    def dirname(self, *comps):
        return os.path.dirname(self.join(*comps))

    def exists(self, *comps):
        return os.path.exists(self.join(*comps))

    def files_under(self, top):
        all_files = []
        for root, dirs, files in os.walk(top):
            for f in files:
                relpath = self.relpath(os.path.join(root, f), top)
                all_files.append(relpath)
        return all_files

    def getcwd(self):
        return os.getcwd()

    def getenv(self, key, default=None):
        return os.getenv(key, default=default)

    def join(self, *comps):
        return os.path.join(*comps)

    def maybe_mkdir(self, *comps):
        path = self.abspath(self.join(*comps))
        if not self.exists(path):
            os.mkdir(path)

    def mkdtemp(self, **kwargs):
        return tempfile.mkdtemp(**kwargs)

    def mtime(self, *comps):
        return os.stat(self.join(*comps)).st_mtime

    def mp_pool(self, processes=None):
        return multiprocessing.Pool(processes)

    def print_err(self, msg, end='\n'):
        self.stderr.write(str(msg) + end)

    def print_out(self, msg, end='\n'):
        self.stdout.write(str(msg) + end)
        self.stdout.flush()

    def read(self, *comps):
        path = self.join(*comps)
        with open(path) as f:
            return f.read()

    def relpath(self, path, start):
        return os.path.relpath(path, start)

    def remove(self, *comps):
        os.remove(self.join(*comps))

    def rmtree(self, path):
        shutil.rmtree(path, ignore_errors=True)

    def sleep(self, time_secs):
        return time.sleep(time_secs)

    def time(self):
        return time.time()

    def write(self, path, contents):
        with open(path, 'w') as f:
            f.write(contents)

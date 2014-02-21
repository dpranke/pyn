import multiprocessing
import os
import subprocess
import sys


class Host(object):
    # pylint: disable=R0201
    stderr = sys.stderr
    stdout = sys.stdout
    python_interpreter = sys.executable

    def call(self, cmd_str):
        proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr

    def chdir(self, *comps):
        return os.chdir(self.join(*comps))

    def cpu_count(self):
        return multiprocessing.cpu_count()

    def dirname(self, path):
        return os.path.dirname(path)

    def exists(self, *comps):
        return os.path.exists(self.join(*comps))

    def join(self, *comps):
        return os.path.join(*comps)

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not self.exists(path):
            os.mkdir(path)

    def mtime(self, *comps):
        return os.stat(self.join(*comps)).st_mtime

    def path_to_module(self, module_name):
        # __file__ is always an absolute path.
        return sys.modules[module_name].__file__

    def print_err(self, *args, **kwargs):
        assert 'file' not in kwargs
        if len(args) > 1:
            self.stderr.write((args[0] % args[1:]) + '\n')
        else:
            self.stderr.write(args[0] + '\n')

    def print_out(self, *args, **kwargs):
        assert 'file' not in kwargs
        if len(args) > 1:
            self.stdout.write((args[0] % args[1:]) + '\n')
        else:
            self.stdout.write(args[0] + '\n')

    def read(self, *comps):
        path = self.join(*comps)
        with open(path) as f:
            return f.read()

    def remove(self, *comps):
        os.remove(self.join(*comps))

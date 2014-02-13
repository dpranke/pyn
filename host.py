#!/usr/bin/env python

from __future__ import print_function

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

    def exit(self, code):
        sys.exit(code)

    def join(self, *comps):
        return os.path.join(*comps)

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not self.exists(path):
            os.mkdir(path)

    def path_to_module(self, module_name):
        # __file__ is always an absolute path.
        return sys.modules[module_name].__file__

    def print_err(self, *args, **kwargs):
        assert 'file' not in kwargs
        print(*args, file=self.stderr, **kwargs)

    def print_out(self, *args, **kwargs):
        assert 'file' not in kwargs
        print(*args, **kwargs)

    def read(self, *comps):
        path = self.join(*comps)
        with open(path) as f:
            return f.read()

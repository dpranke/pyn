#!/usr/bin/env python

from __future__ import print_function

import multiprocessing
import os
import sys


class Host(object):
    stderr = sys.stderr
    stdout = sys.stdout
    python_interpreter = sys.executable

    def call(self, cmd):
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return proc.returncode, stdout, stderr

    def cpu_count(self):
        return multiprocessing.cpu_count()

    def exists(self, *comps):
        return os.path.exists(self.join(*comps))

    def chdir(self, *comps):
        return os.chdir(self.join(*comps))

    def join(self, *comps):
        return os.path.join(*comps)

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not self.exists(path):
            os.mkdir(path)

    def read(self, *comps):
        path = self.join(*comps)
        with open(path) as f:
            return f.read()

    def print_err(self, *args, **kwargs):
        assert 'file' not in kwargs
        print(*args, file=self.stderr, **kwargs)

    def print_out(self, *args, **kwargs):
        assert 'file' not in kwargs
        print(*args, **kwargs)

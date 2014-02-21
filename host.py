import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile


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

    def dirname(self, *comps):
        return os.path.dirname(self.join(*comps))

    def exists(self, *comps):
        return os.path.exists(self.join(*comps))

    def getcwd(self):
        return os.getcwd()

    def join(self, *comps):
        return os.path.join(*comps)

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not self.exists(path):
            os.mkdir(path)

    def mkdtemp(self, **kwargs):
        """Create and return a uniquely named directory.

        This is like tempfile.mkdtemp, but if used in a with statement
        the directory will self-delete at the end of the block (if the
        directory is empty; non-empty directories raise errors). The
        directory can be safely deleted inside the block as well, if so
        desired.

        Note that the object returned is not a string and does not
        support all of the string methods. If you need a string, coerce the
        object to a string and go from there.
        """
        class TemporaryDirectory(object):
            def __init__(self, **kwargs):
                self._kwargs = kwargs
                self._directory_path = tempfile.mkdtemp(**self._kwargs)

            def __str__(self):
                return self._directory_path

            def __enter__(self):
                return self._directory_path

            def __exit__(self, type, value, traceback):
                # Only self-delete if necessary.

                # FIXME: Should we delete non-empty directories?
                if os.path.exists(self._directory_path):
                    os.rmdir(self._directory_path)

        return TemporaryDirectory(**kwargs)

    def mtime(self, *comps):
        return os.stat(self.join(*comps)).st_mtime

    def path_to_module(self, module_name):
        # _file__ is always an absolute path.
        return sys.modules[module_name].__file__

    def print_err(self, msg):
        self.stderr.write(msg + '\n')

    def print_out(self, msg):
        self.stdout.write(msg + '\n')

    def read(self, *comps):
        path = self.join(*comps)
        with open(path) as f:
            return f.read()

    def remove(self, *comps):
        os.remove(self.join(*comps))

    def rmtree(self, path):
        shutil.rmtree(path, ignore_errors=True)

    def write(self, path, contents):
        with open(path, 'w') as f:
            f.write(contents)

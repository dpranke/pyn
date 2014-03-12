# FIXME: make this work w/ python3.
import multiprocessing

from StringIO import StringIO


class FakeHost(object):
    # "too many instance attributes" pylint: disable=R0902
    # "redefining built-in" pylint: disable=W0622

    python_interpreter = 'python'

    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.sep = '/'
        self.dirs = set([])
        self.files = {}
        self.written_files = {}
        self.last_tmpdir = None
        self.current_tmpno = 0
        self.mtimes = {}
        self.cmds = []
        self.cwd = '/tmp'

    def abspath(self, *comps):
        relpath = self.join(*comps)
        if relpath.startswith('/'):
            return relpath
        return self.join(self.cwd, relpath)

    def call(self, cmd_str):
        self.cmds.append(cmd_str)
        args = cmd_str.split()
        if args[0] == 'echo' and args[-2] == '>':
            out = ' '.join(args[1:len(args) - 2]) + '\n'
            self.write(self.abspath(args[-1]), out)
            return 0, '', ''
        if args[0] == 'cat' and args[-2] == '>':
            out = ''
            for f in args[1:len(args) - 2]:
                out += self.read(f)
            self.write(self.abspath(args[-1]), out)
            return 0, '', ''
        return 1, '', ''

    def chdir(self, *comps):
        self.cwd = self.join(*comps)

    def cpu_count(self):
        return 2

    def dirname(self, path):
        return '/'.join(path.split('/')[:-1])

    def exists(self, *comps):
        path = self.join(self.cwd, *comps)
        return path in self.files

    def files_under(self, top):
        files = []
        for f in self.files:
            if self.files[f] is not None and f.startswith(top):
                files.append(self.relpath(f, top))
        return files

    def getcwd(self):
        return self.cwd

    def getenv(self, key, default=None):
        assert key
        return default

    def join(self, *comps):
        return '/'.join(comps).replace('//', '/')

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not path in self.dirs:
            self.dirs.add(path)

    def mkdtemp(self, suffix='', prefix='tmp', dir=None, **_kwargs):
        if dir is None:
            dir = self.sep + '__im_tmp'
        curno = self.current_tmpno
        self.current_tmpno += 1
        self.last_tmpdir = self.join(dir, '%s_%u_%s' % (prefix, curno, suffix))
        return self.last_tmpdir

    def mtime(self, *comps):
        return self.mtimes.get(self.join(*comps), 0)

    def print_err(self, msg, end='\n'):
        self.stderr.write(msg + end)

    def print_out(self, msg, end='\n'):
        self.stdout.write(msg + end)

    def read(self, *comps):
        return self.files[self.abspath(*comps)]

    def relpath(self, path, start):
        return path.replace(start + '/', '')

    def remove(self, *comps):
        path = self.abspath(*comps)
        self.files[path] = None
        self.written_files[path] = None

    def rmtree(self, *comps):
        path = self.abspath(*comps)
        for f in self.files:
            if f.startswith(path):
                self.files[f] = None
                self.written_files[f] = None

    def time(self):
        return 0

    def write(self, path, contents):
        full_path = self.abspath(path)
        self.files[full_path] = contents
        self.written_files[full_path] = contents

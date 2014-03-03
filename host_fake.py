try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class FakeHost(object):
    # "too many instance attributes" pylint: disable=R0902
    # "redefining built-in" pylint: disable=W0622

    python_interpreter = 'python'

    def __init__(self, dirs=None, files=None, mtimes=None, cwd='/tmp'):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.sep = '/'
        self.dirs = set(dirs or [])
        self.files = files or {}
        self.written_files = {}
        self.last_tmpdir = None
        self.current_tmpno = 0
        self.mtimes = mtimes or {}
        self.cmds = []
        self.cwd = cwd
        for f in self.files:
            d = self.dirname(f)
            while not d in self.dirs:
                self.dirs.add(d)
                d = self.dirname(d)

    def call(self, cmd_str):
        self.cmds.append(cmd_str)
        return 0, '', ''

    def chdir(self, *comps):
        self.cwd = self.join(*comps)

    def cpu_count(self):
        return 2

    def dirname(self, path):
        return path.split('/')[:-1].join('/')

    def exists(self, *comps):
        path = self.join(self.cwd, *comps)
        return path in self.files

    def getcwd(self):
        return self.cwd

    def getenv(self, key, default=None):
        assert key
        return default

    def join(self, *comps):
        return '/'.join(comps)

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

    def mp_pool(self, processes=None):
        return FakePool(processes)

    def mtime(self, *comps):
        return self.mtimes[self.join(*comps)]

    def path_to_module(self, module_name):
        return '/src/pyn/' + module_name

    def print_err(self, msg, end='\n'):
        self.stderr.write(msg + end)

    def print_out(self, msg, end='\n'):
        self.stdout.write(msg + end)

    def read(self, *comps):
        return self.files[self.join(self.cwd, *comps)]

    def remove(self, *comps):
        del self.files[self.join(*comps)]

    def rmtree(self, *comps):
        path = self.join(*comps)
        for f in self.files:
            if f.startswith(path):
                f.files[f] = None
                f.written_files[f] = None

    def sleep(self, time_secs):
        pass

    def time(self):
        return 0

    def write(self, path, contents):
        self.files[path] = contents
        self.written_files[path] = contents


class FakePool(object):
    def __init__(self, processes=None):
        self.processes = processes

    def close(self):
        pass

    def map(self, fn, iterable):
        return [fn(i) for i in iterable]

    def join(self):
        pass

    def terminate(self):
        pass

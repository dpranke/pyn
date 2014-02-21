from StringIO import StringIO


class FakeHost(object):
    # "method could be a function" pylint: disable=R0201

    python_interpreter = 'python'

    def __init__(self, dirs=None, files=None, mtimes=None, cwd='/tmp'):
        self.stdout = StringIO()
        self.stderr = StringIO()
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

    def join(self, *comps):
        return '/'.join(comps)

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not path in self.dirs:
            self.dirs.add(path)

    def _mktemp(self, suffix='', prefix='tmp', dir=None, **kwargs):
        if dir is None:
            dir = self.sep + '__im_tmp'
        curno = self.current_tmpno
        self.current_tmpno += 1
        self.last_tmpdir = self.join(dir, '%s_%u_%s' % (prefix, curno, suffix))
        return self.last_tmpdir

    def mkdtemp(self, **kwargs):
        class TemporaryDirectory(object):
            def __init__(self, fs, **kwargs):
                self._kwargs = kwargs
                self._filesystem = fs
                self._directory_path = fs._mktemp(**kwargs)
                fs.maybe_mkdir(self._directory_path)

            def __str__(self):
                return self._directory_path

            def __enter__(self):
                return self._directory_path

            def __exit__(self, type, value, traceback):
                # Only self-delete if necessary.

                # FIXME: Should we delete non-empty directories?
                if self._filesystem.exists(self._directory_path):
                    self._filesystem.rmtree(self._directory_path)

        return TemporaryDirectory(fs=self, **kwargs)

    def mtime(self, *comps):
        return self.mtimes[self.join(*comps)]

    def path_to_module(self, module_name):
        # __file__ is always an absolute path.
        return '/src/pyn/' + module_name

    def print_err(self, msg):
        self.stderr.write(msg + '\n')

    def print_out(self, msg):
        self.stdout.write(msg + '\n')

    def read(self, *comps):
        return self.files[self.join(self.cwd, *comps)]

    def remove(self, *comps):
        del self.files[self.join(*comps)]

    def rmtree(self, *comps)
        path = self.join(*comps)
        for f in self.files:
            if f.startswith(path):
                f[files] = None
                f.written_files.add(f)

    def write(self, _contents):
        self.files[path] = contents
        self.written_files.add(path)

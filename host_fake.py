from StringIO import StringIO


class FakeHost(object):
    # "method could be a function" pylint: disable=R0201

    python_interpreter = 'python'

    def __init__(self, files=None, mtimes=None):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.files = files or {}
        self.mtimes = mtimes or {}
        self.cmds = []
        self.cwd = '/tmp'

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

    def join(self, *comps):
        return '/'.join(comps)

    def maybe_mkdir(self, *comps):
        path = self.join(*comps)
        if not self.exists(path):
            self.files[path + '/'] = ''

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

    def write_tempfile_and_return_name(self, _contents):
        assert False

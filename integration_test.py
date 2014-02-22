import sys
import textwrap
import unittest

from host import Host
from main_test import TestMain
from ninja_parser_test import TestNinjaParser

SHOULD_RUN_COVERAGE = False


class IntegrationTestMain(TestMain):
    @staticmethod
    def call(argv):
        host = Host()
        path_to_main = host.join(host.dirname(host.path_to_module(__name__)),
                                 'main.py')
        if SHOULD_RUN_COVERAGE:
            cmd_prefix = ['coverage', 'run', '--append', path_to_main]
        else:
            cmd_prefix = [host.python_interpreter, path_to_main]

        return host.call(' '.join(cmd_prefix + argv))


class IntegrationTestNinjaParser(TestNinjaParser):
    @staticmethod
    def _call(text, files):
        host = Host()

        host_module_path = host.path_to_module(host.__module__)
        path_to_main = host.join(host.dirname(host_module_path), 'main.py')
        if SHOULD_RUN_COVERAGE:
            cmd_prefix = ['coverage', 'run', '--append', path_to_main]
        else:
            cmd_prefix = [host.python_interpreter, path_to_main]

        orig_wd = host.getcwd()
        try:
            tmpdir = str(host.mkdtemp())
            host.chdir(tmpdir)
            host.write('build.ninja', text)
            for path, contents in list(files.items()):
                dirname = host.dirname(path)
                if dirname:
                    host.maybe_mkdir(dirname)
                host.write(path, contents)

            cmd = cmd_prefix + ['-t', 'check']
            return host.call(' '.join(cmd))
        finally:
            host.rmtree(tmpdir)
            host.chdir(orig_wd)

    def check(self, text, _ast, dedent=True, files=None):
        files = files or {}
        if dedent:
            dedented_text = textwrap.dedent(text)
            returncode, _, _ = self._call(dedented_text, files)
        else:
            returncode, _, _ = self._call(text, files)

        # Note that we ignore what the AST is.
        self.assertEqual(returncode, 0)

    def err(self, text, dedent=True, files=None):
        files = files or {}
        if dedent:
            dedented_text = textwrap.dedent(text)
            returncode, _, _ = self._call(dedented_text, files)
        else:
            returncode, _, _ = self._call(text, files)

        self.assertNotEquals(returncode, 0)

if __name__ == '__main__':
    if '-c' in sys.argv:
        sys.argv.remove('-c')
        SHOULD_RUN_COVERAGE = True
    unittest.main()

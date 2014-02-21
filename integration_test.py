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
    def _call(text):
        host = Host()
        fname = host.write_tempfile_and_return_name(text)

        path_to_main = host.join(host.dirname(host.path_to_module(__name__)),
                                 'main.py')
        if SHOULD_RUN_COVERAGE:
            cmd_prefix = ['coverage', 'run', '--append', path_to_main]
        else:
            cmd_prefix = [host.python_interpreter, path_to_main]
        try:
            cmd = cmd_prefix + ['-f', fname, '-t', 'check']
            return host.call(' '.join(cmd))
        finally:
            host.remove(fname)

    def check(self, text, _ast, dedent=True):
        if dedent:
            dedented_text = textwrap.dedent(text)
            returncode, _, _ = self._call(dedented_text)
        else:
            returncode, _, _ = self._call(text)

        # Note that we ignore what the AST is.
        self.assertEqual(returncode, 0)

    def err(self, text, dedent=True):
        if dedent:
            dedented_text = textwrap.dedent(text)
            returncode, _, _ = self._call(dedented_text)
        else:
            returncode, _, _ = self._call(text)

        self.assertNotEquals(returncode, 0)

    # The tests below will fail w/o real files
    def test_default(self):
        pass

    def test_include(self):
        pass

    def test_spaces_in_paths(self):
        pass

    def test_subninja(self):
        pass

if __name__ == '__main__':
    if '-c' in sys.argv:
        sys.argv.remove('-c')
        SHOULD_RUN_COVERAGE = True
    unittest.main()

import os
import sys
import textwrap
import unittest

from host import Host
from main_test import TestMain
from parser_test import TestNinjaParser


class IntegrationTestMain(TestMain):
    @staticmethod
    def call(argv):
        host = Host()
        path_to_main = host.join(host.dirname(host.path_to_module(__name__)),
                                 'main.py')
        path_to_main = path_to_main.replace(' ', '\\ ')
        cmd_prefix = [host.python_interpreter, path_to_main]
        return host.call(' '.join(cmd_prefix + argv))


class IntegrationTestNinjaParser(TestNinjaParser):
    @staticmethod
    def _call(text, files):
        host = Host()

        host_module_path = host.path_to_module(host.__module__)
        path_to_main = host.join(host.dirname(host_module_path), 'main.py')
        path_to_main = path_to_main.replace(' ', '\\ ')
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

    def err(self, text, files=None):
        files = files or {}
        dedented_text = textwrap.dedent(text)
        returncode, _, _ = self._call(dedented_text, files)
        self.assertNotEquals(returncode, 0)


class PynEvalTest(unittest.TestCase):
    def cmd_prefix(self):
        # return ['ninja']
        host = Host()
        host_module_path = host.path_to_module(host.__module__)
        path_to_main = host.join(host.dirname(host_module_path), 'main.py')
        path_to_main = path_to_main.replace(' ', '\\ ')
        return [host.python_interpreter, path_to_main]

    def files_to_ignore(self):
        # return ['.ninja_deps', '.ninja_log']
        return ['.pyn.db']

    def _call(self, files):
        host = Host()
        cmd_prefix = self.cmd_prefix()

        try:
            orig_wd = host.getcwd()
            tmpdir = str(host.mkdtemp())
            host.chdir(tmpdir)
            for path, contents in list(files.items()):
                dirname = host.dirname(path)
                if dirname:
                    host.maybe_mkdir(dirname)
                host.write(path, contents)

            cmd = cmd_prefix
            returncode, out, err = host.call(' '.join(cmd))

            out_files = {}
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    path = host.relpath(host.join(root, f), tmpdir)
                    out_files[path] = host.read(path)
            return returncode, out_files
        finally:
            host.rmtree(tmpdir)
            host.chdir(orig_wd)

    def check(self, in_files, expected_out_files):
        returncode, actual_out_files = self._call(in_files)
        self.assertEqual(returncode, 0)
        for k, v in expected_out_files.items():
            self.assertEqual(expected_out_files[k], v)

        all_out_files = set(actual_out_files.keys()).difference(self.files_to_ignore())
        self.assertEqual(all_out_files, set(expected_out_files.keys()))

    def test_basic(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            rule echo_out
                command = echo $out > $out

            build foo : echo_out build.ninja

            default foo
            """)

        out_files = in_files.copy()
        out_files['foo'] = 'foo\n'
        self.check(in_files, out_files)

    def disabled_test_var_expansion(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            v = foo

            rule echo_out
                command = echo $out > $out

            build $v : echo_out build.ninja

            v = bar

            build $v : echo_out build.ninja
            """)

        out_files = in_files.copy()
        out_files['foo'] = 'foo\n'
        out_files['bar'] = 'bar\n'

        self.check(in_files, out_files)


if __name__ == '__main__':
    unittest.main()

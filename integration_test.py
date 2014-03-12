import os
import sys
import textwrap
import unittest

import main_test
import parser_test

from host import Host


class IntegrationTestArgs(main_test.TestArgs):
    @staticmethod
    def call(argv):
        host = Host()
        path_to_main = host.join(host.dirname(host.path_to_module(__name__)),
                                 'main.py')
        path_to_main = path_to_main.replace(' ', '\\ ')
        cmd_prefix = [host.python_interpreter, path_to_main]
        return host.call(' '.join(cmd_prefix + argv))


class IntegrationTestBuild(main_test.TestBuild):
    def _files_to_ignore(self):
        # return ['.ninja_deps', '.ninja_log']
        return ['.pyn.db']

    def _host(self):
        return Host()

    def _call(self, host, args):
        host_module_path = host.path_to_module(host.__module__)
        path_to_main = host.join(host.dirname(host_module_path), 'main.py')
        path_to_main = path_to_main.replace(' ', '\\ ')
        cmd_prefix = [host.python_interpreter, path_to_main]

        returncode, _, _ = host.call(' '.join(cmd_prefix + args))
        return returncode


class IntegrationTestNinjaParser(parser_test.TestNinjaParser):
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


if __name__ == '__main__':
    unittest.main()

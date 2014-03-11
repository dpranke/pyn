import re
import textwrap
import unittest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from host import Host
from host_fake import FakeHost
from main import main, VERSION


class TestArgs(unittest.TestCase):
    @staticmethod
    def call(argv):
        host = Host()
        host.stdout = StringIO()
        host.stderr = StringIO()
        actual_returncode = main(host, argv)
        out = host.stdout.getvalue()
        err = host.stderr.getvalue()
        return actual_returncode, out, err

    def check(self, argv, returncode, out_regex, err_regex):
        actual_returncode, out, err = self.call(argv)
        if returncode is not None:
            self.assertEqual(actual_returncode, returncode)
        self.assertTrue(re.match(out_regex, out, re.MULTILINE),
                        '%s does not match %s' % (out_regex, out))
        self.assertTrue(re.match(err_regex, err, re.MULTILINE),
                        '%s does not match %s' % (err_regex, err))

    def test_bad_arg(self):
        self.check(['--bad-arg'], 2, '', '')

    def test_bad_dir(self):
        self.check(['-C', 'missing_dir'], 2, '', '"missing_dir" not found\n')

    def test_bad_file(self):
        self.check(['-f', 'missing_build.ninja'], 2, '',
                   '"missing_build.ninja" not found\n')

    def test_bad_tool(self):
        self.check(['-t', 'foo'], 2, '', 'unsupported tool "foo"\n')

    def test_list(self):
        self.check(['-t', 'list'], 0, '.+', '')

    def test_chdir(self):
        self.check(['-n', '-C', '.'], 0, '', '.*')

    def test_check(self):
        self.check(['-t', 'check'], 0, '', '.*')

    def test_clean(self):
        self.check(['-n', '-t', 'clean'], 0, '', '.*')

    def test_question(self):
        # pass returncode=None here because the result may vary.
        self.check(['-t', 'question'], None, '', '.*')

    def test_debug(self):
        self.check(['-d', 'foo'], 2, '', '-d is not supported yet\n')

    def test_dry_run(self):
        self.check(['-n'], 0, '.+', '')

    def test_usage(self):
        self.check(['--help'], 0, 'usage:.+', '')
        self.check(['-h'], 0, 'usage:.+', '')

    def test_version(self):
        self.check(['--version'], 0, VERSION + '\n', '')


class TestBuild(unittest.TestCase):
    def files_to_ignore(self):
        # return ['.ninja_deps', '.ninja_log']
        return ['.pyn.db']

    def _write_files(self, host, files):
        for path, contents in list(files.items()):
            dirname = host.dirname(path)
            if dirname:
                host.maybe_mkdir(dirname)
            host.write(path, contents)

    def _read_files(self, host, tmpdir):
        out_files = {}
        for f in host.files:
            if f.startswith(tmpdir):
                out_files[f.replace(tmpdir + '/', '')] = host.files[f]
        return out_files

    def _call(self, files):
        host = FakeHost()

        def fake_call(arg_str):
            args = arg_str.split()
            if args[0] == 'echo' and args[2] == '>':
                host.write(host.join(host.cwd, args[3]), args[1] + '\n')
                return 0, '', ''
            return 1, '', ''

        host.call = fake_call

        try:
            orig_wd = host.getcwd()
            tmpdir = str(host.mkdtemp())
            host.chdir(tmpdir)
            self._write_files(host, files)

            returncode = main(host, [])

            out_files = self._read_files(host, tmpdir)
            return returncode, out_files
        finally:
            host.rmtree(tmpdir)
            host.chdir(orig_wd)

    def check(self, in_files, expected_out_files=None,
              expected_return_code=0):
        returncode, actual_out_files = self._call(in_files)

        self.assertEqual(returncode, expected_return_code)

        if expected_out_files:
            for k, v in expected_out_files.items():
                self.assertEqual(expected_out_files[k], v)
            all_out_files = set(actual_out_files.keys()).difference(
                self.files_to_ignore())
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

    def test_multiple_rules_fails(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            subninja echo.ninja
            subninja echo.ninja

            build foo : echo_out build.ninja

            default foo
            """)
        in_files['echo.ninja'] = textwrap.dedent("""
            rule echo_out
                command = echo $out > $out
            """)

        # FIXME: This should succeed.
        #out_files = in_files.copy()
        #out_files['foo'] = 'foo\n'
        #self.check(in_files, out_files)
        self.check(in_files, expected_return_code=1)

    def test_multiple_subninja_vars_fails(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            subninja echo.ninja
            subninja echo.ninja

            rule echo_out
                command = echo $out > $out

            build foo : echo_out build.ninja

            default foo
            """)
        in_files['echo.ninja'] = textwrap.dedent("""
            """)

        # FIXME: This should succeed.
        #out_files = in_files.copy()
        #out_files['foo'] = 'foo\n'
        #self.check(in_files, out_files)
        self.check(in_files, expected_return_code=1)

    def test_var_expansion(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            v = foo

            rule echo_out
                command = echo $out > $out

            build $v : echo_out build.ninja

            v = bar

            build $v : echo_out build.ninja
            """)

        # FIXME: This should succeed.
        #out_files = in_files.copy()
        #out_files['foo'] = 'foo\n'
        #out_files['bar'] = 'bar\n'
        #self.check(in_files, out_files)
        self.check(in_files, expected_return_code=1)

import re
import textwrap
import unittest

# FIXME: make this work w/ python3
from StringIO import StringIO

from host import Host
from host_fake import FakeHost
from main import main, VERSION


def default_test_files():
    in_files = {}
    in_files['build.ninja'] = textwrap.dedent("""
        rule cat
            command = cat $in > $out

        build ab : cat a b
        build cd : cat c d
        build abcd : cat ab cd

        default abcd
        """)
    in_files['a'] = 'hello '
    in_files['b'] = 'world\n'
    in_files['c'] = 'how are '
    in_files['d'] = 'you?\n'
    out_files = in_files.copy()
    out_files['ab'] = 'hello world\n'
    out_files['cd'] = 'how are you?\n'
    out_files['abcd'] = 'hello world\nhow are you?\n'

    return in_files, out_files


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


class UnitTestMixin(object):
    def _files_to_ignore(self):
        # return ['.ninja_deps', '.ninja_log']
        return ['.pyn.db']

    def _host(self):
        return FakeHost()

    def _call(self, host, args):
        host.stdout = StringIO()
        host.stderr = StringIO()
        returncode = main(host, args)
        out = host.stdout.getvalue()
        err = host.stderr.getvalue()
        return returncode, out, err

class CheckMixin(object):
    def _write_files(self, host, files):
        for path, contents in list(files.items()):
            dirname = host.dirname(path)
            if dirname:
                host.maybe_mkdir(dirname)
            host.write(path, contents)

    def _read_files(self, host, tmpdir):
        out_files = {}
        for f in host.files_under(tmpdir):
            out_files[f] = host.read(tmpdir, f)
        return out_files

    def assert_files(self, expected_files, actual_files):
        for k, v in expected_files.items():
            self.assertEqual(expected_files[k], v)
        interesting_files = set(actual_files.keys()).difference(
            self._files_to_ignore())
        self.assertEqual(interesting_files, set(expected_files.keys()))

    def check(self, in_files, expected_out_files=None,
              expected_return_code=0, expected_out=None, expected_err=None,
              args=None):
        host = self._host()
        args = args or []

        try:
            orig_wd = host.getcwd()
            tmpdir = host.mkdtemp()
            host.chdir(tmpdir)
            self._write_files(host, in_files)

            returncode, actual_out, actual_err = self._call(host, args)

            actual_out_files = self._read_files(host, tmpdir)
        finally:
            host.rmtree(tmpdir)
            host.chdir(orig_wd)

        self.assertEqual(returncode, expected_return_code)
        if expected_out is not None:
            self.assertEqual(expected_out, actual_out)
        if expected_err is not None:
            self.assertEqual(expected_err, actual_err)
        if expected_out_files:
            self.assert_files(expected_out_files, actual_out_files)


class TestBuild(unittest.TestCase, UnitTestMixin, CheckMixin):
    def test_basic(self):
        in_files, out_files = default_test_files()
        host = self._host()
        try:
            orig_wd = host.getcwd()
            tmpdir = host.mkdtemp()
            host.chdir(tmpdir)
            self._write_files(host, in_files)

            returncode, _, _ = self._call(host, ['-t', 'question'])
            self.assertEqual(returncode, 1)
            self.assert_files(in_files, self._read_files(host, tmpdir))

            returncode, _, _ = self._call(host, [])
            self.assertEqual(returncode, 0)
            self.assert_files(out_files, self._read_files(host, tmpdir))

            returncode, _, _ = self._call(host, ['-t', 'question'])
            # FIXME: make the fake host deal w/ mtimes properly.
            # self.assertEqual(returncode, 0)
            self.assertTrue(returncode in (0, 1))

            self.assert_files(out_files, self._read_files(host, tmpdir))

            returncode, _, _ = self._call(host, [])
            self.assertEqual(returncode, 0)
            self.assert_files(out_files, self._read_files(host, tmpdir))

            returncode, _, _ = self._call(host, ['-t', 'clean'])
            self.assertEqual(returncode, 0)

            self.assert_files(in_files, self._read_files(host, tmpdir))
        finally:
            host.rmtree(tmpdir)
            host.chdir(orig_wd)

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

            default foo bar
            """)

        out_files = in_files.copy()
        out_files['foo'] = 'foo\n'
        out_files['bar'] = 'bar\n'
        self.check(in_files, out_files)

    def test_var_expansion_across_includes(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            rule echo_out
                command = echo $out > $out

            v = foo
            include build_v.ninja

            v = bar
            include build_v.ninja

            default foo bar
            """)
        in_files['build_v.ninja'] = textwrap.dedent("""
            build $v : echo_out build.ninja
            """)

        out_files = in_files.copy()
        out_files['foo'] = 'foo\n'
        out_files['bar'] = 'bar\n'
        self.check(in_files, out_files)

    def test_subdirs(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            rule echo_out
                command = echo $out > $out

            build out/foo : echo_out build.ninja

            default out/foo
            """)
        out_files = in_files.copy()
        out_files['out/foo'] = 'out/foo\n'
        self.check(in_files, out_files)

    def test_command_line_changes(self):
        # FIXME: write :)
        pass

    def test_target_out_of_date(self):
        # FIXME: write :)
        pass

    def test_verbose(self):
        # FIXME: write :)
        pass

    def test_really_verboses(self):
        # FIXME: write :)
        pass

    def test_gcc_deps(self):
        # FIXME: write :)
        pass

    def test_ctrl_c(self):
        # FIXME: write :)
        pass

    def test_no_work_to_do(self):
        # FIXME: write :)
        pass

    def test_command_fails(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            rule falsify
                command = false

            build foo.o : falsify foo.c

            default foo.o
            """)
        in_files['foo.c'] = 'foo'
        self.check(in_files, expected_return_code=1)

    def test_input_file_in_subdir(self):
        in_files = {}
        in_files['build.ninja'] = textwrap.dedent("""
            rule cat
                command = cat $in > $out

            build out/foo : cat src/foo

            default out/foo
            """)
        in_files['src/foo'] = 'hello'

        out_files = in_files.copy()
        out_files['out/foo'] = 'hello\n'
        self.check(in_files, out_files)


class TestTools(unittest.TestCase, UnitTestMixin, CheckMixin):
    def test_commands(self):
        in_files, _ = default_test_files()
        self.check(in_files, args=['-t', 'commands'],
                   expected_out=('cat a b > ab\n'
                                 'cat c d > cd\n'
                                 'cat ab cd > abcd\n'))

    def test_deps(self):
        # FIXME: implement w/ real deps tests.
        in_files, _ = default_test_files()
        self.check(in_files, args=['-t', 'deps'],
                   expected_out='abcd: deps not found\n')

    def test_query(self):
        in_files, _ = default_test_files()
        self.check(in_files, args=['-t', 'query', 'ab'],
                   expected_out=('ab\n'
                                 '  inputs:\n'
                                 '    a\n'
                                 '    b\n'
                                 '  outputs:\n'
                                 '    abcd\n'))

        self.check(in_files, args=['-t', 'query', 'a'],
                   expected_out=('a\n'
                                 '  outputs:\n'
                                 '    ab\n'))

    def test_rules(self):
        in_files, _ = default_test_files()
        self.check(in_files, args=['-t', 'rules'],
                   expected_out='cat cat $in > $out\n')

    def test_targets(self):
        in_files, _ = default_test_files()

        # print the leaves (FIXME: sort the output).
        self.check(in_files, args=['-t', 'targets', 'rule'],
                   expected_out='a\nc\nb\nd\n')

        # print the outputs built by 'cat'
        self.check(in_files, args=['-t', 'targets', 'rule', 'cat'],
                   expected_out='abcd\nab\ncd\n')

        # print all built objects
        self.check(in_files, args=['-t', 'targets', 'all'],
                   expected_out=('abcd\n'
                                 'ab\n'
                                 'cd\n'))

        # print all built objects
        self.check(in_files, args=['-t', 'targets', 'depth', '2'],
                   expected_out=('abcd\n'
                                 '  ab\n'
                                 '    a\n'
                                 '    b\n'
                                 '  cd\n'
                                 '    c\n'
                                 '    d\n'))

        # print all built objects
        self.check(in_files, args=['-t', 'targets', 'depth'],
                   expected_out=('abcd\n'
                                 '  ab\n'
                                 '  cd\n'))

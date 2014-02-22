import re
import unittest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from host import Host
from main import main, VERSION


class TestMain(unittest.TestCase):
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
        self.check(['-n'], 0, '', '.+')

    def test_usage(self):
        self.check(['--help'], 0, 'usage:.+', '')
        self.check(['-h'], 0, 'usage:.+', '')

    def test_version(self):
        self.check(['--version'], 0, VERSION + '\n', '')


if __name__ == '__main__':
    unittest.main()

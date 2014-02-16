#!/usr/bin/env python

from __future__ import print_function

import re
import unittest

from StringIO import StringIO

from host import Host

import main


class TestMain(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def check(self, cmd_str, returncode, out_regex, err_regex):
        host = Host()
        result = host.call('%s %s %s' % (
                           host.python_interpreter, ' main.py ', cmd_str))
        self.assertEquals(result[0], returncode)
        self.assertTrue(re.match(out_regex, result[1], re.MULTILINE),
                        '%s does not match %s' % (out_regex, result[1]))
        self.assertTrue(re.match(err_regex, result[2], re.MULTILINE),
                        '%s does not match %s' % (err_regex, result[2]))

    def check_main(self, argv, out_regex, err_regex):
        out = StringIO()
        err = StringIO()
        host = Host()

        def print_err(*args, **kwargs):
            print(*args, file=err, **kwargs)

        def print_out(*args, **kwargs):
            print(*args, file=out, **kwargs)

        host.print_err = print_err
        host.print_out = print_out

        main.main(host, argv)

        self.assertTrue(re.match(out_regex, out.getvalue(), re.MULTILINE),
                        '%s does not match %s' % (out_regex, out.getvalue()))
        self.assertTrue(re.match(err_regex, err.getvalue(), re.MULTILINE),
                        '%s does not match %s' % (err_regex, err.getvalue()))

    def test_version(self):
        self.check('--version', 0, main.VERSION + '\n', '')
        try:
            self.check_main(['--version'], main.VERSION + '\n', '')
            self.fail('should have raise PynExit()')
        except Exception as ex:
            self.assertEqual(ex.message, main.VERSION)

    def test_usage(self):
        self.check('--help', 0, 'usage:.+', '')
        self.check('-h', 0, 'usage:.+', '')

    def test_dry_run(self):
        self.check_main(['-n'], '', '.+')


if __name__ == '__main__':
    unittest.main()

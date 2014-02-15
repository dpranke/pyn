#!/usr/bin/env python

from __future__ import print_function

import pymeta_helper
import re
import unittest

from StringIO import StringIO

from host import Host

import main

class TestMain(unittest.TestCase):

    def check(self, cmd_str, returncode, out_regex, err_regex):
        host = Host()
        result = host.call('%s %s %s' % (
                           host.python_interpreter, ' main.py ', cmd_str))
        self.assertEquals(result[0], returncode)
        if not re.match(out_regex, result[1], re.MULTILINE):
            self.fail('%s does not match %s' % (out_regex, result[1]))
        if not re.match(err_regex, result[2], re.MULTILINE):
            self.fail('%s does not match %s' % (err_regex, result[2]))

    def runMain(self, argv, out_regex, err_regex):
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

        if not re.match(out_regex, out.getvalue(), re.MULTILINE):
            self.fail('%s does not match %s' % (out_regex, out.getvalue()))
        if not re.match(err_regex, err.getvalue(), re.MULTILINE):
            self.fail('%s does not match %s' % (err_regex, err.getvalue()))

    def test_version(self):
        self.check('--version', 0, main.VERSION + '\n', '')

    def test_usage(self):
        self.check('--help', 0, 'usage:.+', '')
        self.check('-h', 0, 'usage:.+', '')

    def test_dry_run(self):
        self.assertRaises(pymeta_helper.ParseError, self.runMain, ['-n'], '', '.+')


if __name__ == '__main__':
    unittest.main()

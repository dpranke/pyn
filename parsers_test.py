#!/usr/bin/env python
import textwrap
import unittest

import parsers

from host import Host
from pyn_exceptions import PynException


class TestNinjaParser(unittest.TestCase):
    # disable 'too many public methods' pylint: disable=R0904

    def check(self, text, ast):
        dedented_text = textwrap.dedent(text)
        actual_ast = parsers.parse_ninja_text(Host(), dedented_text)
        self.assertEquals(actual_ast, ast)

    def err(self, text):
        dedented_text = textwrap.dedent(text)
        self.assertRaises(PynException, parsers.parse_ninja_text,
                          Host(), dedented_text)

    def test_syntax_err(self):
        self.err('rule foo')

    def test_sample(self):
        self.check('''
                   cflags = -Wall

                   rule cc
                   command = gcc $cflags -c $in -o $out

                   build foo.o : cc foo.c
                   ''',
                   [['var', 'cflags', '-Wall'],
                    ['rule', 'cc',
                     [['var', 'command', 'gcc $cflags -c $in -o $out']]],
                    ['build', ['foo.o'], 'cc', ['foo.c'], []]])

    def test_simple_build(self):
        self.check('build foo.o : cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], []]])

    def test_simple_cflags(self):
        self.check('cflags = -Wall -O1\n',
                   [['var', 'cflags', '-Wall -O1']])

    def test_simple_default(self):
        self.check('default foo bar\n',
                   [['default', ['foo', 'bar']]])

    def test_simple_rule(self):
        self.check('''
                   rule cc
                   command = gcc $cflags -c $in -o $out
                   ''',
                   [['rule', 'cc',
                     [['var', 'command', 'gcc $cflags -c $in -o $out']]]])

    def test_build_with_deps(self):
        self.check('build foo.o : cc foo.c | foo.h\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], ['foo.h']]])

    def test_no_space_between_output_and_colon(self):
        self.check('build foo.o: cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], []]])


if __name__ == '__main__':
    unittest.main()

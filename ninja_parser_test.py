#!/usr/bin/env python
import textwrap
import unittest

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError

from host import Host


NinjaParser = OMeta.makeGrammar(open('ninja.pymeta').read(), {})


class TestNinjaParser(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def setUp(self):  # 'invalid name' pylint: disable=C0103
        host = Host()
        d = host.dirname(host.path_to_module(__name__))

    def check(self, text, ast):
        dedented_text = textwrap.dedent(text)
        actual_ast = NinjaParser.parse(dedented_text)
        self.assertEquals(actual_ast, ast)

    def err(self, text):
        dedented_text = textwrap.dedent(text)
        self.assertRaises(ParseError, NinjaParser.parse, dedented_text)

    def test_syntax_err(self):
        self.err('rule foo')

    def test_sample(self):
        self.check('''
                   cflags = -Wall

                   rule cc
                       command = gcc $cflags -c $in -o $out

                   build foo.o : cc foo.c
                   ''',
                   [['var', 'cflags', ' -Wall'],
                    ['rule', 'cc',
                     [['var', 'command', ' gcc $cflags -c $in -o $out']]],
                    ['build', ['foo.o'], 'cc', ['foo.c'], [], []]])

    def test_simple_build(self):
        self.check('build foo.o : cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], []]])

    def test_simple_cflags(self):
        self.check('cflags = -Wall -O1\n',
                   [['var', 'cflags', ' -Wall -O1']])

    def test_simple_default(self):
        self.check('default foo bar\n',
                   [['default', ['foo', 'bar']]])

    def test_simple_rule(self):
        self.check('''
                   rule cc
                       command = gcc $cflags -c $in -o $out
                   ''',
                   [['rule', 'cc',
                     [['var', 'command', ' gcc $cflags -c $in -o $out']]]])

    def test_build_with_deps(self):
        self.check('build foo.o : cc foo.c | foo.h\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], ['foo.h'], []]])

    def test_no_space_between_output_and_colon(self):
        self.check('build foo.o: cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], []]])


if __name__ == '__main__':
    unittest.main()

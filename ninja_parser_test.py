#!/usr/bin/env python
import textwrap
import unittest

from common import PynException, Scope
from ninja_parser import parse, expand_vars


class TestNinjaParser(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def check(self, text, ast):
        dedented_text = textwrap.dedent(text)
        actual_ast = parse(dedented_text)
        self.assertEquals(actual_ast, ast)

    def err(self, text):
        dedented_text = textwrap.dedent(text)
        self.assertRaises(PynException, parse, dedented_text)

    def test_blanks(self):
        self.check('', [])
        self.check('\n', [])
        self.check('\n\n', [])

    def test_spaces_in_paths(self):
        self.check('build foo$ bar : cc foo.c',
                   [['build', ['foo bar'], 'cc', ['foo.c'],
                              [], [], []]])

    def test_comments(self):
        self.check('# comment', [])
        self.check('\n# comment', [])
        self.check('cflags = -Wall # comment',
                   [['var', 'cflags', '-Wall']])

    def test_names(self):
        self.check('f = bar', [['var', 'f', 'bar']])
        self.check('foo = bar', [['var', 'foo', 'bar']])
        self.check('foo=bar', [['var', 'foo', 'bar']])
        self.check('foo_123=bar', [['var', 'foo_123', 'bar']])

    def test_syntax_err(self):
        self.err('syntaxerror')

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
                    ['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

    def test_simple_build(self):
        self.check('build foo.o : cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

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
        self.check('build foo : cc',
                   [['build', ['foo'], 'cc', [], [], [], []]])
        self.check('build foo : cc | foo.h',
                   [['build', ['foo'], 'cc', [], ['foo.h'], [], []]])
        self.check('build foo : cc || foo.h',
                   [['build', ['foo'], 'cc', [], [], ['foo.h'], []]])
        self.check('build foo.o : cc foo.c | foo.h\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'],
                              ['foo.h'], [], []]])
        self.check('build foo.o : cc foo.c || foo.idl\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'],
                              [], ['foo.idl'], []]])
        self.check('build foo.o : cc foo.c | foo.h || foo.idl\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'],
                              ['foo.h'], ['foo.idl'], []]])

    def test_no_space_between_output_and_colon(self):
        self.check('build foo.o: cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

    def test_trailing_dollar_sign(self):
        self.check('build foo.o: cc foo.c $\n\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

class TestExpandVars(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def setUp(self):  # 'invalid name' pylint: disable=C0103
        self.scope = Scope('base', None)
        self.scope['foo'] = 'a'
        self.scope['bar'] = 'b'

    def check(self, inp, out):
        self.assertEquals(expand_vars(inp, self.scope), out)

    def err(self, inp):
        self.assertRaises(PynException, expand_vars, inp, self.scope)

    def test_noop(self):
        self.check('xyz', 'xyz')

    def test_simple(self):
        self.check('$foo', 'a')
        self.check('$foo bar', 'a bar')
        self.check('c$foo', 'ca')

    def test_escapes(self):
        self.check('$$', '$')
        self.check('$ ', ' ')
        self.check('$:', ':')

    def test_curlies(self):
        self.check('${foo}', 'a')
        self.check('${foo}bar', 'abar')

    def test_undefined_var_expands_to_nothing(self):
        self.check('$baz', '')

    def test_periods_terminate_variable_names(self):
        self.check('$foo.bar', 'a.bar')

    def test_errors(self):
        self.err('${')
        self.err('${baz')
        self.err('$')
        self.err('$123')
        self.err('${baz foo')


if __name__ == '__main__':
    unittest.main()

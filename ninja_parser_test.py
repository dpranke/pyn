#!/usr/bin/env python
import textwrap
import unittest

from common import PynException, Scope
from ninja_parser import parse, expand_vars


class TestNinjaParser(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def check(self, text, ast, dedent=True):
        if dedent:
            dedented_text = textwrap.dedent(text)
            actual_ast = parse(dedented_text)
        else:
            actual_ast = parse(text)
        self.assertEquals(actual_ast, ast)

    def err(self, text, dedent=True):
        if dedent:
            dedented_text = textwrap.dedent(text)
            self.assertRaises(PynException, parse, dedented_text)
        else:
            self.assertRaises(PynException, parse, text)

    def test_blanks(self):
        self.check('', [])
        self.check('  \n', [], dedent=False)
        self.check('  $\n\n', [], dedent=False)
        self.check('$\n\n', [], dedent=False)
        self.check('  $\n  $\n\n', [], dedent=False)
        self.check('\n', [])
        self.check('\n\n', [])

        # A file w/ spaces but no newline should fail.
        self.err('  ', dedent=False)

    def test_spaces_in_paths(self):
        self.check('build foo$ bar : cc foo.c',
                   [['build', ['foo bar'], 'cc', ['foo.c'],
                              [], [], []]])
        self.check('subninja foo$ bar',
                   [['subninja', 'foo bar']])

    def test_comments(self):
        self.check('# comment', [])
        self.check('# comment\n', [])
        self.check('\n# comment', [])
        self.check('cflags = -Wall # comment',
                   [['var', 'cflags', '-Wall']])

    def test_vars(self):
        self.check('f = bar', [['var', 'f', 'bar']])
        self.check('foo = bar', [['var', 'foo', 'bar']])
        self.check('foo=bar', [['var', 'foo', 'bar']])
        self.check('foo_123=bar', [['var', 'foo_123', 'bar']])
        self.check('foo = ba$ r', [['var', 'foo', 'ba r']])
        self.check('foo = ba$\n  r', [['var', 'foo', 'bar']])
        self.check('foo = ba $\n  r', [['var', 'foo', 'ba r']])

    def test_include(self):
        self.check('include foo.ninja', [['include', 'foo.ninja']])
        self.check('include foo.ninja\n', [['include', 'foo.ninja']])
        self.err('include')
        self.err('include ')

    def test_rule_errs(self):
        self.err('rulefoo')
        self.err('rule 1234')
        self.err('rule foo 1234')

    def test_subninja(self):
        self.check('subninja foo.ninja', [['subninja', 'foo.ninja']])
        self.check('subninja foo.ninja\n', [['subninja', 'foo.ninja']])
        self.err('subninja')
        self.err('subninja ')

    def test_pool(self):
        self.check('''pool foo
                        depth = 1
                   ''', [['pool', 'foo',
                          [['var', 'depth', '1']]]])
        self.err('pool 123')
        self.err('pool foo bar')

    def test_syntax_err(self):
        self.err('syntaxerror')

    def test_sample(self):
        self.check('''
                   cflags = -Wall

                   rule cc
                       command = gcc $cflags -c $in $
                                 -o $out
                       deps = gcc
                       depsfile = $out.d

                   build foo.o : cc foo.c
                   ''',
                   [['var', 'cflags', '-Wall'],
                    ['rule', 'cc',
                     [['var', 'command', 'gcc $cflags -c $in -o $out'],
                      ['var', 'deps', 'gcc'],
                      ['var', 'depsfile', '$out.d']]],
                    ['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

    def test_simple_build(self):
        self.check('build foo.o : cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

    def test_simple_cflags(self):
        self.check('cflags = -Wall -O1\n',
                   [['var', 'cflags', '-Wall -O1']])

    def test_default(self):
        self.check('default foo bar\n',
                   [['default', ['foo', 'bar']]])
        self.check('default foo bar\n',
                   [['default', ['foo', 'bar']]])
        self.err('default')
        self.err('default ')

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

    def test_build_errs(self):
        self.err('buildfoo')
        self.err('build ')
        self.err('build :')
        self.err('build foo.o|')
        self.err('build foo.o:|')
        self.err('build foo.o: cc foo.c |')
        self.err('build foo.o: cc foo.c ||')
        self.err('build foo.o:')
        self.err('build foo.o:|||')

    def test_no_space_between_output_and_colon(self):
        self.check('build foo.o: cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

    def test_trailing_dollar_sign(self):
        self.check('build foo.o: cc foo.c $\n\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])

    def test_var_errs(self):
        # not a legal var name
        self.err('123')

        # no equals sign
        self.err('foo ')


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

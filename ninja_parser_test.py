#!/usr/bin/env python
import textwrap
import unittest

try:
    import ninja_parser
except ImportError as e:
    import subprocess
    err = subprocess.check_call([sys.executable, 'pymeta_helper.py', 'ninja.pym'],
                                cwd=os.path.dirname(__file__))
    if err:
        sys.exit(err)
    import ninja_parser


class TestNinjaParser(unittest.TestCase):
    def check(self, text, ast):
        dedented_text = textwrap.dedent(text)
        actual_ast = ninja_parser.NinjaParser.parse(dedented_text)
        self.assertEquals(actual_ast, ast)

    def err(self, text):
        dedented_text = textwrap.dedent(text)
        self.assertRaises(ninja_parser.ParseError,
                          ninja_parser.NinjaParser.parse, dedented_text)

    def test_syntax_err(self):
        self.err('rule foo')

    def test_sample(self):
        self.check("""
            cflags = -Wall

            rule cc
              command = gcc $cflags -c $in -o $out

            build foo.o : cc foo.c
            """,
            [['var', 'cflags', '-Wall'],
             ['rule', 'cc',
               [['var', 'command', 'gcc $cflags -c $in -o $out']]],
             ['build', ['foo.o'], 'cc', ['foo.c'], []]])


    def test_simple_build(self):
        self.check('build foo.o : cc foo.c\n',
                   [['build', ['foo.o'], 'cc', ['foo.c'], []]])

    def test_simple_cflags(self):
        self.check("cflags = -Wall -O1\n",
                   [['var', 'cflags', '-Wall -O1']])

    def test_simple_rule(self):
        self.check('''
            rule cc
                command = gcc $cflags -c $in -o $out
            ''',
            [['rule', 'cc',
               [['var', 'command', 'gcc $cflags -c $in -o $out']]]])


if __name__ == '__main__':
    unittest.main()

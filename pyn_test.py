#!/usr/bin/env python
import textwrap
import unittest

import pyn


class TestNinjaParser(unittest.TestCase):
    def check(self, text, ast):
        parser = pyn.NinjaParser()
        dedented_text = textwrap.dedent(text)
        actual_ast = parser.parse(dedented_text)
        self.assertEquals(ast, actual_ast)

    def test_simple_cflags(self):
        self.check("cflags = -Wall -O1\n",
                   [['var', 'cflags', '-Wall -O1']])

    def disabled_test_sample(self):
        self.check("""
            cflags = -Wall

            rule cc
              command = gcc $cflags -c $in -o $out

            build foo.o: cc foo.c
            """,
            [['var', 'cflags', '-Wall'],
             ['rule', 'cc', [['var', 'command', 'gcc $cflags -c $in -o $out']]],
             ['build', ['foo.o'], 'cc', ['foo.c']]])


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
import unittest

from common import expand_vars, PynException, Scope


class TestExpandVars(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def setUp(self):  # 'invalid name' pylint: disable=C0103
        self.scope = Scope('base', None)
        self.scope['foo'] = 'a'
        self.scope['bar'] = 'b'

    def check(self, inp, out, additional_vars=None):
        additional_vars = additional_vars or {}
        for k, v in additional_vars.items():
            self.scope[k] = v
        self.assertEquals(expand_vars(inp, self.scope), out)

    def err(self, inp, additional_vars=None):
        additional_vars = additional_vars or {}
        for k, v in additional_vars.items():
            self.scope[k] = v
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

    def test_errors(self):
        self.err('${')
        self.err('${baz')


if __name__ == '__main__':
    unittest.main()

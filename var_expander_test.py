import unittest


from common import PynException, Scope
from var_expander import expand_vars


class TestExpandVars(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def setUp(self):  # 'invalid name' pylint: disable=C0103
        self.scope = Scope('base', None)
        self.scope['foo'] = 'a'
        self.scope['bar'] = 'b'

    def check(self, inp, out):
        self.assertEqual(expand_vars(inp, self.scope), out)

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

import unittest

from stats import Stats


class TestStats(unittest.TestCase):
    def test_basic(self):
        s = Stats('foo', None, None)
        self.assertEqual(s.format(), 'foo')


if __name__ == '__main__':
    unittest.main()
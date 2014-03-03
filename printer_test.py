import unittest

from printer import Printer


class TestPrinter(unittest.TestCase):
    def setUp(self):
        # 'Invalid name' pylint: disable=C0103
        self.out = []

    def print_(self, msg, end='\n'):
        self.out.append(msg + end)

    def test_basic(self):
        pr = Printer(self.print_, False)
        pr.update('foo')
        pr.flush()
        self.assertEqual(self.out, ['foo', '\n'])


if __name__ == '__main__':
    unittest.main()

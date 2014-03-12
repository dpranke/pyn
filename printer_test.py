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

    def test_elide(self):
        pr = Printer(self.print_, False, cols=8)
        pr.update('hello world')
        pr.flush()
        self.assertEqual(self.out, ['hel ...', '\n'])

    def test_overwrite(self):
        pr = Printer(self.print_, True)
        pr.update('hello world')
        pr.update('goodbye world')
        pr.flush()
        self.assertEqual(self.out,
                         ['hello world',
                          '\r           \r',
                          'goodbye world',
                          '\n'])

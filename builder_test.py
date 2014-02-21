import unittest

from builder import Builder


class TestBuilder(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def test_basic(self):
        Builder(None, None, None)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()

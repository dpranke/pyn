#!/usr/bin/env python
import unittest

from builder import Builder


class TestBuilder(unittest.TestCase):
    def test_basic(self):
        Builder(None, None)


if __name__ == '__main__':
    unittest.main()

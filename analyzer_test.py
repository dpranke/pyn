#!/usr/bin/env python
import unittest

from analyzer import NinjaAnalyzer


class TestAnalyzer(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def test_basic(self):
        NinjaAnalyzer(None, None, None)


if __name__ == '__main__':
    unittest.main()

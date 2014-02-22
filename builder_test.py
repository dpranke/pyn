import argparse
import unittest

from host import Host
from ninja_parser import expand_vars
from builder import Builder


class TestBuilder(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904

    def test_basic(self):
        args = argparse.Namespace()
        args.overwrite_status = True
        args.jobs = 1
        args.verbose = 0
        Builder(Host(), args, expand_vars)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()

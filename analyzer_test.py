import unittest

from analyzer import NinjaAnalyzer
from common import PynException
from host_fake import FakeHost


class TestAnalyzer(unittest.TestCase):
    # 'too many public methods' pylint: disable=R0904
    # 'Invalid name 'setUp' pylint: disable=C0103

    def setUp(self):
        self.host = FakeHost()
        self.args = None
        self.parse = lambda msg: []
        self.expand_vars = lambda v, scope: v

    def assertGraphsEqual(self, a, b):
        self.assertEqual(a, b)
        self.fail()

    def check(self, ast, expected_graph=None):
        analyzer = NinjaAnalyzer(self.host, self.args, self.parse,
                                 self.expand_vars)
        actual_graph = analyzer.analyze(ast, 'build.ninja')
        if expected_graph:
            self.assertGraphsEqual(actual_graph, expected_graph)

    def err(self, ast):
        analyzer = NinjaAnalyzer(self.host, self.args, self.parse,
                                 self.expand_vars)
        self.assertRaises(PynException, analyzer.analyze, ast, 'build.ninja')

    def test_empty(self):
        self.check([])

    def test_vars(self):
        self.check([['var', 'foo', 'bar']])

    def test_pool(self):
        self.check([['pool', 'foo', [['var', 'depth', 4]]]])

    def test_subninja_missing(self):
        self.err([['subninja', 'missing.ninja']])

    def test_subninja(self):
        self.host.files['/tmp/sub.ninja'] = ''
        self.check([['subninja', 'sub.ninja']])

    def test_import(self):
        self.host.files['/tmp/sub.ninja'] = ''
        self.check([['include', 'sub.ninja']])

    def test_import_missing(self):
        self.err([['include', 'missing.ninja']])


if __name__ == '__main__':
    unittest.main()

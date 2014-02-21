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

    def check(self, ast):
        analyzer = NinjaAnalyzer(self.host, self.args, self.parse,
                                 self.expand_vars)
        analyzer.analyze(ast, 'build.ninja')

    def err(self, ast):
        analyzer = NinjaAnalyzer(self.host, self.args, self.parse,
                                 self.expand_vars)
        self.assertRaises(PynException, analyzer.analyze, ast, 'build.ninja')

    def test_empty(self):
        self.check([])

    def test_build(self):
        self.check([['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])
        self.err([['build', ['foo.o'], 'cc', ['foo.c'], [], [], []],
                  ['build', ['foo.o'], 'cc', ['foo.c'], [], [], []]])
        self.err([['build', ['foo.o'], 'cc', ['foo.c'], [], [],
                   [['var', 'foo', 'bar'],
                    ['var', 'foo', 'bar']]]])

    def test_vars(self):
        self.check([['var', 'foo', 'bar']])
        self.err([['var', 'foo', 'bar'],
                  ['var', 'foo', 'bar']])

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

    def test_pool(self):
        self.check([['pool', 'foo', [['var', 'depth', 4]]]])
        self.err([['pool', 'foo', [['var', 'depth', 'foo']]]])
        self.err([['pool', 'foo', [['var', 'depth', 4]]],
                  ['pool', 'foo', [['var', 'depth', 4]]]])
        self.err([['pool', 'foo', []]])
        self.err([['pool', 'foo', [['var', 'foo', 4]]]])
        self.err([['pool', 'foo', [['var', 'depth', 4],
                                   ['var', 'foo', 'bar']]]])

    def test_rule(self):
        self.check([['rule', 'cc', [['var', 'command', 'cc -o $out $in']]]])

        self.err([['rule', 'cc', [['var', 'command', 'cc -o $out $in']]],
                  ['rule', 'cc', [['var', 'command', 'cc -o $out $in']]]])
        self.err([['rule', 'cc', [['var', 'command', 'cc -o $out $in'],
                                  ['var', 'command', 'touch $out']]]])

    def test_default(self):
        self.check([['default', ['all']]])

if __name__ == '__main__':
    unittest.main()

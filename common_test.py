import unittest

from common import Graph, Node, Rule, Scope, PynException, \
    find_nodes_to_build, tsort


# 'too many public methods' pylint: disable=R0904


class TestGraph(unittest.TestCase):
    def test_repr(self):
        self.assertEqual(repr(Graph('build.ninja')),
                         'Graph(name="build.ninja")')


class TestNode(unittest.TestCase):
    def test_repr(self):
        self.assertEqual(repr(Node('foo.o', ['foo.o'], Scope('build.ninja',
                                                             None),
                                   'cc', [])),
                         'Node(name="foo.o")')


class TestRule(unittest.TestCase):
    def test_repr(self):
        self.assertEqual(repr(Rule('cc', Scope('build.ninja', None))),
                         'Rule(name="cc")')


class TestScope(unittest.TestCase):
    def setUp(self):
        # 'Invalid name' pylint: disable=C0103
        self.p = Scope('build.ninja', None)
        self.c = Scope('foo.subninja', self.p)
        self.p['foo'] = 'p-foo'
        self.p['bar'] = 'p-bar'
        self.c['foo'] = 'c-foo'

    def test_repr(self):
        self.assertEqual(repr(self.p), 'Scope(name="build.ninja")')
        self.assertEqual(repr(self.c), 'Scope(name="foo.subninja")')

    def test_basic(self):
        self.assertEqual(self.p['foo'], 'p-foo')
        self.assertEqual(self.p['baz'], '')
        self.assertTrue('foo' in self.p)
        self.assertEqual(self.c['foo'], 'c-foo')
        self.assertEqual(self.c['bar'], 'p-bar')

    def test_update_child(self):
        self.c['foo'] = 'c-foo2'
        self.assertEqual(self.p['foo'], 'p-foo')
        self.assertEqual(self.c['foo'], 'c-foo2')

    def test_delete_child(self):
        del self.c['foo']
        self.assertEqual(self.p['foo'], 'p-foo')
        self.assertEqual(self.c['foo'], 'p-foo')

        del self.c['foo']
        self.assertEqual(self.p['foo'], 'p-foo')
        self.assertEqual(self.c['foo'], 'p-foo')


class TestTsort(unittest.TestCase):
    def test_cycle(self):
        g = Graph('build.ninja')
        n1 = Node(name='foo.so', scope='build.ninja', outputs=['foo.so'],
                  rule_name='shlib', explicit_deps=['bar.so'])
        n2 = Node(name='bar.so', scope='build.ninja', outputs=['bar.so'],
                  rule_name='shlib', explicit_deps=['foo.so'])
        g.nodes[n1.name] = n1
        g.nodes[n2.name] = n2
        self.assertRaises(PynException, tsort, g, ['foo.so'])

    def test_simple(self):
        g = Graph('build.ninja')
        n1 = Node(name='foo.so', scope='build.ninja', outputs=['foo.so'],
                  rule_name='shlib', explicit_deps=['foo.o'])
        n2 = Node(name='foo.o', scope='build.ninja', outputs=['foo.o'],
                  rule_name='cc', explicit_deps=['foo.c'])
        g.nodes[n1.name] = n1
        g.nodes[n2.name] = n2
        self.assertEqual(tsort(g, [n1.name]), [n2.name, n1.name])


class TestFindNodesToBuild(unittest.TestCase):
    def test_simple(self):
        g = Graph('build.ninja')
        n1 = Node(name='foo.so', scope='build.ninja', outputs=['foo.so'],
                  rule_name='shlib', explicit_deps=['foo.o'])
        n2 = Node(name='foo.o', scope='build.ninja', outputs=['foo.so'],
                  rule_name='cc', explicit_deps=['foo.c'])
        g.nodes[n1.name] = n1
        g.nodes[n2.name] = n2
        self.assertEqual(find_nodes_to_build(g, [n1.name]),
                         set([n1.name, n2.name]))


if __name__ == '__main__':
    unittest.main()

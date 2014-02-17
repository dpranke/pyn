#!/usr/bin/env python
import unittest

from common import Graph, Node, Rule, Scope


# 'too many public methods' pylint: disable=R0904


class TestGraph(unittest.TestCase):
    def test_repr(self):
        self.assertEquals(repr(Graph()),
                          ('Graph(defaults=[], nodes={}, pools={},'
                           ' rules={}, scopes={})'))


class TestNode(unittest.TestCase):
    def test_repr(self):
        self.assertEquals(repr(Node('foo.o', Scope('build.ninja', None),
                                    'cc', [])),
                          'Node(name=foo.o, scope=build.ninja,'
                          ' rule_name=cc, deps=[])')


class TestRule(unittest.TestCase):
    def test_repr(self):
        self.assertEquals(repr(Rule('cc', Scope('build.ninja', None))),
                          'Rule(name=cc, scope=build.ninja)')


class TestScope(unittest.TestCase):
    def setUp(self):
        # 'Invalid name' pylint: disable=C0103
        self.p = Scope('build.ninja', None)
        self.c = Scope('foo.subninja', self.p)
        self.p['foo'] = 'p-foo'
        self.p['bar'] = 'p-bar'
        self.c['foo'] = 'c-foo'

    def test_repr(self):
        self.assertEquals(repr(self.p),
                          "Scope(name=build.ninja, parent=None, "
                          "objs={'foo': 'p-foo', 'bar': 'p-bar'})")
        self.assertEquals(repr(self.c),
                          "Scope(name=foo.subninja, parent=build.ninja, "
                          "objs={'foo': 'c-foo'})")

    def test_basic(self):
        self.assertEquals(self.p['foo'], 'p-foo')
        self.assertEquals(self.p['baz'], '')
        self.assertTrue('foo' in self.p)
        self.assertEquals(self.c['foo'], 'c-foo')
        self.assertEquals(self.c['bar'], 'p-bar')

    def test_update_child(self):
        self.c['foo'] = 'c-foo2'
        self.assertEquals(self.p['foo'], 'p-foo')
        self.assertEquals(self.c['foo'], 'c-foo2')

    def test_delete_child(self):
        del self.c['foo']
        self.assertEquals(self.p['foo'], 'p-foo')
        self.assertEquals(self.c['foo'], 'p-foo')

        del self.c['foo']
        self.assertEquals(self.p['foo'], 'p-foo')
        self.assertEquals(self.c['foo'], 'p-foo')


if __name__ == '__main__':
    unittest.main()

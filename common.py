class PynException(Exception):
    pass


class Graph(object):
    def __init__(self, name):
        self.name = name
        self.defaults = []
        self.nodes = {}
        self.rules = {}
        self.pools = {}
        self.scopes = {}
        self.subninjas = set()
        self.includes = set()

    def __repr__(self):
        return 'Graph(name="%s")' % self.name


class Node(object):
    def __init__(self, name, scope, rule_name, deps):
        self.name = name
        self.scope = scope
        self.rule_name = rule_name
        self.deps = deps
        self.running = False

    def __repr__(self):
        return 'Node(name="%s")' % self.name


def find_nodes_to_build(graph, requested_targets):
    """Return all of the nodes the requested targets depend on."""
    unvisited_nodes = requested_targets[:]
    unvisited_set = set(unvisited_nodes)
    nodes_to_build = set()
    while unvisited_nodes:
        node = unvisited_nodes.pop(0)
        unvisited_set.remove(node)
        nodes_to_build.add(node)
        for d in graph.nodes[node].deps:
            if d not in nodes_to_build and d not in unvisited_set and d in graph.nodes:
                unvisited_nodes.append(d)
                unvisited_set.add(d)
    return nodes_to_build


def tsort(graph, nodes_to_build):
    """Sort a list of nodes based on their dependencies (leaves first)."""
    # This performs a topological sort of the nodes in the graph by
    # picking nodes arbitrarily, and then doing depth-first searches
    # across the graph from there. It should run in O(|nodes|) time.
    # See http://en.wikipedia.org/wiki/Topological_sorting and Tarjan (1976).
    #
    # This algorithm diverges a bit from the Wikipedia algorithm by
    # inserting new nodes at the tail of the sorted node list instead of the
    # head, because we want to ultimately do a bottom-up traversal.
    def visit(node, visited_nodes, sorted_nodes, unvisited_nodes,
              unvisited_set, sorted_set):
        if node in visited_nodes:
            raise PynException("'%s' is part of a cycle" % node)

        visited_nodes.add(node)
        for d in graph.nodes[node].deps:
            if d in graph.nodes and d not in sorted_set:
                visit(d, visited_nodes, sorted_nodes, unvisited_nodes,
                      unvisited_set, sorted_set)
        if node in unvisited_nodes:
            unvisited_nodes.remove(node)
            unvisited_set.remove(node)
        sorted_nodes.append(node)
        sorted_set.add(node)

    visited_nodes = set()
    unvisited_nodes = [n for n in nodes_to_build]
    sorted_nodes = []
    sorted_set = set(sorted_nodes)
    unvisited_set = set(unvisited_nodes)
    while unvisited_nodes:
        visit(unvisited_nodes[0], visited_nodes, sorted_nodes, unvisited_nodes,
              unvisited_set, sorted_set)
    return sorted_nodes


class Rule(object):
    def __init__(self, name, scope):
        self.name = name
        self.scope = scope

    def __repr__(self):
        return 'Rule(name=%s, scope=%s)' % (self.name, self.scope.name)


class Scope(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.objs = {}

    def __repr__(self):
        if self.parent:
            parent_scope = '"%s"' % self.parent.name
        else:
            parent_scope = 'None'
        s = []
        return 'Scope(name="%s", parent=%s)' % (self.name, parent_scope)

    def __contains__(self, key):
        return key in self.objs or (self.parent and key in self.parent)

    def __setitem__(self, key, value):
        self.objs[key] = value

    def __delitem__(self, key):
        if key in self.objs:
            del self.objs[key]

    def __getitem__(self, key):
        if key in self.objs:
            return self.objs[key]
        if self.parent:
            return self.parent[key]
        return ''

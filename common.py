class PynException(Exception):
    pass


class PynExit(Exception):
    pass


class Graph(object):
    def __init__(self):
        self.defaults = []
        self.nodes = {}
        self.rules = {}
        self.pools = {}
        self.scopes = {}

    def __repr__(self):
        return ('Graph(defaults=%s, nodes=%s, pools=%s, rules=%s, scopes=%s)' %
                (self.defaults, self.nodes, self.pools, self.rules,
                 self.scopes))


class Node(object):
    def __init__(self, name, scope, rule_name, deps):
        self.name = name
        self.scope = scope
        self.rule_name = rule_name
        self.deps = deps

    def __repr__(self):
        return 'Node(name=%s, scope=%s, rule_name=%s, deps=%s)' % (
            self.name, self.scope, self.rule_name, self.deps)


def find_nodes_to_build(graph, requested_targets):
    """Return all of the nodes the requested targets depend on."""
    unvisited_nodes = requested_targets[:]
    nodes_to_build = set()
    while unvisited_nodes:
        node = unvisited_nodes.pop(0)
        nodes_to_build.add(node)
        for d in graph.nodes[node].deps:
            if d not in nodes_to_build and d in graph.nodes:
                unvisited_nodes.append(d)
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
    def visit(node, visited_nodes, sorted_nodes, unvisited_nodes):
        if node in visited_nodes:
            raise PynException("'%s' is part of a cycle" % node)

        visited_nodes.add(node)
        for m in graph.nodes[node].deps:
            if m in graph.nodes and m not in sorted_nodes:
                visit(m, visited_nodes, sorted_nodes, unvisited_nodes)
        unvisited_nodes.remove(node)
        sorted_nodes.append(node)

    visited_nodes = set()
    sorted_nodes = []
    unvisited_nodes = [n for n in nodes_to_build]
    while unvisited_nodes:
        visit(unvisited_nodes[0], visited_nodes, sorted_nodes, unvisited_nodes)
    return sorted_nodes


class Rule(object):
    def __init__(self, name, scope):
        self.name = name
        self.scope = scope

    def __repr__(self):
        return 'Rule(name=%s, scope=%s)' % (self.name, self.scope)


class Scope(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.objs = {}

    def __repr__(self):
        if self.parent:
            parent_scope = self.parent.name
        else:
            parent_scope = 'None'
        return 'Scope(name=%s, parent=%s, objs=%s)' % (
                self.name, parent_scope, self.objs)

    def __contains__(self, key):
        return key in self.objs or (self.parent and key in self.parent)

    def __setitem__(self, key, value):
        self.objs[key] = value

    def __delitem__(self, key):
        del self.objs[key]

    def __getitem__(self, key):
        if key in self.objs:
            return self.objs[key]
        if self.parent:
            return self.parent[key]
        raise KeyError(key)


def expand_vars(msg, scope):
    """Expand the vars in the given string using the variables in scope."""
    expanded_msg = msg.replace('$out', scope.objs['out'])
    expanded_msg = expanded_msg.replace('$in', scope.objs['in'])
    return expanded_msg

class PynException(Exception):
    pass


class PynExit(Exception):
    pass


class Graph(object):
    def __init__(self):
        self.nodes = {}
        self.rules = {}
        self.global_vars = {}
        self.defaults = {}

    def __repr__(self):
        return 'Graph(nodes=%s, rules=%s, global_vars=%s, defaults=%s)' % (
            self.nodes, self.rules, self.global_vars, self.defaults)


class Node(object):
    def __init__(self, name, rule_name, inputs, deps):
        self.name = name
        self.rule_name = rule_name
        self.inputs = inputs
        self.deps = deps

    def __repr__(self):
        return 'Node(name=%s, rule_name=%s, inputs=%s, deps=%s)' % (
            self.name, self.rule_name, self.inputs, self.deps)


class Rule(object):
    def __init__(self, name):
        self.name = name
        self.rule_vars = {}

    def __repr__(self):
        return 'Rule(name=%s, rule_vars=%s)' % (self.name, self.rule_vars)


def find_nodes_to_build(graph, requested_targets):
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

from pyn_exceptions import PynException


class Builder(object):
    def __init__(self, host, args):
        self._host = host
        self._args = args
        self._mtimes = {}

    def build(self, graph):
        requested_targets = self._args.targets or graph.defaults
        nodes_to_build = find_nodes_to_build(graph, requested_targets)
        sorted_nodes = tsort(graph, nodes_to_build)
        sorted_nodes = [n for n in sorted_nodes
                        if graph.nodes[n].rule_name != 'phony']
        total_nodes = len(sorted_nodes)
        num_builds = 0

        for name in sorted_nodes:
            node = graph.nodes[name]
            if self._host.exists(name):
                my_mtime = self._mtime(name)
                do_build = any(self._mtime(d) > my_mtime for d in node.deps)
            else:
                do_build = True

            if do_build:
                num_builds += 1
                self._build_node(graph, node, num_builds, total_nodes)
                self._restat(name)
            else:
                total_nodes -= 1

        if not num_builds:
            self._host.print_err('pyn: no work to do')

    def _build_node(self, graph, node, cur, total_nodes):
        if node.rule_name == 'phony':
            self._host.print_err('[%d/%d] %s' % (cur, total_nodes, node.name))
            return

        rule = graph.rules[node.rule_name]
        command = rule.rule_vars.get('command')
        command = command.replace('$out', node.name)
        command = command.replace('$in', ' '.join(node.inputs))
        if self._args.dry_run:
            ret, out, err = 0, '', ''
        else:
            ret, out, err = self._host.call(command)
        if ret or out or err or self._args.verbose > 1:
            self._host.print_err('[%d/%d] %s' % (cur, total_nodes, command))
            if out:
                self._host.print_out(out)
            if err:
                self._host.print_err(err)
            if ret:
                raise PynException('build failed')
        else:
            desc = rule.rule_vars.get('description', '%s $out' %
                                      node.rule_name)
            desc = desc.replace('$out', node.name)
            desc = desc.replace('$in', ' '.join(node.inputs))
            self._host.print_err('[%d/%d] %s' % (cur, total_nodes, desc))

    def clean(self, graph):
        outputs = [n.name for n in graph.nodes.values()
                   if n.rule_name != 'phony' and self._host.exists(n.name)]
        self._host.print_err('Cleaning...')
        for o in outputs:
            if self._args.verbose:
                self._host.print_err('Remove %s' % o)
            if not self._args.dry_run:
                self._host.remove(o)
        self._host.print_err('%d files' % len(outputs))

    def _mtime(self, name):
        if not name in self._mtimes:
            self._restat(name)
        return self._mtimes[name]

    def _restat(self, name):
        self._mtimes[name] = self._host.mtime(name)


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

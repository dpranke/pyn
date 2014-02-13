from pyn_exceptions import PynException


def build(host, args, graph):
    sorted_nodes = _tsort(graph)
    total_nodes = len(sorted_nodes)
    for cur, name in enumerate(sorted_nodes, start=1):
        node = graph.nodes[name]
        _build_node(host, args, graph, node, cur, total_nodes)


def _build_node(host, args, graph, node, cur, total_nodes):
    if node.rule_name == 'phony':
        return

    rule = graph.rules[node.rule_name]
    command = rule.rule_vars.get('command')
    command = command.replace('$out', node.name)
    command = command.replace('$in', ' '.join(node.inputs))
    if args.dry_run:
        ret, out, err = 0, '', ''
    else:
        ret, out, err = host.call(command)
    if ret or out or err or args.verbose > 1:
        host.print_err('[%d/%d] %s' % (cur, total_nodes, command))
        if out:
            host.print_out(out)
        if err:
            host.print_err(err)
    else:
        desc = rule.rule_vars.get('description', '%s $out' % node.rule_name)
        desc = desc.replace('$out', node.name)
        desc = desc.replace('$in', ' '.join(node.inputs))
        host.print_err('[%d/%d] %s' % (cur, total_nodes, desc))


def _tsort(graph):
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
    unvisited_nodes = graph.nodes.keys()[:]
    while unvisited_nodes:
        visit(unvisited_nodes[0], visited_nodes, sorted_nodes, unvisited_nodes)
    return sorted_nodes

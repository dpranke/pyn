from builder import Builder
from common import find_nodes_to_build, tsort
from var_expander import expand_vars


def check(host, _args, _old_graph, _graph, _started_time):
    """check the syntax of the build files"""
    host.print_out('pyn: syntax is correct.')
    return 0


def clean(host, args, _old_graph, graph, _started_time):
    """clean built files"""

    files_to_remove = []
    for output_name, node in graph.nodes.items():
        if (node.rule_name != 'phony' and host.exists(output_name) and
                (node.scope['generator'] != '1' or '-g' in args.targets)):
            files_to_remove.append(output_name)

    if host.exists('.pyn.db') and '-g' in args.targets:
        files_to_remove.append('.pyn.db')
    if args.verbose:
        host.print_err('Cleaning...')
    else:
        host.print_err('Cleaning... ', end='')

    for f in files_to_remove:
        if args.verbose:
            host.print_err('Remove %s' % f)
        if not args.dry_run:
            host.remove(f)

    host.print_err('%d files.' % len(files_to_remove))
    return 0


def commands(host, args, _old_graph, graph, _started_time):
    """list all commands required to rebuild given targets"""
    requested_targets = args.targets or graph.default
    nodes_to_build = find_nodes_to_build(graph, requested_targets)
    sorted_nodes = tsort(graph, nodes_to_build)
    sorted_nodes = [n for n in sorted_nodes
                    if graph.nodes[n].rule_name != 'phony']

    for node_name in sorted_nodes:
        node = graph.nodes[node_name]
        rule = graph.rules[node.rule_name]
        host.print_out(expand_vars(rule.scope['command'], node.scope,
                                   rule.scope))


def question(host, args, old_graph, graph, started_time):
    """check to see if the build is up to date"""

    builder = Builder(host, args, expand_vars, started_time)
    nodes_to_build = builder.find_nodes_to_build(old_graph, graph)
    if nodes_to_build:
        host.print_out('pyn: build is not up to date.')
        return 1
    else:
        host.print_out('pyn: no work to do.')
        return 0


def tool_names():
    return _TOOLS.keys()


def list_tools(host):
    """print this message"""

    host.print_out('pyn subtools:')
    for tool in sorted(_TOOLS.keys()):
        host.print_out("%10s  %s" % (tool, _TOOLS[tool].__doc__))


def run_tool(host, args, old_graph, graph, started_time):
    return _TOOLS[args.tool](host, args, old_graph, graph, started_time)


_TOOLS = {
    'check': check,
    'clean': clean,
    'commands': commands,
    'list': list_tools,
    'question': question,
}

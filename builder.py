from common import tsort, find_nodes_to_build, PynException


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

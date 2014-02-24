from common import find_nodes_to_build, tsort
from stats import Stats
from printer import Printer


class Builder(object):
    def __init__(self, host, args, expand_vars, started_time):
        self.host = host
        self.args = args
        self._should_overwrite = args.overwrite_status and not args.verbose
        self.expand_vars = expand_vars
        self.stats = Stats(host.getenv('NINJA_STATUS', '[%s/%t] '),
                           host.time, started_time)
        self._printer = Printer(host.print_out, self._should_overwrite)
        self._mtimes = {}
        self._failures = 0
        self._pool = self.host.mp_pool(args.jobs)

    def find_nodes_to_build(self, old_graph, graph):
        requested_targets = self.args.targets or graph.defaults
        nodes_to_build = find_nodes_to_build(graph, requested_targets)
        sorted_nodes = tsort(graph, nodes_to_build)
        sorted_nodes = [n for n in sorted_nodes
                        if graph.nodes[n].rule_name != 'phony']

        nodes_to_build = []
        for node_name in sorted_nodes:
            n = graph.nodes[node_name]
            my_stat = self._stat(node_name)
            if not my_stat or any(self._stat(d) > my_stat for d in n.deps()):
                nodes_to_build.append(node_name)
                continue

            if old_graph and node_name in old_graph.nodes:
                if (self._command(old_graph, node_name) !=
                        self._command(graph, node_name)):
                    nodes_to_build.append(node_name)
                    continue

        return nodes_to_build

    def build(self, graph, nodes_to_build):
        stats = self.stats
        stats.total = len(nodes_to_build)
        stats.started = 0
        stats.started_time = self.host.time()

        running_jobs = []
        try:
            while nodes_to_build and self._failures < self.args.errors:
                while stats.started - stats.finished < self.args.jobs:
                    n = self._find_next_available_node(graph, nodes_to_build)
                    if n:
                        p = self._build_node(graph, n)
                        running_jobs.append((n, p))
                    else:
                        break
                did_work = self._process_completed_jobs(graph, running_jobs)
                if (not did_work and nodes_to_build and
                        self._failures < self.args.errors):
                    self.host.sleep(0.01)

            self._pool.close()
            while running_jobs:
                self._process_completed_jobs(graph, running_jobs)
                if not did_work and running_jobs:
                    self.host.sleep(0.01)
        finally:
            self._pool.terminate()
            self._pool.join()

        self._printer.flush()
        return 1 if self._failures else 0

    def _find_next_available_node(self, graph, nodes_to_build):
        next_node = None
        for node_name in nodes_to_build:
            n = graph.nodes[node_name]
            if not any(d in graph.nodes and graph.nodes[d].running
                       for d in n.deps(include_order_only=True)):
                next_node = node_name
                break

        if next_node:
            nodes_to_build.remove(next_node)
        return next_node

    def _command(self, graph, node_name):
        node = graph.nodes[node_name]
        rule = graph.rules[node.rule_name]
        return self.expand_vars(rule.scope['command'], node.scope)

    def _build_node(self, graph, node_name):
        node = graph.nodes[node_name]
        rule = graph.rules[node.rule_name]
        desc = self.expand_vars(rule.scope['description'], node.scope)
        command = self.expand_vars(rule.scope['command'], node.scope)

        self._build_node_started(node, desc, command)

        dry_run = node.rule_name == 'phony' or self.args.dry_run
        return self._pool.apply_async(_call, (node.name, desc, command,
                                              dry_run, self.host))

    def _process_completed_jobs(self, graph, running_jobs):
        completed_jobs = [(n, p) for n, p in running_jobs if p.ready()]
        did_work = False
        for n, p in completed_jobs:
            running_jobs.remove((n, p))
            self._build_node_done(graph, p.get(timeout=0))
            did_work = True
        return did_work

    def _build_node_started(self, node, desc, command):
        node.running = True
        self.stats.started += 1
        if self.args.verbose > 1:
            self._update(command, elide=False)
        else:
            self._update(desc)

    def _build_node_done(self, graph, result):
        node_name, desc, command, ret, out, err = result
        n = graph.nodes[node_name]
        n.running = False

        if n.scope['depfile'] and n.scope['deps'] == 'gcc':
            path = self.expand_vars(n.scope['depfile'], n.scope)
            if self.host.exists(path):
                depsfile_deps = self.host.read(path).split()[2:]
                self.host.remove(path)
                if n.depsfile_deps != depsfile_deps:
                    n.depsfile_deps = depsfile_deps
                    graph.dirty = True

        self.stats.finished += 1

        if ret:
            self._failures += 1
            self._update(command, prefix='FAILED: ', elide=False)
        elif self.args.verbose > 1:
            self._update(command, elide=False)
        elif self.args.verbose:
            self._update(desc, elide=False)
        elif self._should_overwrite:
            self._update(desc)
        if out or err:
            self._printer.flush()
        if out:
            self.host.print_out(out, end='')
        if err:
            self.host.print_err(err, end='')

    def _update(self, msg, prefix=None, elide=True):
        prefix = prefix or self.stats.format()
        self._printer.update(prefix + msg, elide=elide)

    def _stat(self, name):
        if not name in self._mtimes:
            self._restat(name)
        return self._mtimes.get(name, 0)

    def _restat(self, name):
        if self.host.exists(name):
            self._mtimes[name] = self.host.mtime(name)
        else:
            self._mtimes[name] = 0


def _call(node_name, desc, command, dry_run, host):
    if dry_run:
        ret, out, err = 0, '', ''
    else:
        ret, out, err = host.call(command)
    return (node_name, desc, command, ret, out, err)

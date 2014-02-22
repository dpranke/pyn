from common import find_nodes_to_build, tsort, PynException
from stats import Stats


class Builder(object):
    def __init__(self, host, args, expand_vars):
        self.host = host
        self.args = args
        self.expand_vars = expand_vars
        self.stats = Stats(host.getenv('NINJA_STATUS', '[%s/%t] '),
                           host.time)
        self._mtimes = {}
        self._failures = 0
        self._last_line = ''
        self._should_overwrite = args.overwrite_status and not args.verbose
        self._pool = self.host.mp_pool(args.jobs)

    def build(self, graph, question=False):
        requested_targets = self.args.targets or graph.defaults
        nodes_to_build = find_nodes_to_build(graph, requested_targets)
        sorted_nodes = tsort(graph, nodes_to_build)
        sorted_nodes = [n for n in sorted_nodes
                        if graph.nodes[n].rule_name != 'phony']

        nodes_to_build = []
        for name in sorted_nodes:
            node = graph.nodes[name]
            my_mtime = self._stat(name)
            if any(self._stat(d) >= my_mtime for d in node.deps):
                nodes_to_build.append(node)

        if not nodes_to_build:
            self.host.print_out('pyn: no work to do')
            return

        if question:
            raise PynException('build is not up to date.')

        self.stats.total = len(nodes_to_build)
        self.stats.started = 0
        self.stats.started_time = self.host.time()

        running_jobs = []
        while nodes_to_build and self._failures < self.args.errors:
            while self.stats.started - self.stats.finished < self.args.jobs:
                n = self._find_next_available_node(graph, nodes_to_build)
                if n:
                    p = self._build_node(graph, n)
                    running_jobs.append((n, p))
                else:
                    break
            self._process_completed_jobs(running_jobs)
            if nodes_to_build and self._failures < self.args.errors:
                self.host.sleep(0.03)

        while running_jobs:
            self._process_completed_jobs(running_jobs)
            if running_jobs:
                self.host.sleep(0.03)

        self.host.print_err('')

    @staticmethod
    def _find_next_available_node(graph, nodes_to_build):
        next_node = None
        for n in nodes_to_build:
            if not any(d in graph.nodes and graph.nodes[d].running
                       for d in n.deps):
                next_node = n
                break

        if next_node:
            nodes_to_build.remove(next_node)
        return next_node

    def _process_completed_jobs(self, running_jobs):
        completed_jobs = [(n, p) for n, p in running_jobs if p.ready()]
        for n, p in completed_jobs:
            running_jobs.remove((n, p))
            self._build_done(p.get(timeout=0))

    def _build_node(self, graph, node):
        rule = graph.rules[node.rule_name]
        desc = self.expand_vars(rule.scope['description'], node.scope)
        command = self.expand_vars(rule.scope['command'], node.scope)

        self.stats.started += 1
        if self.args.verbose > 1:
            self._start(command, elide=False)
        else:
            self._start(desc)

        def call(command):
            if node.rule_name == 'phony' or self.args.dry_run:
                ret, out, err = 0, '', ''
            else:
                ret, out, err = self.host.call(command)
            return (node, desc, command, ret, out, err)

        return self._pool.apply_async(call, (command,))

    def _build_done(self, result):
        node, desc, command, ret, out, err = result
        node.running = False
        self.stats.finished += 1
        if ret:
            self._failures += 1
            self._update('FAILED: ' + command)
        elif self.args.verbose > 1:
            self._finish(command, elide=False)
        elif self.args.verbose:
            self._finish(desc, elide=False)
        else:
            self._finish(desc)
        if out:
            self.host.print_out(out)
        if err:
            self.host.print_err(err)

    def _start(self, msg, elide=True):
        if elide:
            msg = msg[:78]
        self._update(self.stats.format() + msg)

    def _finish(self, msg, elide=True):
        if elide:
            msg = msg[:78]
        if self._should_overwrite:
            self._update(self.stats.format() + msg)

    def _update(self, msg):
        if msg == self._last_line:
            return
        if self._should_overwrite:
            self.host.print_err('\r' + ' ' * len(self._last_line) + '\r',
                                end='')
        elif self._last_line:
            self.host.print_err('')
        self.host.print_err(msg, end='')
        last_nl = msg.rfind('\n')
        self._last_line = msg[last_nl + 1:]

    def clean(self, graph):
        outputs = [n.name for n in list(graph.nodes.values())
                   if n.rule_name != 'phony' and self.host.exists(n.name)]
        self.host.print_err('Cleaning...')
        for o in outputs:
            if self.args.verbose:
                self.host.print_err('Remove %s' % o)
            if not self.args.dry_run:
                self.host.remove(o)
        self.host.print_err('%d files' % len(outputs))

    def _stat(self, name):
        if not name in self._mtimes:
            self._restat(name)
        return self._mtimes.get(name, -1)

    def _restat(self, name):
        if self.host.exists(name):
            self._mtimes[name] = self.host.mtime(name)
        else:
            self._mtimes[name] = -1

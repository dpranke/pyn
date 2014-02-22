import time

from common import find_nodes_to_build, tsort, PynException


class Stats(object):
    def __init__(self, status_format):
        self.fmt = status_format
        self.finished = 0
        self.started = 0
        self.total = 0
        self.running = 0
        self.started_time = None

    def format(self):
        out = ''
        p = 0
        end = len(self.fmt)
        while p < end:
            c = self.fmt[p]
            if c == '%' and p < end - 1:
                cn = self.fmt[p + 1]
                if cn == 'e':
                    out += int(time.time() - self.started_time)
                elif cn == 'f':
                    out += str(self.finished)
                elif cn == 'o':
                    now = time.time()
                    if now > self.started_time:
                        out += '%5.1f' % (self.finished - self.started /
                                          now - self.started_time)
                    else:
                        out += '-'
                elif cn == 'p':
                    out += '%5.1f' % (self.started * 100.0 / self.total)
                elif cn == 'r':
                    out += str(self.started - self.finished)
                elif cn == 's':
                    out += str(self.started)
                elif cn == 't':
                    out += str(self.total)
                elif cn == '%%':
                    out += '%'
                else:
                    out += cn
                p +=2
            else:
                out += c
                p += 1
        return out


class Builder(object):
    def __init__(self, host, args, expand_vars):
        self.host = host
        self.args = args
        self.expand_vars = expand_vars
        self.stats = Stats(host.getenv('NINJA_STATUS', '[%s/%t] '))
        self._mtimes = {}
        self._last_line = ''
        self._should_overwrite = args.overwrite_status

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
        self.stats.start_time = time.time()

        while nodes_to_build:
            node = nodes_to_build.pop(0)
            self._build_node(graph, node)
        if self._last_line:
            self.host.print_err('')

    def _build_node(self, graph, node):
        if node.rule_name == 'phony':
            self._finish(node.name)
            return

        rule = graph.rules[node.rule_name]
        desc = self.expand_vars(rule.scope['description'], node.scope)
        command = self.expand_vars(rule.scope['command'], node.scope)
        if self.args.verbose > 1:
            self._start(node.name, command, elide=False)
        else:
            self._start(node.name, desc)

        if self.args.dry_run:
            ret, out, err = 0, '', ''
        else:
            ret, out, err = self.host.call(command)

        if ret or out or err or self.args.verbose > 1:
            if ret or self.args.verbose > 1:
                self._finish(node.name, command, elide=False)
            else:
                self._finish(node.name, desc, elide=False)

            if out:
                self.host.print_out(out)
            if err:
                self.host.print_err(err)
            if ret:
                raise PynException('build failed')
        else:
            self._finish(node.name, desc)

    def _start(self, node_name, msg, elide=True):
        self.stats.started += 1
        self._update(self.stats.format() + msg)

    def _finish(self, node_name, msg, elide=True):
        self.stats.finished += 1
        self._update(self.stats.format() + msg)

    def _update(self, msg):
        if msg == self._last_line:
            return
        if self._should_overwrite:
            self.host.print_err('\r' + ' '* len(self._last_line) + '\r', end='')
        else:
            self.host.print_err('')
        self.host.print_err(msg, end='')
        last_nl = msg.rfind('\n')
        self._last_line = msg[last_nl + 1:]

    def clean(self, graph):
        outputs = [n.name for n in graph.nodes.values()
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

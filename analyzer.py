from common import Graph, Node, PynException, Rule, Scope


class NinjaAnalyzer(object):
    # "method could be a function" pylint: disable=R0201
    def __init__(self, host, args, parse, expand_vars):
        self.host = host
        self.args = args
        self.parse = parse
        self.expand_vars = expand_vars

    def analyze(self, ast, filename=None, graph=None, scope=None):
        assert filename or (graph and scope)
        graph = graph or Graph()
        scope = scope or Scope(filename, None)
        graph.scopes[filename] = scope
        for decl in ast:
            graph = getattr(self, '_decl_' + decl[0])(graph, scope, decl)

        self._add_deps_in_depfiles(graph)

        return graph

    def _decl_build(self, graph, scope, decl):
        _, outputs, rule_name, inputs, ideps, odeps, build_vars = decl

        build_name = ' '.join(outputs)
        build_scope = Scope(build_name, scope)
        build_scope['out'] = ' '.join(outputs)
        build_scope['in'] = ' '.join(inputs)
        self._add_vars_to_scope(build_vars, build_scope)

        n = Node(build_name, build_scope, rule_name, inputs + ideps + odeps)
        self._add_outputs_to_graph(outputs, n, graph)
        return graph

    def _decl_default(self, graph, _scope, decl):
        _, defaults = decl

        graph.defaults = graph.defaults + defaults
        return graph

    def _decl_include(self, graph, scope, decl):
        _, path = decl

        if not self.host.exists(path):
            raise PynException("'%s' not found." % path)

        ast = self.parse(self.host.read(path))
        return self.analyze(ast, filename=None, graph=graph, scope=scope)

    def _decl_pool(self, graph, _scope, decl):
        _, name, pool_vars = decl

        if name in graph.pools:
            raise PynException("pool '%s' already declared" % name)
        if not pool_vars:
            raise PynException("pool '%s' has no depth variable" % name)
        if len(pool_vars) > 1:
            raise PynException("pool '%s' has too many variables" % name)

        _, var_name, var_value = pool_vars[0]
        if var_name != 'depth':
            raise PynException("pool '%s' has a variable named %s, not "
                               "'depth'" % (name, var_name))
        try:
            depth = int(var_value)
        except ValueError:
            raise PynException("pool '%s'\'s depth value, '%s', is not an int"
                               % (name, var_value))

        graph.pools[name] = depth
        return graph

    def _decl_rule(self, graph, scope, decl):
        _, rule_name, rule_vars = decl

        if rule_name in graph.rules:
            raise PynException("'rule %s' declared more than once" % rule_name)

        rule_scope = Scope(rule_name, scope.name)
        self._add_vars_to_scope(rule_vars, rule_scope)
        rule = Rule(rule_name, rule_scope)
        graph.rules[rule_name] = rule
        return graph

    def _decl_subninja(self, graph, _scope, decl):
        _, path = decl
        if not self.host.exists(path):
            raise PynException("'%s' not found." % path)
        ast = self.parse(self.host.read(path))
        subgraph = self.analyze(ast, path)
        for s in list(subgraph.scopes.values()):
            if s.name in graph.scopes:
                raise PynException("scope '%s' declared in multiple files " %
                                   s.name)
            graph.scopes[s.name] = s

        for n in list(subgraph.nodes.values()):
            self._add_outputs_to_graph(n.outputs, n, graph)
        return graph

    def _decl_var(self, graph, scope, decl):
        self._add_vars_to_scope([decl], scope)
        return graph

    def _add_vars_to_scope(self, var_decls, scope):
        for _, name, val in var_decls:
            if name in scope.objs:
                raise PynException("'var %s' declared more than once "
                                   " in %s'" % (name, scope.name))
            scope.objs[name] = val

    def _add_outputs_to_graph(self, outputs, node, graph):
        for output_name in outputs:
            if output_name in graph.nodes:
                raise PynException("build output '%s' declared more than "
                                   "once " % output_name)
            graph.nodes[output_name] = node

    def _add_deps_in_depfiles(self, graph):
        for n in list(graph.nodes.values()):
            depfile_path = self.expand_vars(n.scope['depfile'], n.scope)
            if self.host.exists(depfile_path):
                n.deps.extend(self.host.read(depfile_path).split()[2:])

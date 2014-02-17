from common import Graph, Node, PynException, Rule, Scope


class NinjaAnalyzer(object):
    # "method could be a function" pylint: disable=R0201
    def __init__(self, host, args, parse):
        self.host = host
        self.args = args
        self.parse = parse

    def analyze(self, ast, filename=None, graph=None, scope=None):
        assert filename or (graph and scope)
        graph = graph or Graph()
        scope = scope or Scope(filename, None)
        graph.scopes[filename] = scope
        for decl in ast:
            graph = getattr(self, '_decl_' + decl[0])(graph, scope, decl)

        return graph

    def _decl_build(self, graph, scope, decl):
        _, outputs, rule_name, inputs, deps, build_vars = decl

        if len(outputs) > 1:
            raise PynException("More than one output is not supported yet")
        build_name = outputs[0]
        if build_name in graph.nodes:
            raise PynException("build %' declared more than once")

        build_scope = Scope(build_name, scope)
        build_scope['out'] = ' '.join(outputs)
        build_scope['in'] = ' '.join(inputs)
        for _, name, val in build_vars:
            if name in build_scope.objs:
                raise PynException("'var %s' declared more than once "
                                   " in build %s'" % (name, build_name))
            build_scope.objs[name] = val

        graph.nodes[build_name] = Node(build_name, build_scope, rule_name,
                                       inputs + deps)
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
        if pool_vars[0][0] != 'depth':
            raise PynException("pool '%s' has a variable named %s, not "
                               "'depth'" % (name, pool_vars[0][0]))
        try:
            depth = int(pool_vars[0][1])
        except ValueError:
            raise PynException("pool '%s'\'s depth value, '%s', is not an int"
                               % (name, pool_vars[0][1]))

        graph.pools[name] = depth
        return graph

    def _decl_rule(self, graph, scope, decl):
        _, rule_name, rule_vars = decl

        if rule_name in graph.rules:
            raise PynException("'rule %s' declared more than once" % rule_name)

        rule_scope = Scope(rule_name, scope.name)
        for _, var_name, val in rule_vars:
            if var_name in rule_scope:
                raise PynException("'var %s' declared more than once "
                                   " in rule %s'" % (var_name, rule_name))
            rule_scope[var_name] = val

        rule = Rule(rule_name, rule_scope)
        graph.rules[rule_name] = rule
        return graph

    def _decl_subninja(self, graph, _scope, decl):
        _, path = decl
        if not self.host.exists(path):
            raise PynException("'%s' not found." % path)
        ast = self.parse(self.host.read(path))
        subgraph = self.analyze(ast, path)
        for s in subgraph.scopes:
            if s.name in graph.scopes:
                raise PynException("scope '%s' declared in multiple files " %
                                   s.name)
            graph.scopes[s.name] = s
        for n in subgraph.nodes:
            if n.name in graph.nodes:
                raise PynException("build '%s' declared in multiple files " %
                                   n.name)
            graph.nodes[n.name] = n
        return graph

    def _decl_var(self, graph, scope, decl):
        _, var_name, value = decl

        if var_name in scope:
            raise PynException("'var %s' is declared more than once "
                               "in the same scope" % var_name)

        scope[var_name] = value
        return graph

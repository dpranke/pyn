from common import Graph, Node, PynException, Rule, Scope


class NinjaAnalyzer(object):
    def __init__(self, host, args, parse, expand_vars):
        self.host = host
        self.args = args
        self.parse = parse
        self.expand_vars = expand_vars

    def analyze(self, ast, filename):
        graph = Graph(filename)
        scope = Scope(filename, None)
        graph.scopes[filename] = scope

        graph = self._add_ast(graph, scope, ast)
        graph = self._add_includes(graph)
        graph = self._add_subninjas(graph)
        graph = self._add_deps_in_depfiles(graph)

        return graph

    def _add_ast(self, graph, scope, ast):
        for decl in ast:
            graph = getattr(self, '_decl_' + decl[0])(graph, scope, decl)
        return graph

    def _add_includes(self, graph):
        asts = self._pmap(_read_and_parse, graph.includes)
        for ast in asts:
            graph = self._add_ast(graph, graph.scopes[graph.name], ast)
        return graph

    def _add_subninjas(self, graph):
        subgraphs = self._pmap(_read_and_analyze, graph.subninjas)
        for subgraph, includes, subninjas in subgraphs:
            subgraph = self._add_includes(subgraph)
            subgraph = self._add_subninjas(subgraph)
            graph = self._merge_graphs(graph, subgraph)

        return graph

    def _merge_graphs(self, graph, subgraph):
        for name, rule in subgraph.rules.items():
            if name in graph.rules:
                raise PynException("rule '%s' declared in multiple files " %
                                   name)
            graph.rules[name] = rule
        for name, scope in subgraph.scopes.items():
            if name in graph.scopes:
                raise PynException("scope '%s' declared in multiple files " %
                                   name)
            graph.scopes[name] = scope

        self._add_nodes_to_graph(subgraph.nodes, graph)
        return graph

    def _add_deps_in_depfiles(self, graph):
        for n in list(graph.nodes.values()):
            depfile_path = self.expand_vars(n.scope['depfile'], n.scope)
            if self.host.exists(depfile_path):
                n.deps.extend(self.host.read(depfile_path).split()[2:])
        return graph

    def _add_vars_to_scope(self, var_decls, scope):
        for _, name, val in var_decls:
            if name in scope.objs:
                raise PynException("'var %s' declared more than once "
                                   "in %s'" % (name, scope.name))
            scope.objs[name] = val

    def _add_nodes_to_graph(self, nodes, graph):
        for name, node in nodes.items():
            if name in graph.nodes:
                raise PynException("build output '%s' declared more than "
                                   "once " % name)
            graph.nodes[name] = node

    def _pmap(self, fn, paths):
        for path in paths:
            if not self.host.exists(path):
                raise PynException("'%s' not found." % path)

        return map(fn, [(self, path) for path in paths])

        # FIXME: Using a parallel map seems to just be slower.
        # vs = []
        # tuples = [(self, path) for path in paths]
        # pool = self.host.mp_pool(self.args.jobs)
        # try:
        #    vs = pool.map(fn, tuples)
        #    pool.close()
        #except:
        #    pool.terminate()
        #    raise
        # finally:
        #    pool.join()
        # return vs

    def _decl_build(self, graph, scope, decl):
        _, outputs, rule_name, inputs, ideps, odeps, build_vars = decl

        build_name = ' '.join(outputs)
        build_scope = Scope(build_name, scope)
        build_scope['out'] = ' '.join(outputs)
        build_scope['in'] = ' '.join(inputs)
        self._add_vars_to_scope(build_vars, build_scope)

        n = Node(build_name, build_scope, rule_name, inputs + ideps + odeps)
        self._add_nodes_to_graph({n.name: n}, graph)
        return graph

    def _decl_default(self, graph, _scope, decl):
        _, defaults = decl

        graph.defaults = graph.defaults + defaults
        return graph

    def _decl_include(self, graph, _scope, decl):
        _, path = decl
        graph.includes.add(path)
        return graph

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
        graph.subninjas.add(path)
        return graph

    def _decl_var(self, graph, scope, decl):
        self._add_vars_to_scope([decl], scope)
        return graph


def _read_and_parse(arg_tuple):
    analyzer, path = arg_tuple
    return analyzer.parse(analyzer.host.read(path))


def _read_and_analyze(arg_tuple):
    analyzer, path = arg_tuple
    try:
        ast = analyzer.parse(analyzer.host.read(path))
        graph = Graph(path)
        scope = Scope(path, None)
        graph.scopes[path] = scope
        graph = analyzer._add_ast(graph, scope, ast)
        graph = analyzer._add_deps_in_depfiles(graph)
        return (graph, graph.includes, graph.subninjas)
    except PynException as ex:
        analyzer.host.print_err("failed to parse %s: %s" % (path, str(ex)))
        graph = Graph(path)
        scope = Scope(path, None)
        graph.scopes[path] = scope
        return (graph, set(), set())

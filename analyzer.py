from common import Graph, Node, Rule, PynException


class NinjaAnalyzer(object):
    # "method could be a function" pylint: disable=R0201
    def __init__(self, host, args, parser):
        self.host = host
        self.args = args
        self.parser = parser

    def analyze(self, ast):
        graph = Graph()
        for decl in ast:
            getattr(self, '_decl_' + decl[0])(graph, decl)
        return graph

    def _decl_build(self, graph, decl):
        _, outputs, rule_name, inputs, deps = decl
        if len(outputs) > 1:
            raise PynException("More than one output is not supported yet")
        output = outputs[0]
        if output in graph.nodes:
            raise PynException("build %' declared more than once")

        graph.nodes[output] = Node(output, rule_name, inputs, inputs + deps)

    def _decl_default(self, graph, decl):
        graph.defaults = decl[1]

    def _decl_import(self, _graph, _decl):
        raise PynException("'import' is not supportedyet")

    def _decl_pool(self, _graph, _decl):
        raise PynException("'pool' is not supported yet")

    def _decl_rule(self, graph, decl):
        _, rule_name, rule_vars = decl

        if rule_name in graph.rules:
            raise PynException("'rule %s' declared more than once" % rule_name)

        rule = Rule(rule_name)
        graph.rules[rule_name] = rule
        for _, var_name, val in rule_vars:
            if var_name in rule.rule_vars:
                raise PynException("'var %s' declared more than once "
                                   " in rule %s'" % (var_name, rule_name))
            rule.rule_vars[var_name] = val

    def _decl_subninja(self, _graph, _decl):
        raise PynException("'subninja' is not supported yet")

    def _decl_var(self, graph, decl):
        _, var_name, value = decl
        if var_name in graph.global_vars:
            raise PynException("'var %s' is declared more than once "
                               "at the top level" % var_name)
        graph.global_vars[var_name] = value

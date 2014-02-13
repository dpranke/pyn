from pyn_exceptions import PynException


class _Graph(object):
    def __init__(self):
        self.nodes = {}
        self.rules = {}
        self.global_vars = {}
        self.defaults = {}

    def __repr__(self):
        return 'Graph(nodes=%s, rules=%s, global_vars=%s, defaults=%s)' % (
            self.nodes, self.rules, self.global_vars, self.defaults)


class _Rule(object):
    def __init__(self, name):
        self.name = name
        self.rule_vars = {}

    def __repr__(self):
        return 'Rule(name=%s, rule_vars=%s)' % (self.name, self.rule_vars)


class _Node(object):
    def __init__(self, name, rule_name, inputs, deps):
        self.name = name
        self.rule_name = rule_name
        self.inputs = inputs
        self.deps = deps

    def __repr__(self):
        return 'Node(name=%s, rule_name=%s, inputs=%s, deps=%s)' % (
            self.name, self.rule_name, self.inputs, self.deps)


def analyze_ninja_ast(host, _args, ast, _parser_cb):
    ast_visitors = {
        'build': _decl_build,
        'default': _decl_default,
        'import': _decl_import,
        'pool': _decl_pool,
        'rule': _decl_rule,
        'subninja': _decl_subninja,
        'var': _decl_var,
    }

    graph = _Graph()
    for decl in ast:
        decl_type = decl[0]
        ast_visitors[decl_type](host, graph, decl)

    return graph


def _decl_build(_host, graph, decl):
    _, outputs, rule_name, inputs, deps = decl
    if len(outputs) > 1:
        raise PynException("More than one output is not supported yet")
    output = outputs[0]
    if output in graph.nodes:
        raise PynException("build %' declared more than once")

    graph.nodes[output] = _Node(output, rule_name, inputs, inputs + deps)


def _decl_default(_host, graph, decl):
    graph.defaults = decl[1]


def _decl_import(_host, _graph, _decl):
    raise PynException("'import' is not supportedyet")


def _decl_pool(_host, _graph, _decl):
    raise PynException("'pool' is not supported yet")


def _decl_rule(_host, graph, decl):
    _, rule_name, rule_vars = decl

    if rule_name in graph.rules:
        raise PynException("'rule %s' declared more than once" % rule_name)

    rule = _Rule(rule_name)
    graph.rules[rule_name] = rule
    for _, var_name, val in rule_vars:
        if var_name in rule.rule_vars:
            raise PynException("'var %s' declared more than once "
                               " in rule %s'" % (var_name, rule_name))
        rule.rule_vars[var_name] = val


def _decl_subninja(_host, _graph, _decl):
    raise PynException("'subninja' is not supported yet")


def _decl_var(_host, graph, decl):
    _, var_name, value = decl
    if var_name in graph.global_vars:
        raise PynException("'var %s' is declared more than once "
                           "at the top level" % var_name)
    graph.global_vars[var_name] = value

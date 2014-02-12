#!/usr/bin/env python

import argparse

from host import Host

def _gen_parser():
    import os
    import subprocess
    import sys
    subprocess.check_call([sys.executable, 'pymeta_helper.py', 'ninja.pymeta'],
                          cwd=os.path.dirname(__file__))

_gen_parser()

import ninja_parser


VERSION = '0.1'


class PynException(Exception):
    pass


class Graph(object):
    def __init__(self):
        self.nodes = {}
        self.rules = {}
        self.global_vars = {}
        self.defaults = {}

    def __repr__(self):
        return 'Graph(nodes=%s, rules=%s, global_vars=%s, defaults=%s)' % (
            self.nodes, self.rules, self.global_vars, self.defaults)


class Rule(object):
    def __init__(self, name):
        self.name = name
        self.rule_vars = {}

    def __repr__(self):
        return 'Rule(name=%s, rule_vars=%s)' % (self.name, self.rule_vars)


class Node(object):
    def __init__(self, name, rule_name, inputs, deps):
        self.name = name
        self.rule_name = rule_name
        self.inputs = inputs
        self.deps = deps

    def __repr__(self):
        return 'Node(name=%s, rule_name=%s, inputs=%s, deps=%s)' % (
            self.name, self.rule_name, self.inputs, self.deps)


def main(host, argv=None):
    args = parse_args(host, argv)

    if args.version:
        raise PynException(VERSION)

    if args.debug:
        raise PynException('-d is not supported yet')
    if args.tool:
        raise PynException('-t is not supported yet')
    if args.dry_run:
        raise PynException('-n is not supported yet')

    ast = parse_build_files(host, args)
    graph = compute_graph(host, ast)
    build_graph(host, graph, args)


def parse_build_files(host, args):
    if args.dir:
        if not host.exists(args.dir):
            raise PynException("'%s' does not exist" % args.dir)
        host.chdir(args.dir)

    if not host.exists(args.file):
        raise PynException("'%s' does not exist" % args.file)

    try:
        build_txt = host.read(args.file)
        return ninja_parser.NinjaParser.parse(build_txt)
    except Exception as e:
        raise PynException(str(e))


def compute_graph(host, ast):
    ast_visitors = {
        'build': handle_build,
        'default': handle_default,
        'import': handle_import,
        'pool': handle_pool,
        'rule': handle_rule,
        'subninja': handle_subninja,
        'var': handle_var,
    }

    graph = Graph()
    for decl in ast:
        decl_type = decl[0]
        ast_visitors[decl_type](host, graph, decl)

    return graph

def handle_build(_host, graph, decl):
    _, outputs, rule_name, inputs, deps  = decl
    if len(outputs) > 1:
        raise PynException("More than one output is not supported yet")
    output = outputs[0]
    if output in graph.nodes:
        raise PynException("build %' declared more than once")

    graph.nodes[output] = Node(output, rule_name, inputs, inputs + deps)


def handle_default(_host, graph, decl):
    graph.defaults = decl[1:]


def handle_import(_host, _graph, _decl):
    raise PynException("'import' is not supportedyet")


def handle_pool(_host, _graph, _decl):
    raise PynException("'pool' is not supported yet")


def handle_rule(_host, graph, decl):
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


def handle_subninja(_host, _graph, _decl):
    raise PynException("'subninja' is not supported yet")


def handle_var(_host, graph, decl):
    _, var_name, value = decl
    if var_name in graph.global_vars:
        raise PynException("'var %s' is declared more than once "
                            "at the top level" % var_name)
    graph.global_vars[var_name] = value


def build_graph(host, graph, args):
    sorted_nodes = tsort(graph)
    total_nodes = len(sorted_nodes)
    for cur, name in enumerate(sorted_nodes, start=1):
        if args.verbose:
            host.print_err('[%d/%d] %s' % (cur, total_nodes, name))

def tsort(graph):
    # This performs a topological sort of the nodes in the graph by
    # picking nodes arbitrarily, and then doing depth-first searches
    # across the graph from there. It should run in O(|nodes|) time.
    # See http://en.wikipedia.org/wiki/Topological_sorting and Tarjan (1976).
    #
    # This algorithm diverges a bit from the Wikipedia algorithm by
    # inserting new nodes at the tail of the sorted node list instead of the
    # head, because we want to ultimately do a bottom-up traversal.
    def visit(node, visited_nodes, sorted_nodes, unvisited_nodes):
        if node in visited_nodes:
            raise PynException("'%s' is part of a cycle" % node)

        visited_nodes.add(node)
        for m in graph.nodes[node].deps:
            if m in graph.nodes and m not in sorted_nodes:
                visit(m, visited_nodes, sorted_nodes, unvisited_nodes)
        unvisited_nodes.remove(node)
        sorted_nodes.append(node)

    visited_nodes = set()
    sorted_nodes = []
    unvisited_nodes = graph.nodes.keys()[:]
    while unvisited_nodes:
        visit(unvisited_nodes[0], visited_nodes, sorted_nodes, unvisited_nodes)
    return sorted_nodes


def parse_args(host, argv):
    default_target = 'default'

    parser = argparse.ArgumentParser(prog='pyn')
    parser.usage = '%(prog)s [options] [targets...]'
    parser.description = (
            'if targets are unspecified, builds the \'%s\' '
            'target (see manual)' % default_target)
    parser.add_argument('--version', action='store_true',
        help='print pyn version ("%s")' % VERSION)
    parser.add_argument('-C', metavar='DIR', dest='dir',
        help='change to DIR before doing anything else')
    parser.add_argument('-f', metavar='FILE', dest='file',
        default='build.ninja',
        help='specify input build file [default=%(default)s]')
    parser.add_argument('-j', metavar='N', type=int, dest='jobs',
        default=host.cpu_count(),
        help=('run N jobs in parallel [default=%(default)s, '
              'derived from CPUs available]'))
    parser.add_argument('-l', metavar='N', type=float,
        help='do not start new jobs if the load average is greater than N')
    parser.add_argument('-k', metavar='N', type=int, dest='errors', default=1,
        help='keep going until N jobs fail [default=default]')
    parser.add_argument('-n', action='store_true', dest='dry_run',
        help='dry run (don\'t run commands but act like they succeeded)')
    parser.add_argument('-v', action='store_true', dest='verbose',
        help='show all command lines while building')
    parser.add_argument('-d', metavar='MODE', dest='debug',
        help='enable debugging (use -d list to list modes)')
    parser.add_argument('-t', metavar='TOOL', dest='tool',
        help='run a subtool (use -t list to list subtools)')
    parser.add_argument('targets', nargs='*', default=[default_target],
        help=argparse.SUPPRESS)
    return parser.parse_args(args=argv)


if __name__ == '__main__':
    main(Host())

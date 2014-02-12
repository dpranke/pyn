#!/usr/bin/env python

from __future__ import print_function

import argparse
import multiprocessing
import os
import pprint
import sys

def _gen_parser():
    import subprocess
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


def main(argv=None, stdout=None, stderr=None):
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    args = parse_args(argv)

    if args.version:
        raise PynException(VERSION)

    if args.debug:
        raise PynException('-d is not supported yet')
    if args.tool:
        raise PynException('-t is not supported yet')
    if args.dry_run:
        raise PynException('-n is not supported yet')

    ast = parse_build_files(args)
    graph = compute_graph(ast)
    build(graph, args, stderr)


def parse_build_files(args):
    if args.dir:
        if not os.path.exists(args.dir):
            raise PynException("'%s' does not exist" % args.dir)
        os.chdir(args.dir)

    if not os.path.exists(args.file):
        raise PynException("'%s' does not exist" % args.file)

    try:
        with open(args.file) as f:
            build_txt = f.read()

        return ninja_parser.NinjaParser.parse(build_txt)
    except Exception as e:
        raise PynException(str(e))

def compute_graph(ast):
    graph = Graph()

    for decl in ast:
        decl_type = decl[0]

        if decl_type == 'subninja':
            raise PynException("'subninja' is not supported yet")

        if decl_type == 'import':
            raise PynException("'import' is not supported yet")

        if decl_type == 'pool':
            raise PynException("'pool' is not supported yet")

        if decl_type == 'rule':
            _, rule_name, rule_vars = decl

            if rule_name in graph.rules:
                raise PynException("'rule %s' declared more than once" %
                                   name)

            rule = Rule(rule_name)
            graph.rules[rule_name] = rule
            for _, var_name, val in rule_vars:
                if var_name in rule.rule_vars:
                    raise PynException("'var %s' declared more than once "
                                       " in rule %s'" % (var_name, rule_name))
                rule.rule_vars[var_name] = val
            continue

        if decl_type == 'build':
            _, outputs, rule_name, inputs, deps  = decl
            if len(outputs) > 1:
                raise PynException("More than one output is not supported yet")
            output = outputs[0]
            if output in graph.nodes:
                raise PynException("build %' declared more than once")

            graph.nodes[output] = Node(output, rule_name, inputs, inputs + deps)
            continue

        if decl_type == 'var':
            _, var_name, value = decl
            if var_name in graph.global_vars:
                raise PynException("'var %s' is declared more than once "
                                   "at the top level" % var_name)
            continue

        if decl_type == 'default':
            graph.defaults = decl[1:]
            continue

        raise PynException("unknown decl type: %s" % decl_type)

    return graph


def build(graph, _args, stderr):
    sorted_nodes = tsort(graph)
    max = len(sorted_nodes)
    for cur, name in enumerate(sorted_nodes, start=1):
        print('[%d/%d] %s' % (cur, max, name), file=stderr)


def tsort(graph):
    def visit(n, visited_nodes, sorted_nodes, unvisited_nodes):
        if n in visited_nodes and n not in sorted_nodes:
            raise PynException("'%s' is part of a cycle" % n)
        if n not in visited_nodes and n not in sorted_nodes:
            visited_nodes.add(n)
            for m in graph.nodes[n].deps:
                if m in graph.nodes:
                    visit(m, visited_nodes, sorted_nodes, unvisited_nodes)
            unvisited_nodes.remove(n)
            sorted_nodes.append(n)

    visited_nodes = set()
    sorted_nodes = []
    unvisited_nodes = graph.nodes.keys()[:]
    while unvisited_nodes:
        visit(unvisited_nodes[0], visited_nodes, sorted_nodes, unvisited_nodes)
    return sorted_nodes


def parse_args(argv):
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
        default=multiprocessing.cpu_count(),
        help=('run N jobs in parallel [default=%(default)s, '
              'derived from CPUs available]'))
    parser.add_argument('-l', metavar='N', type=float,
        help='do not start new jobs if the load average is greater than N')
    parser.add_argument('-k', metavar='N', type=int, dest='errors', default=1,
        help='keep going until N jobs fail [default=default]')
    parser.add_argument('-n', action='store_true', dest='dry_run',
        help='dry run (don\'t run commands but act like they succeeded)')
    parser.add_argument('-v', action='store_true',
        help='show all command lines while building')
    parser.add_argument('-d', metavar='MODE', dest='debug',
        help='enable debugging (use -d list to list modes)')
    parser.add_argument('-t', metavar='TOOL', dest='tool',
        help='run a subtool (use -t list to list subtools)')
    parser.add_argument('targets', nargs='*', default=[default_target],
        help=argparse.SUPPRESS)
    return parser.parse_args(args=argv)


if __name__ == '__main__':
    main()

#!/usr/bin/env python

from __future__ import print_function

import argparse
import multiprocessing
import os
import pprint
import sys


import pymeta_helper

VERSION = '0.1'

def main(argv=None, stdout=None, stderr=None):
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    args = parse_args(argv)

    if args.version:
        print(VERSION, file=stdout)
        return 1

    graph, err = parse_build_files(args)
    if not graph or err:
        print(err, file=stderr)
        return 1

    if args.debug:
        print('-d is not supported yet', file=stderr)
        return 1
    if args.tool:
        print('-t is not supported yet', file=stderr)
        return 1
    if args.dry_run:
        print('-n is not supported yet', file=stderr)
        return 1

    return build_graph(graph, args, stderr)


def parse_build_files(args):
    if args.dir:
        if not os.path.exists(args.dir):
            return None, "Error: '%s' does not exist" % args.dir
        os.chdir(args.dir)

    if not os.path.exists(args.file):
        return None, "Error: '%s' does not exist" % args.file

    try:
        with open(args.file) as f:
            build_txt = f.read()

        n = NinjaParser()
        return n.parse(build_txt), None
    except Exception as e:
        return None, 'Error: %s' % str(e)


def build_graph(graph, _args, stderr):
    pprint.pprint(graph, stream=stderr)


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


ParseError = pymeta_helper.ParseError  # pylint: disable=C0103


class NinjaParser(pymeta_helper.ParserBase):
    name = "pyn"

    grammar = """

grammar    = decls:ds end -> ds

decls      = (ws|'\n')* decl:d  decls:ds -> [d] + ds
           | (ws|'\n')* decl:d           -> [d]
           | (ws|'\n')*                 -> []

decl       = rule | build | var | default | subninja | import | pool

rule       = "rule" ws ident:n eol indented_var+:vs -> ['rule', n, vs]

build      = "build" ws paths:os ws ":" ws ident:rule ws paths:ins deps:ds eol
           -> ['build', os, rule, ins, ds]

deps       = "|" targets:ts -> ts
           | -> []

var        = ident:n ws "=" spaces (~eol anything)+:v eol
           -> ['var', n, ''.join(v)]

default    = "default" ws targets:ts -> ['default', ts]

subninja   = "subninja" ws path:p    -> ['subninja', p]

import     = "include" ws path:p     -> ['import', p]

pool       = "pool" ws ident:name eol indented_var+:vars -> ['pool', name, vars]

indented_var = ws var:v              -> v

targets    = ident:i ws targets:ts   -> [i] + ts
           | ident:i                 -> [i]

ident      = (letter|'_'|'$'|'.'):hd (letter|'.'|'_')*:tl -> ''.join([hd] + tl)

paths      = path:p ws paths:ps -> [p] + ps
           | path:p -> [p]

path       = '"' (~('"'|'\n') anything)+:p '"' -> ''.join(p)
           | (~(' '|':'|'='|eol) anything)+:p -> ''.join(p)

eol        = comment
           | ' '* ~('$' '\n') '\n'

comment    = "#" (~'\n' anything)* '\n'

ws         = (' '|('$' '\n'))+

"""

if __name__ == '__main__':
    main()

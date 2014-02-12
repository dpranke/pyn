#!/usr/bin/env python

from __future__ import print_function

import multiprocessing
import argparse
import sys

import pymeta_helper

VERSION = '0.1'

def main(argv=None, stdout=None, stderr=None):
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    args = parse_args(argv)

    if args.version:
        print(VERSION, file=stdout)
        sys.exit(1)

    if args.dir:
        if not os.path.exists(args.dir):
            print("Error: '%s' does not exist" % args.dir, file=stderr)
            sys.exit(1)
        os.chdir(options.dir)

    sys.exit(run(args, stdout, stderr))


def run(args, stdout, stderr):
    n = NinjaParser()
    try:
        ast = n.parse(sample1)
        print(ast, file=stdout)
    except Exception as e:
        print(e, file=stderr)


ParseError = pymeta_helper.ParseError

def parse_args(argv):
    DEFAULT_TARGET = 'default'

    parser = argparse.ArgumentParser()
    parser.usage = 'pyn [options] [targets...]'
    parser.description = (
            'if targets are unspecified, builds the \'%s\' '
            'target (see manual)' % DEFAULT_TARGET)
    parser.add_argument('--version', action='store_true',
        help='print pyn version ("%s")' % VERSION)
    parser.add_argument('-C', metavar='DIR', dest='dir',
        help='change to DIR before doing anything else')
    parser.add_argument('-f', metavar='FILE', default='build.ninja',
        help='specify input build file [default=%(default)s]')
    parser.add_argument('-j', default=multiprocessing.cpu_count(), metavar='N',
        help=('run N jobs in parallel [default=%(default)s, '
              'derived from CPUs available]'))
    parser.add_argument('-l', metavar='N',
        help='do not start new jobs if the load average is greater than N')
    parser.add_argument('-k', metavar='N', default=1,
        help='keep going until N jobs fail [default=default]')
    parser.add_argument('-n', action='store_true',
        help='dry run (don\'t run commands but act like they succeeded)')
    parser.add_argument('-v', action='store_true',
        help='show all command lines while building')
    parser.add_argument('-d', metavar='MODE',
        help='enable debugging (use -d list to list modes)')
    parser.add_argument('-t', metavar='TOOL',
        help='run a subtool (use -t list to list subtools)')
    parser.add_argument('targets', nargs='*', default=[DEFAULT_TARGET])
    return parser.parse_args()


class NinjaParser(pymeta_helper.ParserBase):
    name = "pyn"

    grammar = """

grammar    = decls:ds end -> ds

decls      = ws_or_comments decl:d  decls:ds -> [d] + ds
           | ws_or_comments decl:d           -> [d]
           | ws_or_comments                  -> []

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

ident      = (letter|'_'|'$'):hd (letter)*:tl -> ''.join([hd] + tl)

paths      = path:p ws paths:ps -> [p] + ps
           | path:p -> [p]

path       = '"' (~('"'|'\n') anything)+:p '"' -> ''.join(p)
           | (~(' '|':'|'='|eol) anything)+:p -> ''.join(p)

eol        = comment
           | ' '* ~('$' '\n') '\n'

comment    = "#" (~'\n' anything)* '\n'

ws         = ' '+

ws_or_comments = (' '|('$' '\n')|'\n'|comment)*

"""

if __name__ == '__main__':
    main()

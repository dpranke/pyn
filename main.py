#!/usr/bin/env python
import argparse
import sys
import textwrap

from analyzer import NinjaAnalyzer
from builder import Builder
from common import PynException, PynExit
from host import Host
from ninja_parser import parse, expand_vars


VERSION = '0.4a'


def main(host, argv=None):
    args = parse_args(host, argv)
    if args.version:
        raise PynExit(VERSION)
    if args.debug:
        raise PynException('-d is not supported yet')
    if args.dir:
        if not host.exists(args.dir):
            raise PynException("'%s' does not exist" % args.dir)
        host.chdir(args.dir)
    if not host.exists(args.file):
        raise PynException("'%s' does not exist" % args.file)

    ast = parse(host.read(args.file))
    analyzer = NinjaAnalyzer(host, args, parse, expand_vars)
    graph = analyzer.analyze(ast, args.file)
    if args.tool == 'check':
        raise PynExit("pyn: syntax is correct")
    builder = Builder(host, args, expand_vars)
    if args.tool:
        if args.tool == 'list':
            raise PynExit(textwrap.dedent('''\
                pyn subtools:
                  clean     clean built files
                  check     check the syntax and semantics of
                            the build file (and all included files)
                  question  check to see if the build is up-to-date'''))
        elif args.tool == 'clean':
            builder.clean(graph)
        elif args.tool == 'question':
            builder.build(graph, question=True)
        else:
            raise PynException("Unsupported tool '%s'" % args.tool)
    else:
        builder.build(graph)


def parse_args(host, argv):
    ap = argparse.ArgumentParser(prog='pyn')
    ap.usage = '%(prog)s [options] [targets...]'
    ap.description = ("if targets are unspecified, builds the 'default' "
                      "targets (see manual).")
    ap.add_argument('--version', action='store_true',
                    help='print pyn version ("%s")' % VERSION)
    ap.add_argument('-C', metavar='DIR', dest='dir',
                    help='change to DIR before doing anything else')
    ap.add_argument('-f', metavar='FILE', dest='file', default='build.ninja',
                    help='specify input build file [default=%(default)s]')
    ap.add_argument('-j', metavar='N', type=int, dest='jobs',
                    default=host.cpu_count(),
                    help=('run N jobs in parallel [default=%(default)s, '
                          'derived from CPUs available]'))
    ap.add_argument('-l', metavar='N', type=float,
                    help=('do not start new jobs if the load average '
                          'is greater than N'))
    ap.add_argument('-k', metavar='N', type=int, dest='errors', default=1,
                    help='keep going until N jobs fail [default=default]')
    ap.add_argument('-n', action='store_true', dest='dry_run',
                    help=('dry run (don\'t run commands but act like they '
                          'succeeded)'))
    ap.add_argument('-v', action='count', dest='verbose',
                    help='show all command lines while building')
    ap.add_argument('-d', metavar='MODE', dest='debug',
                    help='enable debugging (use -d list to list modes)')
    ap.add_argument('-t', metavar='TOOL', dest='tool',
                    help='run a subtool (use -t list to list subtools)')
    ap.add_argument('targets', nargs='*', default=[],
                    help=argparse.SUPPRESS)
    return ap.parse_args(args=argv)


def _real_main():
    h = Host()
    code = 0
    try:
        main(h)
    except PynExit as e:
        h.print_out(e.message)
    except PynException as e:
        h.print_err('Error: ' + str(e))
        code = 1
    return code

if __name__ == '__main__':
    sys.exit(_real_main())

#!/usr/bin/env python

import argparse

import analyzer
import builder
import parsers

from pyn_exceptions import PynException
from host import Host


VERSION = '0.1'


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

    if args.dir:
        if not host.exists(args.dir):
            raise PynException("'%s' does not exist" % args.dir)
        host.chdir(args.dir)

    ast = parsers.parse_ninja_file(host, args.file)
    graph = analyzer.analyze_ninja_ast(host, args, ast,
                                       parsers.parse_ninja_file)
    builder.build(host, args, graph)


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
        help='do not start new jobs if the load average is greater than N')
    ap.add_argument('-k', metavar='N', type=int, dest='errors', default=1,
        help='keep going until N jobs fail [default=default]')
    ap.add_argument('-n', action='store_true', dest='dry_run',
        help='dry run (don\'t run commands but act like they succeeded)')
    ap.add_argument('-v', action='store_true', dest='verbose',
        help='show all command lines while building')
    ap.add_argument('-d', metavar='MODE', dest='debug',
        help='enable debugging (use -d list to list modes)')
    ap.add_argument('-t', metavar='TOOL', dest='tool',
        help='run a subtool (use -t list to list subtools)')
    ap.add_argument('targets', nargs='*', default=[],
        help=argparse.SUPPRESS)
    return ap.parse_args(args=argv)


if __name__ == '__main__':
    h = Host() # pylint: disable=C0103
    try:
        main(h)
    except PynException as e:
        s = str(e)
        if s == VERSION:
            h.print_err(s)
        else:
            h.print_err('Error: ' + s)
        h.exit(1)

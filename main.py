#!/usr/bin/env python
import argparse
import sys

import pymeta_helper

from analyzer import NinjaAnalyzer
from builder import Builder
from common import PynException, PynExit
from host import Host


VERSION = '0.3'


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

    d = host.dirname(host.path_to_module(__name__))
    parser = pymeta_helper.make_parser(host.join(d, 'ninja.pymeta'))
    ast = parser.parse(host.read(args.file))

    analyzer = NinjaAnalyzer(host, args, parser)

    graph = analyzer.analyze(ast, args.file)

    builder = Builder(host, args)
    if args.tool:
        if args.tool == 'list':
            raise PynExit("pyn subtools:\n"
                          "  clean  clean built files")
        elif args.tool == 'clean':
            builder.clean(graph)
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


if __name__ == '__main__':
    # pylint: disable=C0103
    h = Host()
    code = 0
    try:
        main(h)
    except PynExit as e:
        h.print_out(e)
    except PynException as e:
        h.print_err('Error: ' + str(e))
        code = 1
    sys.exit(code)

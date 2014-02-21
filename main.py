import argparse
import sys
import textwrap

from analyzer import NinjaAnalyzer
from builder import Builder
from common import PynException
from host import Host
from ninja_parser import parse, expand_vars


VERSION = '0.4a'


def main(host, argv=None):
    returncode, args = parse_args(host, argv)
    if returncode is not None:
        return returncode
    if args.version:
        host.print_out(VERSION)
        return 0
    if args.debug:
        host.print_err('-d is not supported yet')
        return 2
    if args.tool and args.tool not in ('check', 'clean', 'list', 'question'):
        host.print_err('unsupported tool "%s"' % args.tool)
        return 2
    if args.tool == 'list':
        host.print_out(textwrap.dedent('''\
            pyn subtools:
            clean     clean built files
            check     check the syntax and semantics of the build file
                      (and all included files)
            question  check to see if the build is up-to-date
            '''))
        return 0
    if args.dir:
        if not host.exists(args.dir):
            host.print_err('"%s" not found' % args.dir)
            return 2
        host.chdir(args.dir)
    if not host.exists(args.file):
        host.print_err('"%s" not found' % args.file)
        return 2

    try:
        ast = parse(host.read(args.file))

        analyzer = NinjaAnalyzer(host, args, parse, expand_vars)
        graph = analyzer.analyze(ast, args.file)
        if args.tool == 'check':
            host.print_out('pyn: syntax is correct')
            return 0

        builder = Builder(host, args, expand_vars)

        if args.tool == 'clean':
            builder.clean(graph)
        elif args.tool == 'question':
            builder.build(graph, question=True)
        else:
            builder.build(graph)
        return 0

    except PynException as e:
        host.print_err(str(e))
        return 1


def parse_args(host, argv):

    class ReturningArgParser(argparse.ArgumentParser):
        returncode = None

        # 'Redefining built-in "file" pylint: disable=W0622
        def print_help(self, file=None):
            super(ReturningArgParser, self).print_help(file or host.stdout)

        def error(self, message):
            self.exit(2, message)

        def exit(self, status=0, message=None):
            self.returncode = status
            if message:
                host.print_err(message)

    ap = ReturningArgParser(prog='pyn')
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
    args = ap.parse_args(args=argv)
    return ap.returncode, args


if __name__ == '__main__':
    sys.exit(main(Host()))

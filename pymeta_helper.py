#/usr/bin/python

from __future__ import print_function

import argparse
import importlib
import os
import sys


class ParseError(Exception):
    pass


class ParserBase(object):
    name = None
    grammar = None

    def __init__(self, name=None, grammar=None,
                 src_dir=None, filename=None,
                 classname=None):
        self.grammar = grammar or self.grammar
        self.name = name or self.name
        self.src_dir = src_dir or os.path.dirname(os.path.abspath(__file__))
        self.filename = filename or self.name.lower() + '_parser.py'
        self.classname = classname or self.name.capitalize() + 'Parser'
        self.grammar_constant_name = self.name.upper() + '_GRAMMAR'

        assert self.name
        assert self.grammar

        if self.generated_grammar() != self.grammar:
            self.generate_parser_module()

        self._module = importlib.import_module(self.filename.replace('.py', ''))
        self._cls = getattr(self._module, self.classname)

        # pylint: disable=W0212
        self._parse_error = self._module._MaybeParseError

    def parse(self, txt):
        try:
            return self._cls.parse(txt)
        except self._module.ParseError as e:
            raise ParseError(str(e))

    def generated_grammar(self):
        if not os.path.exists(self.filename):
            return None

        with open(self.filename) as fp:
            lines = fp.readlines()
            start = lines.index('%s = """\n' % self.grammar_constant_name)
            end = lines[start:].index('"""\n')
            txt = '\n' + ''.join(lines[start+1:start + end])
            return txt

    def generate_parser_module(self):
        from pymeta.grammar import OMetaGrammar
        from pymeta import builder

        tree = OMetaGrammar(self.grammar).parseGrammar(self.classname,
                                                       builder.TreeBuilder)
        with open(os.path.join(self.src_dir, 'pymeta', 'runtime.py')) as fp:
            runtime_str = fp.read()
        with open(os.path.join(self.src_dir, self.filename), 'w') as fp:
            fp.write('# %s: disable=C0103,C0301,C0302,R0201,R0903\n\n' %
                     'pylint')
            fp.write(runtime_str)
            fp.write('\n\n')
            fp.write('%s = """\n%s\n"""\n\n' % (self.grammar_constant_name,
                                            self.grammar))
            fp.write('GrammarBase = OMetaBase\n')
            fp.write('\n\n')

            parser_cls_code = builder.writePython(tree)
            fp.write(parser_cls_code)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pymeta_helper')
    parser.usage = '[options] grammar'
    parser.add_argument('grammar', nargs=1,
        help=argparse.SUPPRESS)
    parser.add_argument('-o', metavar='FILE', dest='output',
        help='destination file (defaults to s/grammar.pymeta/grammar.py)')
    parser.add_argument('-n', '--name',
        help='base name of grammar')
    args = parser.parse_args(args=argv)

    filename = args.grammar[0]
    if not os.path.exists(filename):
        print("Error: '%s' not found", file=sys.stderr)
        sys.exit(1)

    with open(filename) as f:
        grammar = f.read()

    basename = os.path.basename(args.grammar[0]).replace('.pymeta', '')
    name = args.name or basename.capitalize()

    ParserBase(grammar=grammar, name=name)

if __name__ == '__main__':
    main()

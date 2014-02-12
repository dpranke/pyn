import importlib
import os


class ParseError(Exception):
    pass


class ParserBase(object):
    name = None
    grammar = None

    def __init__(self):
        assert self.name
        assert self.grammar

        self.src_dir = os.path.dirname(os.path.abspath(__file__))
        self.filename = self.name.lower() + '_parser.py'
        self.classname = self.name.capitalize() + 'Parser'
        self.grammar_constant_name = self.name.upper() + '_GRAMMAR'

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
            fp.write('%s = """%s"""\n\n' % (self.grammar_constant_name,
                                            self.grammar))
            fp.write('GrammarBase = OMetaBase\n')
            fp.write('\n\n')

            parser_cls_code = builder.writePython(tree)
            fp.write(parser_cls_code)

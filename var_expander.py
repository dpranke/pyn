import textwrap

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError, _MaybeParseError

from common import PynException


VarParser = OMeta.makeGrammar("""

grammar = chunk*:cs end         -> ''.join(cs)

chunk   = ~'$' anything:c       -> c
        | '$' (' '|':'|'$'):c   -> c
        | '$' '{' varname:v '}' -> lookup(v)
        | '$' varname:v         -> lookup(v)

varname = (letter|'_')+:ls      -> ''.join(ls)

""", {'lookup': None})


def expand_vars(msg, scope, rule_scope=None):

    def lookup(v):
        if var in self.scope.objs:
            return self.scope.objs[var]
        if self.rule_scope and var in self.rule_scope.objs:
            return self.rule_scope.objs[var]
        if self.scope.parent:
            return self.scope.parent[var]
        return ''

    parser = VarParser(msg)
    parser.globals['lookup'] = lookup
    try:
        return parser.apply('grammar')[0]
    except _MaybeParseError as e:
        raise PynException(str(e))

import textwrap

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError, _MaybeParseError

from common import PynException


_OMetaNinjaParser = OMeta.makeGrammar("""
grammar  = (empty_line* decl)*:ds empty_line* end      -> ds

decl     = build | rule | var | subninja | include
         | pool | default

build    = "build" ws paths:os ws? ':' ws name:rule
            explicit_deps:eds implicit_deps:ids order_only_deps:ods eol
            (ws var)*:vs                               -> ['build', os, rule,
                                                           eds, ids, ods, vs]

rule     = "rule" ws name:n eol (ws var)*:vs           -> ['rule', n, vs]

var      = name:n ws? '=' ws? value:v eol              -> ['var', n, v]

value    = (~eol (('$' '\n' ' '+ -> '')|anything))*:vs -> ''.join(vs)

subninja = "subninja" ws path:p                        -> ['subninja', p]

include  = "include" ws path:p                         -> ['include', p]

pool     = "pool" ws name:n eol (ws var)*:vars         -> ['pool', n, vars]

default  = "default" ws paths:ps eol                   -> ['default', ps]

paths    = path:hd (ws path)*:tl                       -> [hd] + tl

path     = (('$' ' ')|(~(' '|':'|'='|'|'|eol) anything))+:p -> ''.join(p)

name     = letter:hd (letter|digit|'_')*:tl            -> ''.join([hd] + tl)

explicit_deps = ws? paths:ps                           -> ps
         |                                             -> []

implicit_deps = ws? '|' ws? paths:ps                   -> ps
         |                                             -> []

order_only_deps = ws? "||" ws? paths:ps                -> ps
         |                                             -> []

empty_line = ws? (comment | '\n')

eol      = ws? (comment | '\n' | end)

ws       = (' '|('$' '\n'))+

comment  = '#' (~'\n' anything)* ('\n'|end)
""", {})


class NinjaParser(object):
    """Parse the contents of a .ninja file and return an AST."""

    def parse(self, msg):
        v, p, err = self.apply('grammar', msg, 0, len(msg))
        if err:
            raise PynException(err)
        else:
            return v

    def grammar_(self, msg, start, end):
        pass

    def apply(self, rule, msg, start, end):
        p = _OMetaNinjaParser(msg[start:end])
        try:
            return (p.apply(rule)[0], p.input.position, None)
        except _MaybeParseError as ex:
            return (None, p.input.position, PynException(str(ex)))

def parse(msg):
    return NinjaParser().parse(msg)


def expand_vars(msg, scope):
    return VarExpander(scope).parse(msg)


class VarExpander(object):
    """Expand the variables in a string.

    grammar = chunk*:cs end         -> ''.join(cs)
    chunk   = ~'$' anything:c       -> c
            | '$' (' '|':'|'$'):c   -> c
            | '$' '{' varname:v '}' -> scope[v]
            | '$' varname:v         -> scope[v]
    varname = (letter|'_')+:ls      -> ''.join(ls)
    """

    def __init__(self, scope):
        self.scope = scope

    def parse(self, msg):
        v, p, err = self.grammar_(msg, 0, len(msg))
        if err:
            raise PynException("%s at %d" % (err, p))
        else:
            return v

    def grammar_(self, msg, start, end):
        vs = []
        v, p, err = self.chunk_(msg, start, end)
        while v:
            vs.append(v)
            v, p, err = self.chunk_(msg, p, end)
        if err:
            return (None, p, err)
        return (''.join(vs), p, err)

    def chunk_(self, msg, start, end):
        if end - start > 0 and msg[start] == '$':
            if end - start == 1:
                return (None, start + 1, "expecting a varname or a '{'")
            elif msg[start + 1] in (' ', ':', '$'):
                return (msg[start + 1], start + 2, None)
            elif msg[start + 1] == '{':
                v, p, err = self.varname_(msg, start + 2, end)
                if err:
                    return (None, p, err)
                elif p > end - 1:
                    return (None, p, "expecting a closing }")
                elif msg[p] == '}':
                    return (self.scope[v], p + 1, None)
                else:
                    return (None, p, "expecting a closing }")
            else:
                v, p, err = self.varname_(msg, start + 1, end)
                if err:
                    return (None, p, err)
                else:
                    return (self.scope[v], p, None)
        elif end - start > 0:
            return msg[start], start + 1, None
        else:
            return None, start, None

    def varname_(self, msg, start, end):
        vs = []
        p = start
        while p < end and (msg[p].isalpha() or msg[p] == '_'):
            vs.append(msg[p])
            p += 1
        if p > start:
            return ''.join(vs), p, None
        return None, start, "expecting a varname"



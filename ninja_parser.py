import textwrap

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError, _MaybeParseError

from common import PynException


NinjaParser = OMeta.makeGrammar("""
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


def parse(msg):
    try:
        return NinjaParser.parse(msg)
    except ParseError as e:
        raise PynException(str(e))


VarParser = OMeta.makeGrammar(textwrap.dedent("""
            grammar = chunk*:cs end         -> ''.join(cs)
            chunk   = ~'$' anything:c       -> c
                    | '$' (' '|':'|'$'):c   -> c
                    | '$' '{' varname:v '}' -> scope[v]
                    | '$' varname:v         -> scope[v]
            varname = (letter|'_')+:ls      -> ''.join(ls)
            """), {'scope': None})


def expand_vars(msg, scope):
    def chunk(msg):
        if msg and msg[0] == '$':
            if len(msg) == 1:
                return (None, 1, "expecting a varname or a '{'")
            elif msg[1] in (' ', ':', '$'):
                return (msg[1], 2, None)
            elif msg[1] == '{':
                v, p, err = varname(msg[2:])
                if err:
                    return (None, p, err)
                elif len(msg) < p + 3:
                    return (None, p + 1, "expecting a closing }")
                elif msg[p + 2] == '}':
                    return (scope[v], p + 3, None)
                else:
                    return (None, p + 2, "expecting a closing }")
            else:
                v, p, err = varname(msg[1:])
                if err:
                    return (None, p, err)
                else:
                    return (scope[v], p + 1, None)
        else:
            if msg:
                return msg[0], 1, None
            else:
                return None, 0, None

    def varname(msg):
        p = 0
        while p < len(msg) and (msg[p].isalpha() or msg[p] == '_'):
            p += 1
        if p:
            return msg[0:p], p, None
        return None, 0, "expecting a varname"

    vs = []
    v, p, err = chunk(msg)
    while v:
        vs.append(v)
        msg = msg[p:]
        v, p, err = chunk(msg)
    if err:
        raise PynException("%s at %d" % (err, p))
    else:
        return ''.join(vs)


    try:
        parser = VarParser(msg)
        parser.globals['scope'] = scope
        return parser.apply('grammar')[0]
    except _MaybeParseError as e:
        raise PynException(e.message)

import textwrap

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError

from common import PynException


NinjaParser = OMeta.makeGrammar("""
grammar  = (empty_line* decl)*:ds empty_line* end      -> ds

decl     = build | rule | var | subninja | include
         | pool | default

build    = "build" ws paths:os ws? ':' ws name:rule
           ws paths:ins deps:ds eol (ws var)*:vs       -> ['build', os, rule,
                                                           ins, ds, vs]

rule     = "rule" ws name:n eol (ws var)*:vs           -> ['rule', n, vs]

var      = name:n ws? '=' ws? value:v eol              -> ['var', n, v]

value    = (~eol (('$' '\n' ' '+ -> '')|anything))*:vs -> ''.join(vs)

subninja = "subninja" ws path:p                        -> ['subninja', p]

include  = "include" ws path:p                         -> ['include', p]

pool     = "pool" ws name:n eol (ws var)*:vars         -> ['pool', n, vars]

default  = "default" ws paths:ps eol                   -> ['default', ps]

paths    = path:hd (ws path)*:tl                       -> [hd] + tl

path     = (~(' '|':'|'='|'|'|eol) anything)+:p        -> ''.join(p)

name     = (letter|'_')*:ls                            -> ''.join(ls)

deps     = ws? '|' ws? paths:ps                        -> ps
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


def expand_vars(msg, scope):
    try:
        return OMeta.makeGrammar(textwrap.dedent("""
            grammar = chunk*:cs end         -> ''.join(cs)
            chunk   = ~'$' anything:c       -> c
                    | '$' (' '|':'|'$'):c   -> c
                    | '$' '{' varname:v '}' -> scope[v]
                    | '$' varname:v         -> scope[v]
            varname = (letter|'_')+:ls      -> ''.join(ls)
            """), {'scope': scope}).parse(msg)
    except ParseError as e:
        raise PynException(e.message)

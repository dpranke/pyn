import textwrap

from pymeta.grammar import OMeta
from pymeta.runtime import ParseError, _MaybeParseError

from common import PynException


NinjaParser = OMeta.makeGrammar("""
grammar  = (empty_line* decl)*:ds empty_line* end      -> ds

decl     = build | rule | subninja | include
         | pool | default | var

build    = "build" ws paths:os ws? ':' ws name:rule
            explicit_deps:eds implicit_deps:ids
            order_only_deps:ods eol
            ws_vars:vs                                 -> ['build', os, rule,
                                                           eds, ids, ods, vs]

rule     = "rule" ws name:n eol ws_vars:vs             -> ['rule', n, vs]

subninja = "subninja" ws path:p eol                    -> ['subninja', p]

include  = "include" ws path:p eol                     -> ['include', p]

pool     = "pool" ws name:n eol ws_vars:vars           -> ['pool', n, vars]

default  = "default" ws paths:ps eol                   -> ['default', ps]

ws_vars  = (ws var)*:vs                                -> vs

var      = name:n ws? '=' ws? value:v eol              -> ['var', n, v]

value    = (~eol value_ch)*:vs                         -> ''.join(vs)

value_ch = '$' ' '                                     -> ' '
         | '$' '\n' ' '+                               -> ''
         | ~eol anything:ch                            -> ch

paths    = path:hd (ws path)*:tl                       -> [hd] + tl

path     = path_ch+:p                                  -> ''.join(p)

path_ch  = '$' ' '                                     -> ' '
         | ~(' ' | ':' | '=' | '|' | eol) anything:ch  -> ch

name     = (letter|'_'):hd (letter|digit|'_')*:tl      -> ''.join([hd] + tl)

explicit_deps   = ws? paths:ps                         -> ps
                |                                      -> []

implicit_deps   = ws? '|' ws? paths:ps                 -> ps
                |                                      -> []

order_only_deps = ws? '|' '|' ws? paths:ps             -> ps
                |                                      -> []

empty_line      = ws? comment? ('\n' | end)

eol             = ws? ('\n' | end)

ws              = (' '|('$' '\n'))+

comment         = '#' (~'\n' anything)* ('\n'|end)
""", {})


def parse(msg, fname=''):
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
    try:
        parser = VarParser(msg)
        parser.globals['scope'] = scope
        return parser.apply('grammar')[0]
    except _MaybeParseError as e:
        raise PynException(e.message)

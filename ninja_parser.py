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
        v, p, err = self.grammar_(msg, 0, len(msg))
        if err:
            raise PynException(err)
        else:
            return v

    def grammar_(self, msg, start, end):
        """ (empty_line* decl)*:ds empty_line* end -> ds """
        ds = []
        err = None
        p = start
        while not err and p < end:
            while not err and p < end:
                _, p, err = self.empty_line_(msg, p, end)
            orig_p = p
            if p < end:
                v, p, err = self.decl_(msg, orig_p, end)
                if not err:
                    ds.append(v)
            else:
                err = None
        if not err:
            return ds, p, err
        else:
            return None, p, err

    def decl_(self, msg, start, end):
        """ build | rule | var | subninja | include | pool | default """
        v, p, err = self.build_(msg, start, end)
        if not err:
            return v, p, err
        v, p, err = self.rule_(msg, start, end)
        if not err:
            return v, p, err
        v, p, err = self.var_(msg, start, end)
        if not err:
            return v, p, err
        v, p, err = self.subninja_(msg, start, end)
        if not err:
            return v, p, err
        v, p, err = self.include_(msg, start, end)
        if not err:
            return v, p, err
        v, p, err = self.pool_(msg, start, end)
        if not err:
            return v, p, err
        return self.default_(msg, start, end)
        if not err:
            return v, p, err

    def build_(self, msg, start, end):
        """ "build" ws paths:os ws? ':' ws name:rule
            explicit_deps:eds implicit_deps:ids order_only_deps:ods eol
            (ws var)*:vs -> ['build', os, rule, eds, ids, ods, vs] """
        return self.apply('build', msg, start, end)

    def rule_(self, msg, start, end):
        """ "rule" ws name:n eol (ws var)*:vs -> ['rule', n, vs] """
        return self.apply('rule', msg, start, end)

    def var_(self, msg, start, end):
        """ ws? '=' ws? value:v eol -> ['var', n, v] """
        return self.apply('var', msg, start, end)

    def value_(self, msg, start, end):
        """ (~eol (('$' '\n' ' '+ -> '')|anything))*:vs -> ''.join(vs) """
        return self.apply('value', msg, start, end)

    def subninja_(self, msg, start, end):
        """ "subninja" ws path:p -> ['subninja', p] """
        if end - start < 8 or msg[start:start + 8] != 'subninja':
            return None, start, "expecting 'subninja'"
        p = start + 8
        v, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err
        v, p, err = self.apply('path', msg, p, end)
        if err:
            return None, p, err
        else:
            return ['subninja', v], p, None

    def include_(self, msg, start, end):
        """ "include" ws path:p -> ['include', p] """
        if end - start < 7 or msg[start:start + 7] != 'include':
            return None, start, "expecting 'include'"
        p = start + 7
        v, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err
        v, p, err = self.apply('path', msg, p, end)
        if err:
            return None, p, err
        else:
            return ['include', v], p, None

    def pool_(self, msg, start, end):
        """ "pool" ws name:n eol (ws var)*:vars -> ['pool', n, vars] """
        return self.apply('pool', msg, start, end)

    def default_(self, msg, start, end):
        """ "default" ws paths:ps eol  -> ['default', ps] """
        if end - start < 7 or msg[start:start + 7] != 'default':
            return None, start, "expecting 'default'"
        p = start + 7
        v, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err
        v, p, err = self.apply('paths', msg, p, end)
        if err:
            return None, p, err
        else:
            return ['default', v], p, None

    def paths_(self, msg, start, end):
        """ path:hd (ws path)*:tl -> [hd] + tl """
        return self.apply('paths', msg, start, end)

    def path_(self, msg, start, end):
        """ (('$' ' ')|(~(' '|':'|'='|'|'|eol) anything))+:p -> ''.join(p) """
        return self.apply('path', msg, start, end)

    def name_(self, msg, start, end):
        """ letter:hd (letter|digit|'_')*:tl -> ''.join([hd] + tl) """
        return self.apply('name', msg, start, end)

    def explicit_deps_(self, msg, start, end):
        """ ws? paths:ps -> ps | -> [] """
        return self.apply('explicit_deps', msg, start, end)

    def implicit_deps_(self, msg, start, end):
        """ ws? '|' paths:ps -> ps | -> [] """
        return self.apply('implicit_deps_', msg, start, end)

    def order_only_deps_(self, msg, start, end):
        """ ws? '|' '|' paths:ps -> ps | -> [] """
        return self.apply('order_only_deps', msg, start, end)

    def empty_line_(self, msg, start, end):
        """ ws? (comment | '\n') """
        _, p, err = self.ws_(msg, start, end)
        if p < end and msg[p] == '\n':
            return '\n', p + 1, None
        elif p < end:
            v, p, err = self.comment_(msg, p, end)
            if err:
                return None, p, err
            else:
                return v, p, err
        else:
            return None, p, "expecting a '\n' or a '#'"

    def ws_(self, msg, start, end):
        """ (' '|('$' '\n'))+ """
        p = start
        if p < end and msg[p] == ' ':
            p += 1
        elif p < end - 1 and msg[p:p + 2] == '$\n':
            p += 2
        else:
            return None, p, "expecting either ' ' or '$\n'"

        err = None
        while not err and p < end:
            if msg[p] == ' ':
                p += 1
            elif p < end - 1 and msg[p:p + 2] == '$\n':
                p += 2
            else:
                err = "expecting either ' ' or '$\n'"
        return None, p, None

    def comment_(self, msg, start, end):
        """ '#' (~'\n' anything)* ('\n'|end) """
        if msg[start] != '#':
            return None, start, "expecting a '#'"
        p = start + 1
        while p < end and p != '\n':
            p += 1
        return None, p, None

    def apply(self, rule, msg, start, end):
        ometa_parser = _OMetaNinjaParser(msg[start:end])
        try:
            v = ometa_parser.apply(rule)[0]
            return (v, start + ometa_parser.input.position, None)
        except _MaybeParseError as ex:
            return (None, start + ex.position, PynException(ex.error))


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

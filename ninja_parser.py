import re

from common import PynException



class NinjaParser(object):
    """Parse the contents of a .ninja file and return an AST."""

    def parse(self, msg):
        v, p, err = self.grammar_(msg, 0, len(msg))
        if err:
            raise PynException(err)
        else:
            return v

    def expect(self, msg, start, end, substr):
        l = len(substr)
        if (end - start) < l or msg[start:start + l] != substr:
            return None, start, 'expecting "%s" at %d' % (substr, start)
        return substr, start + l, None

    def grammar_(self, msg, start, end):
        """ ((empty_line* decl)*:ds empty_line*) end -> ds """
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
        if not err:
            return ds, p, err
        else:
            return None, p, err

    def decl_(self, msg, start, end):
        """ build | rule | var | subninja | include | pool | default """
        v, p, err = self.build_(msg, start, end)
        if not err:
            return v, p, None

        v, p, err = self.rule_(msg, start, end)
        if not err:
            return v, p, None

        v, p, err = self.var_(msg, start, end)
        if not err:
            return v, p, None

        v, p, err = self.subninja_(msg, start, end)
        if not err:
            return v, p, None

        v, p, err = self.include_(msg, start, end)
        if not err:
            return v, p, None

        v, p, err = self.pool_(msg, start, end)
        if not err:
            return v, p, None

        v, p, err = self.default_(msg, start, end)
        if err:
            return None, p, ("expecting one of 'build', 'rule', "
                             "a variable name', 'subninja', 'include', ",
                             "'pool', or 'default'")
        else:
            return v, p, None

    def build_(self, msg, start, end):
        """ "build" ws paths:os ws? ':' ws name:rule
            explicit_deps:eds implicit_deps:ids order_only_deps:ods eol
            ws_vars:vs -> ['build', os, rule, eds, ids, ods, vs] """
        p = start
        v, p, err = self.expect(msg, p, end, 'build')
        if err:
            return v, p, err

        _, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err

        os, p, err = self.paths_(msg, p, end)
        if err:
            return None, p, err

        _, p, _ = self.ws_(msg, p, end)
        if err:
            return None, p, err

        v, p, err = self.expect(msg, p, end, ':')
        if err:
            return None, p, err

        _, p, _ = self.ws_(msg, p, end)

        rule, p, err = self.name_(msg, p, end)
        if err:
            return None, p, err

        eds, p, _ = self.explicit_deps_(msg, p, end)

        ids, p, _ = self.implicit_deps_(msg, p, end)

        ods, p, _ = self.order_only_deps_(msg, p, end)

        _, p, err = self.eol_(msg, p, end)
        if err:
            return None, p, err

        vs, p, _ = self.ws_vars_(msg, p, end)

        return ['build', os, rule, eds, ids, ods, vs], p, None

    def rule_(self, msg, start, end):
        """ "rule" ws name:n eol ws_vars:vs -> ['rule', n, vs] """
        p = start

        _, p, err = self.expect(msg, p, end, 'rule')
        if err:
            return None, p, err

        _, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err

        n, p, err = self.name_(msg, p, end)
        if err:
            return None, p, err

        _, p, err = self.eol_(msg, p, end)
        if err:
            return None, p, err

        vs, p, _ = self.ws_vars_(msg, p, end)

        return ['rule', n, vs], p, None

    def ws_vars_(self, msg, start, end):
        """ (ws var)*:vs -> vs """
        p = start
        vs = []
        err = None
        while p < end and not err:
            _, p, err = self.ws_(msg, p, end)
            if not err:
                v, p, err = self.var_(msg, p, end)
                if not err:
                    vs.append(v)
        return vs, p, None

    def var_(self, msg, start, end):
        """ name:n ws? '=' ws? value:v eol -> ['var', n, v] """
        n, p, err = self.name_(msg, start, end)
        if err:
            return None, p, err

        _, p, _ = self.ws_(msg, p, end)

        _, p, err = self.expect(msg, p, end, '=')
        if err:
            return None, p, err

        _, p, _ = self.ws_(msg, p, end)

        v, p, err = self.value_(msg, p, end)
        if err:
            return None, p, err

        _, p, err = self.eol_(msg, p, end)
        if err:
            return None, p, err
        return ['var', n, v], p, None

    def value_(self, msg, start, end):
        """ (~eol (('$' ' ' -> ' ')|('$' '\n' ' '+ -> '')|anything))*:vs
            -> ''.join(vs) """
        p = start
        vs = []
        _, _, err = self.eol_(msg, p, end)
        while err and p < end:
            if p < (end - 1) and msg[p:p + 2] == '$ ':
                vs.append(' ')
                p += 2
            elif p < (end - 1) and msg[p:p + 2] == '$\n':
                p += 2
                _, p, _ = self.ws_(msg, p, end)
            else:
                vs.append(msg[p])
                p += 1
            _, _, err = self.eol_(msg, p, end)
        return ''.join(vs), p, None

    def subninja_(self, msg, start, end):
        """ "subninja" ws path:p eol -> ['subninja', p] """
        v, p, err = self.expect(msg, start, end, 'subninja')
        if err:
            return v, p, err

        v, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err

        v, p, err = self.path_(msg, p, end)
        if err:
            return None, p, err

        _, p, err = self.eol_(msg, p, end)
        return ['subninja', v], p, None

    def include_(self, msg, start, end):
        """ "include" ws path:p eol -> ['include', p] """
        v, p, err = self.expect(msg, start, end, 'include')
        if err:
            return v, p, err

        v, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err

        v, p, err = self.path_(msg, p, end)
        if err:
            return None, p, err

        _, p, err = self.eol_(msg, p, end)
        return ['include', v], p, None

    def pool_(self, msg, start, end):
        """ "pool" ws name:n eol ws_vars:vs -> ['pool', n, vs] """
        _, p, err = self.expect(msg, start, end, 'pool')
        if err:
            return None, p, err
        _, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err
        n, p, err = self.name_(msg, p, end)
        if err:
            return None, p, err
        _, p, err = self.eol_(msg, p, end)
        if err:
            return None, p, err
        vs, p, err = self.ws_vars_(msg, p, end)
        if err:
            return None, p, err
        return ['pool', n, vs], p, None

    def default_(self, msg, start, end):
        """ "default" ws paths:ps eol  -> ['default', ps] """
        v, p, err = self.expect(msg, start, end, 'default')
        if err:
            return v, p, err

        v, p, err = self.ws_(msg, p, end)
        if err:
            return None, p, err

        v, p, err = self.paths_(msg, p, end)
        if err:
            return None, p, err

        _, p, err = self.eol_(msg, p, end)
        return ['default', v], p, None

    def paths_(self, msg, start, end):
        """ path:hd (ws path)*:tl -> [hd] + tl """
        hd, p, err = self.path_(msg, start, end)
        tl = []
        if err:
            return None, p, err

        while p < end and not err:
            v, p, err = self.ws_(msg, p, end)
            if not err:
                v, p, err = self.path_(msg, p, end)
                if not err:
                    tl.append(v)
        return [hd] + tl, p, None

    def path_(self, msg, start, end):
        """ (('$' ' ')|(~(' '|':'|'='|'|'|eol) anything))+:vs -> ''.join(vs) """
        vs = []
        p = start
        while p < end:
            c = msg[p]
            if c.isalpha():
                vs.append(c)
                p += 1
            elif c == ' ':
                break
            elif c == '\n':
                break
            elif c == '$' and (p < end - 1) and msg[p+1] == ' ':
                vs.append(' ')
                p += 2
            elif c in (':', '=', '|'):
                break
            else:
                orig_p = p
                v, p, err = self.eol_(msg, p, end)
                if v or not err:
                    p = orig_p
                    break
                else:
                    vs.append(c)
                    p += 1
        if len(vs) == 0:
            return None, start, 'expecting a path'
        else:
            return ''.join(vs), p, None

    def name_(self, msg, start, end):
        """ letter:hd (letter|digit|'_')*:tl -> ''.join([hd] + tl) """
        p = start
        if p == end:
            return None, p, 'expecting a name'
        hd = msg[p]
        if not hd.isalpha():
            return None, p, 'expecting a letter to start a name'
        p += 1
        tl = []
        while p < end and (msg[p].isalpha() or msg[p].isdigit() or
                           msg[p] == '_'):
            tl.append(msg[p])
            p += 1
        return hd + ''.join(tl), p, None

    def explicit_deps_(self, msg, start, end):
        """ ws? paths:ps -> ps | -> [] """
        if start == end:
            return [], start, None

        _, p, _ = self.ws_(msg, start, end)

        ps, p, err = self.paths_(msg, p, end)
        if err:
            return [], start, None
        return ps, p, None

    def implicit_deps_(self, msg, start, end):
        """ ws? '|' ws? paths:ps -> ps | -> [] """
        if start == end:
            return [], start, None

        _, p, _ = self.ws_(msg, start, end)

        _, p, err = self.expect(msg, p, end, '|')
        if err:
            return [], start, None

        _, p, _ = self.ws_(msg, p, end)

        ps, p, err = self.paths_(msg, p, end)
        if err:
            return [], start, None
        return ps, p, None

    def order_only_deps_(self, msg, start, end):
        """ ws? '|' '|' ws? paths:ps -> ps | -> [] """
        if start == end:
            return [], start, None

        _, p, _ = self.ws_(msg, start, end)

        _, p, err = self.expect(msg, p, end, '||')
        if err:
            return [], start, None

        _, p, _ = self.ws_(msg, p, end)

        ps, p, err = self.paths_(msg, p, end)
        if err:
            return None, p, err
        return ps, p, None

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

    def eol_(self, msg, start, end):
        """ ws? (comment | '\n' | end) """
        if start < end and (msg[start] == ' ' or msg[start] == '$'):
            _, p, err = self.ws_(msg, start, end)
        else:
            p = start
        if p < end:
            if msg[p] == '\n':
                return '\n', p + 1, None
            elif p == end:
                return None, p, None
            elif msg[p] == '#':
                return self.comment_(msg, p, end)
            else:
                return None, p, "expecting a newline, comment, or EOF"
        else:
            return None, p, None

    def ws_(self, msg, start, end):
        """ (' '|('$' '\n'))+ """
        p = start
        err = None
        while not err and p < end:
            if msg[p] == ' ':
                p += 1
            elif msg[p] == '$' and p < end - 1 and msg[p+1] == '\n':
                p += 2
            else:
                err = "expecting either ' ' or '$\n'"
        if p == start:
            return None, p, err
        else:
            return None, p, None

    def comment_(self, msg, start, end):
        """ '#' (~'\n' anything)* ('\n'|end) """
        if msg[start] != '#':
            return None, start, "expecting a '#'"
        p = start + 1
        while p < end and msg[p] != '\n':
            p += 1
        if p < end:
            return '\n', p, None
        else:
            return None, p, None


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

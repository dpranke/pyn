from common import PynException


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

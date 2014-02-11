#!/usr/bin/env python
import optparse
import sys

import pymeta_helper


sample = """

cflags = -Wall

rule cc
  command = gcc $cflags -c $in -o $out

build foo.o: cc foo.c

"""


sample1 = "cflags = -Wall -O1\n"


def main(argv):
    parser = optparse.OptionParser()
    parser.parse_args()

    n = NinjaParser()
    try:
        ast = n.parse(sample1)
        print ast
    except Exception as e:
        print e


class NinjaParser(pymeta_helper.ParserBase):
    name = "pyn"

    grammar = """

grammar    = decls:ds end -> ds

decls      = spaces_or_comments decl:d decls:ds -> [d] + ds
           | spaces_or_comments decl            -> [d]
           | spaces_or_comments                 -> []

decl       = rule | build_edge | variable | default | reference | pool

rule       = "rule" spaces ident:name eol indented_var+:vars -> ['rule', name, vars]

build_edge = "build" spaces outputs:os spaces ":" spaces inputs:is spaces optional_deps:ds -> ['build', os, is, ds]

variable   = ident:name spaces "=" spaces values:v eol -> ['var', name, v]

values     = (~eol anything)+:v  -> ''.join(v)

default    = "default" spaces targets:ts -> ['default', ts]

reference  = "subninja" spaces path:p  -> ['subninja', p]
           | "include" spaces path:p   -> ['import', p]

pool       = "pool" spaces ident:name eol indented_var+:vars -> ['pool', name, vars]

indented_var = spaces variable:v -> v

targets    = ident:i spaces targets:ts -> [i] + ts
           | ident:i                   -> [i]

spaces_or_comments = (' '|'\t'|'\n'|comment)*

comment    = "#" ~('\n') '\n'

eol        = comment
           | ' '* '\n'

ident      = (letter|'_'):hd (letter)*:tl -> ''.join([hd] + tl)

"""


if __name__ == '__main__':
    main(sys.argv[1:])

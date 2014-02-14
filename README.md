# pyn

pyn is a Python-based implementation of
[Ninja](http://martine.github.io/ninja/).

It is pronounced "pin." The name comes from "PYthon Ninja." Not coincidentally,
it also rhymes with the GN frontend to Ninja being developed by the Chromium
project.

Ninja is a brilliantly designed and well-implemented build system.

pyn is intended largely as an exercise to see how hard it is to (re-)implement
a full-fidelity version of Ninja, and to do it clearly, in as few lines as
possible. pyn should be a drop-in replacement for ninja.

The primary intent is to be clear, not fast (use Ninja itself if you want to be
fast); however, it is also intended to be a reference to compare how much
slower a (theoretically) well-written Python program really is to a
well-written C++ program that has been tuned for speed. Eventually there may be
multiple implementations of pyn designed for different goals in mind. 

pyn is also designed to be more easily reusable and extensible, for uses
where you might want to parse and repurpose ninja files.

It uses [PyMeta 2](https://bitbucket.org/wkornewald/pymeta/src),
as a parser generator. PyMeta 2 is an implementation of
[OMeta](https://github.com/alexwarth/ometa-js) in Python.

pyn is licensed under the Apache Source License. For more information see
the LICENSE file in the source repo.

## Things that still need to be implemented

* the 'import' directive
* the 'subninja' directive
* proper variable expansion
* per-build variables
* parallel job execution
  * basic support, including handling of the -j flag
  * support for the -k flag for load throttling
  * support for 'pools'
* deps support
* restat and generator support
* rspfiles
* NINJA_STATUS parsing and options

Also:

* various debug modes (-d stats, explain, keeprsp)
* various tools (-t browse, commands, deps, graph, query, targets, compdb,
  recompact)
  * also -t clean for targets
* something like the .ninja_log support for faster startup and to detect
  command line changes
* more tests
* code coverage integration into the build.ninja file
* additional linting support for pyflakes, pep8 as well as pylint.
* better cross-python module dependency checking inot the build.ninja file
  (python deps support?)

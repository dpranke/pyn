#!/usr/bin/python
# Copyright 2014 Dirk Pranke. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import sys


def main(argv):
    imports = set()
    froms = set()
    content = []
    main_block = []

    modules = set([arg.replace('.py', '') for arg in argv])
    for fname in argv:
        lines = open(fname).readlines()
        for lineno, line in enumerate(lines):
            words = line.split(' ')
            if words[0] == 'import':
                imports.add(line)
            elif words[0] == 'from':
                if words[1] in modules:
                    continue
                else:
                    froms.add(line)
            elif line.startswith('if __name__ =='):
                main_block = lines[lineno:]
                break
            elif line.startswith('#!'):
                continue
            else:
                content.append(line)
        content.append('\n')
        content.append('\n')

    out = '#!/usr/bin/python\n'
    out += ''.join(sorted(imports))
    out += '\n'
    out += ''.join(sorted(froms))
    out += '\n'
    out += ''.join(content)
    out += '\n'
    out += ''.join(main_block)

    out = re.sub('\n\n\n+', '\n\n\n', out).rstrip()
    print out


if __name__ == '__main__':
    main(sys.argv[1:])

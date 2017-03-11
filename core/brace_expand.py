#!/usr/bin/env python3
"""
brace_expand.py
"""

import sys


def Cartesian(tuples):
  if len(tuples) == 1:
    for x in tuples[0]:
      yield (x,)
  else:
    for x in tuples[0]:
      for y in Cartesian(tuples[1:]):
        yield (x,) + y  # join tuples


def main(argv):
  # What kin
  #
  # Cross product:
  # ={a,b}-{c,d}=
  # ==a-c== ==a-d== ==b-c== ==b-d==
  # 2 x 2

  # echo =={a,{b,c,d},e}==
  # ==a=== ==b=== ==c=== ==d=== ==e===
  # 2 + 3
  #
  # So use these tokens: { , }
  # Turn it into a tree
  #
  # [ WordPart, AlternateParts(WordPart, AlternateParts, ), WordPart, ...]


  print('Hello from brace_expand.py')

  # TODO: How to represent the adjacent strings?

  for t in Cartesian([('a', 'b'), ('c', 'd', 'e'), ('f', 'g')]):
    print(t)

  for t in Cartesian([('a', 'b')]):
    print(t)

# Algorithm for cartesian product:
# make it recursive



if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)

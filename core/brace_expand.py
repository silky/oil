#!/usr/bin/env python3
"""
brace_expand.py

NOTE: bash implements in the braces.c file (835 lines).  It uses goto!  Gah.

TODO: {1..7..3} as well.

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


def BraceExpand(parts):
  """
  Args:
    parts: list of strings or tuples

  echo -{A,={a,b}=,B}-

  CompoundWord -> BraceExpandedWord -> CompoundWord

  BraceExpandedWord [
    '-'
    Alternatives (
      'A'
      BraceExpandedWord [
        '='
        Alternatives (
          'a'
          'b'
        )
        '='
      ]
      'B'
    )
    '-'
  ]
  """

  # Evaluation issue:

  # Should we do it as a parse tree transformation?
  # Is it two transformations or one?  I think bash does it with one, but we
  # want two for clarity.
  pass


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
  #
  # BraceExpandedPart(...)

  # Is it almost like a regex? '{' .* ',' ( .* ) '}'
  # Well it can be nested.
  # I think for every { you recurse.


  # $ echo {a,{b},c}
  # a {b} c
  # $ echo {a}
  #{a}

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

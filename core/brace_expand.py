#!/usr/bin/env python3
"""
brace_expand.py

NOTE: bash implements in the braces.c file (835 lines).  It uses goto!  Gah.

TODO: {1..7..3} as well.
  Problem: '.' is a Lit_Chars character.  I think you can reshape it only if
  there's a { and } ?
  Actually you can probably use a regex: 
  digit+ '..' digit+  ( '..' digit+ )?
"""

import sys

from core.id_kind import Id
from osh import ast_ as ast

word_part_e = ast.word_part_e


def Cartesian(tuples):
  if len(tuples) == 1:
    for x in tuples[0]:
      yield (x,)
  else:
    for x in tuples[0]:
      for y in Cartesian(tuples[1:]):
        yield (x,) + y  # join tuples


def BraceDetect(w):
  """
  Args:
    list of WordPart

  Returns:
    CartesianWord

  Another option:

  Take CompoundWord

  And then mutate the parts list?  The invariant can be that the opening {
    always turns into a CartesianPart(word* word) list?
    Just like ArrayLiteralPart.


  Write a grammar for it?  Does it need a stack?  O

  # an alternative is a literal, possibly empty, or another brace_expr
  alt = lit* | brace_expr

  # a brace_expr is group of at least 2 braced and comma-separated
  # alternatives, with optional prefix and suffix.
  brace_expr = lit* '{' alt ',' alt (',' alt)* '}' lit*

  Problem this grammar: it's not LL(1) 
  What's the best way to handle it?  LR(1) parser?

  """
  for i, part in enumerate(w.parts):
    if part.tag == word_part_e.LiteralPart:
      id_ = part.token.id
      if id_ == Id.Lit_LBrace:
        print('{')
        #alt_part, end_index = ParseAlternatives(i, w.parts)
        #if alt_part:
        #  w.parts[i] == alt_part
          # clear until end_index?

      elif id_ == Id.Lit_RBrace:
        print('}')
      elif id_ == Id.Lit_Comma:
        print(',')


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

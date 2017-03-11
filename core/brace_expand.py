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


  Grammar:

    # an alternative is a literal, possibly empty, or another brace_expr

    part = <any part except LiteralPart>

    alt = part* | brace_expr

    # a brace_expr is group of at least 2 braced and comma-separated
    # alternatives, with optional prefix and suffix.
    brace_expr = part* '{' alt ',' alt (',' alt)* '}' part*

  Problem this grammar: it's not LL(1) 

  Is it indirect left-recursive?

  What's the best way to handle it?  LR(1) parser?

  Doesn't submit to Pratt parsing because it's not

  Try ANTLR or what?  Does this have indirect left recursion?

  Maybe do lookahead?  You can use recursive descent if you are OK with a lot
  of lookahead.  quadratic algorithm?

  Not good for PEG: left recursion

  TODO:
  - Try yacc?
  - or ply?  just use strings like ab{ab,cd,e}de

  Iterative algorithm:

  Parse it with a stack?
    It's a stack that asserts there is at least one , in between {}

  Yeah just go through and when you see {, push another list.
  When you get ,  append to list
  When you get } and at least one ',', appendt o list
  When you get } without, then pop

  If there is no matching }, then abort with error

  if not balanced, return error too?
  """
  # Errors:
  # }a{    - stack depth dips below 0
  # {a,b}{ - Stack depth doesn't end at 0

  alternatives = []
  stack = [alternatives]  # stack of alternatives
  cur_parts = []

  state = 0  # 0: 

  for i, part in enumerate(w.parts):
    print(i, part)
    if part.tag == word_part_e.LiteralPart:
      id_ = part.token.id
      if id_ == Id.Lit_LBrace:
        print('{')
        stack[-1].append(ast.CompoundWord(cur_parts))
        cur_parts = []

        alternatives = ['ALT']
        stack.append(alternatives)

        #alt_part, end_index = ParseAlternatives(i, w.parts)
        #if alt_part:
        #  w.parts[i] == alt_part
          # clear until end_index?

      elif id_ == Id.Lit_RBrace:
        print('}')
        stack[-1].append(ast.CompoundWord(cur_parts))
        cur_parts = []
        alternatives = stack.pop()
        cur_parts.append(alternatives)

      elif id_ == Id.Lit_Comma:
        print(',')
        # Top of stack
        stack[-1].append(ast.CompoundWord(cur_parts))
        cur_parts = []

      else:
        cur_parts.append(part)

    else:
      cur_parts.append(part)

  assert len(stack) == 1
  return cur_parts


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

#!/usr/bin/env python3
"""
pgen_tool.py
"""

import sys

from foil.pgen2 import pgen
from foil import py_ast

import tokenize  # from stdlib?


class Parser:
  def __init__(self, grammar):
    self.grammar = grammar  # string name -> pgen_ast.term

  def Parse(self, start_symbol, lexer):
    # TODO:
    pass


class Lexer:
  def __init__(self, f):
    self.f = f
    self._lexer = tokenize.generate_tokens(f.readline)

  def Read(self):
    return self._lexer.__next__()


def main(argv):
  try:
    grammar_path = argv[1]
  except IndexError:
    f = sys.stdin
  else:
    f = open(grammar_path)

  try:
    prog_path = argv[2]
  except IndexError:
    raise
  else:
    prog_f = open(prog_path)

  pg = pgen.PgenParser(f)
  lang_grammar, start_symbol = pg.parse()
  print(lang_grammar)
  print(start_symbol)

  # TODO: Now interpret the grammar somehow.
  # Copy from Annex?
  # Switch on the node.tag

  # Need the Python tokenizer here too!
  # TODO: For clarity, maybe write your own regex pgen tokenizer.  It's
  # trivial.

  # TODO: Get a rule dict of names -> rhs.
  # 

  print(py_ast)


  lexer = Lexer(prog_f)
  for i in range(10):
    print(lexer.Read())
  return


  py = Parser(lang_grammar)
  print(py)
  py.Parse(start_symbol, lexer)


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)

#!/usr/bin/env python3
"""
pgen_tool.py
"""

import sys

from foil.pgen2 import pgen
from foil import py_ast

import tokenize  # from stdlib?
import token


class GrammarInterpreter:

  def __init__(self, grammar, lexer):
    self.grammar = grammar  # string name -> pgen_ast.term
    self.lexer = lexer
    self.token = None
    self.Next()

  def Next(self):
    while True:
      self.token = self.lexer.Read()
      if self.token.type != tokenize.COMMENT:
        break

  def Parse(self, start_symbol, lexer):
    while True:
      self.Next()
      print(self.token)


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

  gp = pgen.GrammarParser(f)
  lang_grammar, start_symbol = gp.parse()
  print(lang_grammar)
  print(start_symbol)

  print(py_ast)

  # Need the Python tokenizer here too!
  # TODO: For clarity, maybe write your own regex pgen tokenizer.  It's
  # trivial.
  lexer = Lexer(prog_f)

  # A grammar interpreter is a parser
  gi = GrammarInterpreter(lang_grammar, lexer)

  print(gi)
  gi.Parse(start_symbol, lexer)


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)

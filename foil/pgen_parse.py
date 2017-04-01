#!/usr/bin/env python3
"""
pgen_tool.py
"""

import sys

from foil import pgen_ast
from foil import py_ast

from foil.pgen2 import token, tokenize  # from stdlib?


class GrammarParser:
    """Parser extracted from pgen2/pgen.py.

    That built a DFA/NFA on the fly.  Here we build an ASDL data structure
    first.
    """

    def __init__(self, f):
        self.generator = tokenize.generate_tokens(f.readline)
        self.gettoken() # Initialize lookahead

    def parse(self):
        """
        Returns:
          pgen_ast.grammar
        """
        rules = {}
        startsymbol = None
        # MSTART: (NEWLINE | RULE)* ENDMARKER
        while self.type != token.ENDMARKER:
            while self.type == token.NEWLINE:
                self.gettoken()
            # RULE: NAME ':' RHS NEWLINE
            name = self.expect(token.NAME)
            self.expect(token.OP, ":")
            rhs = self.parse_rhs()
            self.expect(token.NEWLINE)

            #r = pgen_ast.rule(name, rhs)
            rules[name] = rhs

            #print name, oldlen, newlen
            if startsymbol is None:
                startsymbol = name
        return rules, startsymbol

    def parse_rhs(self):
        """
        Returns:
          Alt
          term

        RHS: ALT ('|' ALT)*
        """
        seq = self.parse_alt()
        if self.value != "|":
            return seq
        else:
            a = pgen_ast.Alt()
            a.alts.append(seq)
            while self.value == "|":
                self.gettoken()
                a.alts.append(self.parse_alt())
            return a

    def parse_alt(self):
        """
        ALT: ITEM+
        """
        seq = pgen_ast.Seq()
        seq.terms.append(self.parse_item())

        while (self.value in ("(", "[") or
               self.type in (token.NAME, token.STRING)):
            seq.terms.append(self.parse_item())

        if len(seq.terms) == 1:
          return seq.terms[0]
        else: 
          return seq

    def parse_item(self):
        """
        Returns:
          Optional
          Repeat
          term

        ITEM: '[' RHS ']' | ATOM ['+' | '*']
        """
        if self.value == "[":
            self.gettoken()
            rhs = self.parse_rhs()
            self.expect(token.OP, "]")
            return pgen_ast.Optional(rhs)
        else:
            atom = self.parse_atom()
            value = self.value
            if value not in ("+", "*"):
                return atom
            self.gettoken()
            if value == "+":
                return pgen_ast.Repeat(atom, 1)
            else:
                return pgen_ast.Repeat(atom, 0)

    def parse_atom(self):
        """
        Returns:
          Group
          Name
          String

        ATOM: '(' RHS ')' | NAME | STRING
        """
        if self.value == "(":
            # TODO: Don't need Group?  It is implicit in the tree?
            self.gettoken()
            rhs = self.parse_rhs()
            self.expect(token.OP, ")")
            return pgen_ast.Group(rhs)
        elif self.type == token.NAME:
            v = self.value
            self.gettoken()
            return pgen_ast.Name(v)
        elif self.type == token.STRING:
            # Tokenizer doesn't strip this
            assert self.value.startswith("'"), self.value
            assert self.value.endswith("'"), self.value
            v = self.value[1:-1]
            self.gettoken()
            return pgen_ast.String(v)
        else:
            self.raise_error("expected (...) or NAME or STRING, got %s/%s",
                             self.type, self.value)

    def expect(self, type, value=None):
        if self.type != type or (value is not None and self.value != value):
            self.raise_error("expected %s/%s, got %s/%s",
                             type, value, self.type, self.value)
        value = self.value
        self.gettoken()
        return value

    def gettoken(self):
        tup = next(self.generator)
        while tup[0] in (tokenize.COMMENT, tokenize.NL):
            tup = next(self.generator)
        self.type, self.value, self.begin, self.end, self.line = tup
        #print token.tok_name[self.type], repr(self.value)


# From Python's Parser/parser.c.
#
# "To avoid the need to construct FIRST sets, we can require that all but
# the last alternative of a rule (really: arc going out of a DFA's state)
# must begin with a terminal symbol."
# Is this true?  Doesn't seem like it.


# pgen2/parse.py
#
# This has the addtoken() interface.
# Hm this looks just like Lemon parser generator?
#
# You call the lexer and parser in a loop.  Rather than the parser calling the
# lexer.

# first, follow, nullable
#
# table of terminals X non-terminals
#
# terminals are the tokens
# non-terminals are the  rules.
#
# Number both of them in order.
#
# Table can be (terminal ID, non-terminal ID) -> production
#
# What's the difference between production ID and non-terminal ID?  aren't they
# the same?
#
# NO a production doesn't have ALTERNATIVES.  Each arm of an alternative is a
# different production for the same non-terminal.
#
# It's BNF vs. EBNF I guess.
#
# I've been seeing BNF -> LL(1) prediction table.  How do I do EBNF?
# Well this

# It's the same; another way to look at it is that we want to construct a
# transition table from non-terminal -> non-terminal based on the current
# terminal/token.

class GrammarInterpreter:

  def __init__(self, grammar, lexer):
    self.grammar = grammar  # string name -> pgen_ast.term
    self.lexer = lexer

    # Token quintuple
    self.type = None
    self.value = None
    self.begin = None
    self.end = None
    self.line = None

    self.Next()

  def Next(self):
    while True:
      t = self.lexer.Read()
      # NOTE: pgen2.tokenize has a different interface than stdlib tokenize!
      self.type, self.value, self.begin, self.end, self.line = t
      if self.type != tokenize.COMMENT:
        break

  def Parse(self, start_symbol, lexer):
    # TODO: For productions, call self.Parse() recursively.

    # for each token, figure out which rules apply?
    # Have to call self.Parse recursively?
    # or self.TryOne?
    # Oh this is about First/Follow sets!  Duh!

    # Do we only need first set?  Not follow?  Because of epsilon?
    #
    # top-down, predictive, non-recursive parser?

    # epislon is like foo* -- how to detect?

    while True:
      self.Next()
      print(self.type, self.value)


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

  gp = GrammarParser(f)
  lang_grammar, start_symbol = gp.parse()
  print(lang_grammar)
  return
  print(start_symbol)

  print(py_ast)

  # TODO: lang_parser -> table
  # What's the table format?
  # (name, int) for terminals
  # (name, int) for non-terminals
  # (int, term*) for productions ?  How to serialize that?
  # prediction table as 2D array: #terminals x #non-terminals

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

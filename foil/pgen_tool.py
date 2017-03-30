#!/usr/bin/env python3
"""
pgen_tool.py
"""

import sys

from foil.pgen2 import pgen
from foil import py_ast


def main(argv):
  try:
    grammar_path = argv[1]
  except IndexError:
    f = sys.stdin
  else:
    f= open(grammar_path)

  p = pgen.PgenParser(f)
  t, start_symbol = p.parse()
  print(t)
  print(start_symbol)

  # TODO: Now interpret the grammar somehow.
  # Copy from Annex?
  # Switch on the node.tag

  # Need the Python tokenizer here too!
  # TODO: For clarity, maybe write your own regex pgen tokenizer.  It's
  # trivial.

  # TODO: Fill these in:
  #
  # Num(object n) -- a number as a PyObject.
  # Bytes(bytes s)
  # Constant(constant value)
  # NameConstant(singleton value)
  #
  # singleton: None, True or False
  # constant can be None, whereas None means "no value" for object.
  #
  # Hm do I want an LST?  Then it shouldn't have these typed values?  That
  # comes later?
  #
  # identifier: this one is used a lot.  Why not string?

  print(py_ast)


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)


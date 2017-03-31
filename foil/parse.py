#!/usr/bin/env python3
"""
parse.py

"""

import sys

from foil.pgen2 import driver
from foil.pgen2 import token, tokenize
from foil import pytree
from foil import pygram


def main(argv):

  # NOTE: Parsing tables are cached with pickle.
  # For Python 3.

  # lib2to3 had a flag for the print statement!  Don't use it with Python 3.

  grammar = pygram.python_grammar_no_print_statement
  #grammar = pygram.python_grammar

  d = driver.Driver(grammar, convert=pytree.convert)

  py_path = argv[1]
  with open(py_path) as f:
    tokens = tokenize.generate_tokens(f.readline)
    tree = d.parse_tokens(tokens)
  print(tree)
  print(type(tree))
  for c in tree.children:
    print(repr(c))
  print('\tChildren: %d' % len(tree.children), file=sys.stderr)


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print >>sys.stderr, 'FATAL: %s' % e
    sys.exit(1)

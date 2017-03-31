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

  grammar = pygram.python_grammar

  d = driver.Driver(grammar, convert=pytree.convert)

  py_path = argv[1]
  with open(py_path) as f:
    tokens = tokenize.generate_tokens(f.readline)
    tree = d.parse_tokens(tokens)
  print(tree)
  print(type(tree))
  for c in tree.children:
    print(repr(c))


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print >>sys.stderr, 'FATAL: %s' % e
    sys.exit(1)

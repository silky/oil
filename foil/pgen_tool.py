#!/usr/bin/env python3
"""
pgen_tool.py
"""

import sys

from foil.pgen2 import pgen


def main(argv):
  grammar_path = argv[1]
  with open(grammar_path) as f:
    p = pgen.PgenParser(f)
    p.parse()


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)


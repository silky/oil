#!/usr/bin/env python3
"""
gen_ast.py

Generate code for the AST.

First in C++.
Maybe later in ML?  Not sure.  In ML I would need the Id tags to take care of
cases. Hm.

Yeah that's probably a useful exercise actually.

Each type is ForExpressionNode

ForExpression.

"""

import sys


def main(argv):
  print('Hello from gen_ast.py')


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)

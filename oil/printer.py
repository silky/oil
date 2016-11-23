#!/usr/bin/env python3
"""
printer.py
"""

import sys


class OilPrinter(object):

  def __init__(self, style=None):
    # Styles are a bunch of options, and can be named.
    # Should encompass the 80 column limit, etc.
    self.style = style

  def Print(self, node, f):
    """
    Args:
      node: CNode
      f: file to print to
    """
    # node.ctype, or cnode.type?

    if node.type == CType.Command:
      # TODO: Use word printer, etc.
      # Which needs parts
      print(node.words)
    else:
      raise AssertionError(node.type)



def main(argv):
  # main() should go in bin/oil.py?  Or bin/tools.py?  sh2oil symlink.

  p = OilPrinter()
  # TODO: parse a program, get the node, print it
  print(p)


if __name__ == '__main__':
  try:
    main(sys.argv)
  except RuntimeError as e:
    print('FATAL: %s' % e, file=sys.stderr)
    sys.exit(1)

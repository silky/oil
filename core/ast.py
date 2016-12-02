#!/usr/bin/python
"""
ast.py
"""

import sys


class BinOutput:
  """
  TODO: Pass this to every node?

  And they will call PrintInt() or something

  """

  def __init__(self, f):
    # params:

    # block_size: 16 bytes
    # ref_width:  3 byte/24-bit references.  Assert if you exceed 16M.
    # index_width: 1 bytes/16 bit references.  No more than 256 contiguous
    # commands.  Can be split up into multiple nodes I guess.

    self.f = f

  # a non-leaf node?
  def AddNode(self, node):
    pass

  # depending on length, either a node or two nodes?  Yeah I guess you can add
  # two nodes
  def AddString(self, s):
    pass

  def Header(self):
    pass


# TODO: bin/oil needs
#
# oil compile foo.sh

def Serialize(f, bin_out):
  pass


class Schema:
  """
  TODO: Collect all the nodes
  """
  def __init__(self):
    self.node_types = []

  def AddNodeType(self, n):
    # TODO:
    # - Look at the doc string
    # - or look at _Schema property?

    # Atoms
    #   Int
    #   String
    #   Ref<T>
    #
    # Composites
    #   SourceLocation
    #   Token
    #   CNode  -- CmdNode -> SimpleCmdNode
    #   RedirNode
    #   ExprNode -- subsumes Word, WordPart, VarOp, because that is the string
    #     language.
    #     CommandExprNode can be CommandSubNode I guess.

    # To compile down: WordPart, VarOp.  These can be expressed as FUNCTIONS
    # including CONCATENATION, and optional WORD SPLITTING.

    pass


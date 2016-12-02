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

    self.block_size = 16  # 16 byte blocks, often organized in 1 + 5*3 fashion
    self.ref_width = 3  # 3 byte/24 bit references

    self.block_index = 0

  # a non-leaf node?
  def AddNode(self, node):
    pass

  # depending on length, either a node or two nodes?  Yeah I guess you can add
  # two nodes
  def AddString(self, s):
    pass

  def Header(self):
    pass


# Vertical slice:
#
# 1. Parse SimpleCommandNode -- list of Words
#    might have to simplify the tree... remove singleton nodes?
# 2. Serialize the CompoundWord -> LiteralPart -> Token -> (SourceLocation, String)
# 3. Write a schema for CompoundWord/LiteralPart/Token/SourceLocation/String
#    On each of those classes.
# 4. Then interpret the schema and write the output
# 5. Read it in C++ manually at first?
#    Nah actually you can just generate classes from the schema.  Just do
#    SimpleCommandNode.words, which is a list of tokens, and then print source
#    locations for debugging.
# 6. And then adapt your old C++ code to execute it.
#
# Then you might be able to use the schema to drive Python.  Call methods no
# BinOutput I guess.


def Dump(node, bin_out):
  # node.Dump(bin_out)

  # And then it will call it on its children for you?
  # Hm.  Do you have to edit every node?  For now I think that is fine.
  # Define the schema at the same time for now?

  # use virtual dispatch on child type?
  #
  # Each node can have a 

  # node.DumpBin
  # They can call _Node.Dump(self, bin_out) oto

  # Do you even need the schema then?
  #
  # This is dependent on the SHAPE of the data and not the ID, so I think
  # virtual dispatch is OK?

  pass


class Schema:
  """
  TODO: Collect all the nodes
  """
  def __init__(self):
    self.defs = []

  def Defs(self):
    return ''.join(self.defs)

  def Add(self, n):
    self.defs.append(n.SCHEMA)

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


#!/usr/bin/env python3
# Copyright 2016 Andy Chu. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
"""
cmd_node.py -- AST Nodes for the command language
"""

import io

from osh import ast

from asdl import py_meta
from core import util
from core.id_kind import Id, IdName
from core.word_node import CompoundWord
from core.base import _Node


class CNode(_Node):
  """Abstract base class for _CompoundCNode/SimpleCommandNode/AssignmentNode."""

  def __init__(self, id):
    _Node.__init__(self, id)
    self.redirects = []  # common to almost all nodes
    # TODO: Do this in ASDL.
    #self.word_start = -1  # 1-based index into words
    #self.word_end = -1

  def _PrintLineRedirects(self, f):
    if self.redirects:
      f.write('redirects=[')
      for i, r in enumerate(self.redirects):
        if i != 0:
          f.write(' ')
        f.write(repr(r))
      f.write(']')

  def _PrintTreeRedirects(self, f, indent=0):
    ind = indent * ' '
    if self.redirects:
      f.write(ind)
      f.write('<\n')
      for r in self.redirects:
        f.write(ind)
        f.write(repr(r))
        f.write(',\n')
      f.write(ind)
      f.write('>\n')


def _GetHereDocsToFill(redirects):
  return [
      r for r in redirects
      if r.op_id in (Id.Redir_DLess, Id.Redir_DLessDash) and not r.was_filled
  ]


def GetHereDocsToFill(node):
  """For CommandParser to fill here docs"""
  # Has to be a POST ORDER TRAVERSAL of here docs, e.g.
  #
  # while read line; do cat <<EOF1; done <<EOF2
  # body
  # EOF1
  # while
  # EOF2
  if isinstance(node, ast.DBracket):
    return []

  if isinstance(node, SimpleCommandNode):
    return _GetHereDocsToFill(node.redirects)

  if isinstance(node, _CompoundCNode):
    # TODO: This must dispatch on the individual heterogeneous children.
    # Some nodes don't have redirects.

    here_docs = []
    for child in node.children:
      here_docs.extend(GetHereDocsToFill(child))
    here_docs.extend(_GetHereDocsToFill(node.redirects))  # parent
    return here_docs

  # Default, for assignment node, etc.
  return []
  #raise AssertionError(node)


class SimpleCommandNode(CNode):
  def __init__(self):
    CNode.__init__(self, Id.Node_Command)
    self.words = []  # CompoundWord instances
    self.more_env = {}  # binding

  def PrintLine(self, f):
    f.write('(Com ')
    self._PrintLineRedirects(f)
    if self.more_env:
      # NOTE: This gives a {a:b, c:d} format.
      f.write('more_env=%s ' % self.more_env)
    for i, w in enumerate(self.words):
      if i != 0:
        f.write(' ')
      w.PrintLine(f)
    f.write(')')

  def PrintTree(self, f, indent=0):
    ind = indent * ' '
    f.write(ind)
    f.write('(Com ')
    # Print words, space-separated
    for i, w in enumerate(self.words):
      if i != 0:
        f.write(' ')
      w.PrintLine(f)  # PrintTree for ComSub and so forth?  nodes?
    if self.redirects:
      f.write('\n')
      self._PrintTreeRedirects(f, indent=indent + 2)
    if self.more_env:
      # NOTE: This gives a {a:b, c:d} format.
      f.write('\n')
      f.write(ind)
      f.write(ind)  # 2 indents
      f.write('more_env=%s\n' % self.more_env)
    multiline = bool(self.redirects) or bool(self.more_env)
    if multiline:
      f.write(ind)
    f.write(')')


class NoOpNode(CNode):
  """Dummy node for the empty "else" condition."""
  def __init__(self):
    CNode.__init__(self, Id.Node_NoOp)

  def PrintLine(self, f):
    f.write('(ElseTrue)')


class AssignmentNode(CNode):
  def __init__(self, scope, flags):
    CNode.__init__(self, Id.Node_Assign)
    self.scope = scope
    self.flags = flags
    # readonly foo bar=baz is allowed.  We separate them here.  Order
    # information is not preserved.
    self.words = []
    self.bindings = {}

  def PrintLine(self, f):
    f.write('(= ')
    f.write('scope=%s ' % self.scope)
    f.write('flags=%s ' % self.flags)
    f.write('words=%s ' % self.words)
    f.write('bindings=%s' % self.bindings)
    f.write(')')


class DBracketNode(CNode):
  """Represents a top level [[ expression."""
  def __init__(self, bnode):
    CNode.__init__(self, Id.KW_DLeftBracket)
    self.bnode = bnode  # type: _BNode

  def PrintLine(self, f):
    f.write('(DBracket ')
    f.write('%s' % self.bnode)
    f.write(')')


class DParenNode(CNode):
  """Represents a top level (( expression."""
  def __init__(self, anode):
    CNode.__init__(self, Id.Op_DLeftParen)
    self.anode = anode  # type: _ExprNode

  def PrintLine(self, f):
    f.write('(DParen ')
    f.write('%s' % self.anode)
    f.write(')')


# NOTE: This has N children, instead of a fixed 0, 1, or 2.
class _CompoundCNode(CNode):
  def __init__(self, id):
    CNode.__init__(self, id)
    # children of type CNode.
    self.children = []

  def _PrintHeader(self, f):
    """Print node name and node-specifc values."""
    raise NotImplementedError(self.__class__.__name__)

  def PrintTree(self, f, indent=0):
    f.write(indent * ' ' + '(')
    self._PrintHeader(f)
    f.write('\n')
    for c in self.children:
      if isinstance(c, py_meta.Obj):
        f.write(str(c))
      else:
        c.PrintTree(f, indent=indent + 2)
        f.write('\n')
    f.write(indent * ' ' + ')')

  def PrintLine(self, f):
    # All on a single line.  No newlines, and don't respect indent.
    f.write('(')
    self._PrintHeader(f)
    f.write(' ')
    for c in self.children:
      c.PrintLine(f)
      f.write(' ')
    f.write(')')

  def __eq__(self, other):
    # TODO: Switch on the type too!  Check all the extra info for each node
    # type.
    return self.id == other.id and self.children == other.children


class ListNode(_CompoundCNode):
  """
  For BraceGroup, function body, case item, etc.

  children: list of AND_OR
  """
  def __init__(self):
    _CompoundCNode.__init__(self, Id.Op_Semi)

  def _PrintHeader(self, f):
    f.write('List')
    if self.redirects:
      f.write(' redirects=')
      f.write(str(self.redirects))


class SubshellNode(_CompoundCNode):
  """
  children: either list of AND_OR, or a LIST node?

  Exec() is different I guess
  """
  def __init__(self):
    _CompoundCNode.__init__(self, Id.Node_Subshell)
    # no redirects for subshell?

  def _PrintHeader(self, f):
    f.write('Subshell')


class ForkNode(_CompoundCNode):
  """
  children: either list of AND_OR, or a LIST node?
  """
  def __init__(self):
    _CompoundCNode.__init__(self, Id.Node_Fork)

  def _PrintHeader(self, f):
    f.write('Fork')


class PipelineNode(_CompoundCNode):
  """
  children: list of SimpleCommandNode
  """
  def __init__(self, children, negated):
    _CompoundCNode.__init__(self, Id.Op_Pipe)
    self.children = children
    self.negated = negated
    # If there are 3 children, they are numbered 0, 1, and 2.  There are two
    # pipes -- 0 and 1.  This list contains the pipe numbers that are |& rather
    # than |.  We are optimizing for the common case.
    self.stderr_indices = []

  def _PrintHeader(self, f):
    f.write('Pipeline%s' % ('!' if self.negated else '',))


class AndOrNode(_CompoundCNode):
  """
  children[0]: LHS
  children[1]: RHS
  """
  def __init__(self, op):
    _CompoundCNode.__init__(self, Id.Node_AndOr)
    self.op = op  # TokenType Op_DAmp or Op_DPipe, set by parser

  def _PrintHeader(self, f):
    f.write('AndOr %s' % IdName(self.op))


class ForNode(_CompoundCNode):
  """
  children: list of AND_OR?
  """

  def __init__(self):
    _CompoundCNode.__init__(self, Id.Node_ForEach)
    self.iter_name = None  # type: str
    self.iter_words = []  # can be empty explicitly empty, which is dumb
    # whether we should iterate over args; iter_words should be empty
    self.do_arg_iter = False

  def _PrintHeader(self, f):
    f.write('For %s' % self.iter_name)
    if self.do_arg_iter:
      f.write(' do_arg_iter')
    else:
      f.write(' %s' % self.iter_words)
    f.write(')')


class ForExpressionNode(_CompoundCNode):
  """
  children: list of AND_OR?
  """
  def __init__(self, init, cond, update):
    _CompoundCNode.__init__(self, Id.Node_ForExpr)
    self.init = init  # type: ExprNode
    self.cond = cond  # type: ExprNode
    self.update = update  # type: ExprNode

  def _PrintHeader(self, f):
    # TODO: Put these on separate lines
    f.write('ForExpr %s %s %s' % (self.init, self.cond, self.update))


class WhileNode(_CompoundCNode):
  """
  children[0] = condition (LIST)
  children[1] = body (LIST)
  """
  def __init__(self, children):
    _CompoundCNode.__init__(self, Id.KW_While)
    self.children = children

  def _PrintHeader(self, f):
    f.write('While')


class UntilNode(_CompoundCNode):
  """
  children[0] = condition (LIST)
  children[1] = body (LIST)
  """
  def __init__(self, children):
    _CompoundCNode.__init__(self, Id.KW_Until)
    self.children = children

  def _PrintHeader(self, f):
    f.write('Until')


class FunctionDefNode(_CompoundCNode):
  """
  children = statement body
  """
  def __init__(self):
    _CompoundCNode.__init__(self, Id.Node_FuncDef)
    self.name = ''

  def _PrintHeader(self, f):
    f.write('FunctionDef %s %s' % (self.name, self.redirects))


class IfNode(_CompoundCNode):
  """
  children = condition, action, condition, action

  Last condition is TRUE for else!!!
  """
  def __init__(self):
    _CompoundCNode.__init__(self, Id.KW_If)

  def _PrintHeader(self, f):
    f.write('If')


class CaseNode(_CompoundCNode):
  """
  Representation:
    pat_word_list = patterns to match, a list parallel to 'children'
    children = CNodes to execute

  This representation makes it easier to write homogeneous walkers.

  Alternatively, we could represent the patterns as a boolean expression, like:

  case $v in foo|bar) echo match ;; *) echo nope ;; esac

  # Also does this force evaluation differently?
  if (v ~ Glob/foo/ or v ~ Glob/bar/) {
    echo match
  } else {
    echo nope
  }
  """
  def __init__(self):
    _CompoundCNode.__init__(self, Id.KW_Case)
    # the word to match against successive patterns
    self.to_match = None  # type: Word
    self.pat_word_list = []  # List<List<Word>> -- patterns to match

  def _PrintHeader(self, f):
    # TODO: Since pat_word_list is parallel to children, it should be printed
    # on multiple lines!
    f.write('Case to_match=%s, pat_word_list=%s' % (self.to_match,
      self.pat_word_list))

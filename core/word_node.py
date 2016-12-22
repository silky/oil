#!/usr/bin/env python3
# Copyright 2016 Andy Chu. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
"""
word_node.py -- AST Nodes for the word language.

In contrast to the "dumb" nodes for the arith, bool, and command languages,
these nodes have a lot of behavior defined by virtual dispatch, precisely
BECAUSE the other 3 languages use the words as "tokens".
"""

import io
import re

from core.base import _Node
from core.id_kind import Id, Kind, IdName, LookupKind
from core.tokens import EncodeTokenVal
from core.value import Value
from core import word

from core import util

#
# Word
#

# http://stackoverflow.com/questions/4419704/differences-between-declare-typeset-and-local-variable-in-bash
# "local and declare are mostly identical and take all the same arguments with
# two exceptions: local will fail if not used within a function, and local with
# no args filters output to print(only locals, declare doesn't.")
EAssignFlags = util.Enum('EAssignFlags', 'EXPORT READONLY'.split())
# I think I need scope and flags
EAssignScope = util.Enum('EAssignScope', 'LOCAL GLOBAL'.split())


#
# WordPart
#


class WordPart(_Node):
  def __init__(self, id):
    _Node.__init__(self, id)

  def __repr__(self):
    # repr() always prints as a single line
    f = io.StringIO()
    self.PrintLine(f)
    return f.getvalue()

  def PrintTree(self, f):
    raise NotImplementedError

  def PrintLine(self, f):
    # Circular -- each part must override at least one
    f.write(repr(self))

  def TokenPair(self):
    """
    Returns:
      Leftmost token and rightmost token.
    """
    raise NotImplementedError(self.__class__.__name__)


class ArrayLiteralPart(WordPart):
  """An Array literal is WordPart that contains other Words.

  In contrast, a DoubleQuotedPart is a WordPart that contains other
  WordParts.

  It's a WordPart because foo=(a b c) is a word with 2 parts.

  Note that foo=( $(ls /) ) is also valid.
  """
  def __init__(self):
    # There is no Left ArrayLiteral, so just use the right one.
    WordPart.__init__(self, Id.Right_ArrayLiteral)
    self.words = []  # type: List[CompoundWord]

  def __repr__(self):
    return '[Array ' + ' '.join(repr(w) for w in self.words) + ']'


class _LiteralPartBase(WordPart):
  def __init__(self, id, token):
    _Node.__init__(self, id)
    self.token = token

  def TokenPair(self):
    return self.token, self.token

  def __eq__(self, other):
    return self.token == other.token


class LiteralPart(_LiteralPartBase):
  """A word part written literally in the program text.

  It could be unquoted or quoted, depending on if it appears in a
  DoubleQuotedPart.  (SingleQuotedPart contains a list of Token instance, not
  WordPart instances.)
  """
  def __init__(self, token):
    _LiteralPartBase.__init__(self, Id.Lit_Chars, token)

  def __repr__(self):
    # This looks like a token, except it uses [] instead of <>.  We need the
    # exact type to reverse it, e.g. '"' vs \".

    # e.g. for here docs, break it for readability.  TODO: Might want the
    # PrintLine/PrintTree distinction for parts to.
    newline = ''
    #if self.token.val == '\n':
    #  newline = '\n'
    # TODO: maybe if we have the token number, we can leave out the type.  The
    # client can look it up?
    return '[%s %s]%s' % (
        IdName(self.token.id), EncodeTokenVal(self.token.val),
        newline)

  def LiteralId(self):
    return self.token.id


class EscapedLiteralPart(_LiteralPartBase):
  """e.g. \* or \$."""

  def __init__(self, token):
    _LiteralPartBase.__init__(self, Id.Lit_EscapedChar, token)

  def __repr__(self):
    # Quoted part.  TODO: Get rid of \ ?
    return '[\ %s %s]' % (
        IdName(self.token.id), EncodeTokenVal(self.token.val))


class SingleQuotedPart(WordPart):

  def __init__(self):
    WordPart.__init__(self, Id.Left_SingleQuote)
    self.tokens = []  # list of Id.Lit_Chars tokens

  def TokenPair(self):
    if self.tokens:
      return self.tokens[0], self.tokens[-1]
    else:
      # NOTE: This can't happen with ''.  TODO: Include the actual single
      # quote!
      return None, None

  def __repr__(self):
    return '[SQ %s]' % (' '.join(repr(t) for t in self.tokens))


class DoubleQuotedPart(WordPart):

  def __init__(self):
    WordPart.__init__(self, Id.Left_DoubleQuote)
    # TODO: Add token_type?  Id.Left_D_QUOTE, Id.Left_DD_QUOTE.  But what about
    # here doc?  It could be a dummy type.
    self.parts = []

  def __eq__(self, other):
    return self.parts == other.parts

  def __repr__(self):
    return '[DQ ' + ''.join(repr(p) for p in self.parts) + ']'

  def TokenPair(self):
    if self.parts:
      begin, _ = self.parts[0].TokenPair()
      _, end = self.parts[-1].TokenPair()
      return begin, end
    else:
      return None, None


class CommandSubPart(WordPart):
  def __init__(self, token, command_list):
    WordPart.__init__(self, Id.Left_CommandSub)
    self.token = token
    self.command_list = command_list

  def __eq__(self, other):
    return self.command_list == other.command_list

  def __repr__(self):
    f = io.StringIO()
    self.command_list.PrintLine(f)  # print(on a single line)
    return '[ComSub %s]' % f.getvalue()


class VarSubPart(WordPart):

  def __init__(self, name, token=None):
    """
    Args:
      name: a string, including '@' '*' '#' etc.?
      token: For debugging only?  Change to SourceLocation?
    """
    WordPart.__init__(self, Id.Left_VarSub)
    self.name = name
    self.token = token

    # This is the PARSED representation.  The executed representation will be
    # a tree of ExprNode.
    self.prefix_op = None  # e.g. VarOp0(VSubBang)
    self.bracket_op = None  # e.g. VarOp1(ExprNode) or VarOp0(Lit_At)
    self.suffix_op = None  # e.g. VarOp1(VTest) or VarOp1(VOp1) or VOp2

  def PrintLine(self, f):
    f.write('[VarSub %s' % self.name)  # no quotes around name
    if self.prefix_op:
      f.write(' prefix_op=%r' % self.prefix_op)
    if self.bracket_op:
      f.write(' bracket_op=%r' % self.bracket_op)
    if self.suffix_op:
      f.write(' suffix_op=%r' % self.suffix_op)
    f.write(']')

  def TokenPair(self):
    if self.token:
      return self.token, self.token
    else:
      return None, None


class TildeSubPart(WordPart):

  def __init__(self, prefix):
    """
    Args:
      prefix: tilde prefix ("" if no prefix)
    """
    WordPart.__init__(self, Id.Lit_Tilde)
    self.prefix = prefix

  def __repr__(self):
    return '[TildeSub %r]' % self.prefix


class ArithSubPart(WordPart):

  def __init__(self, anode):
    # TODO: Do we want to also have Id.Left_ArithSub2 to preserve the source?
    # Although honestly, for most uses cases, it's probably fine to convert
    # everything to POSIX.
    WordPart.__init__(self, Id.Left_ArithSub)
    self.anode = anode

  def __repr__(self):
    return '[ArithSub %r]' % self.anode


class _BTokenInterface(object):
  """
  Common interface between unevaluated words (for [[ ) and evaluated words
  (for [ ).
  """
  def BoolId(self):
    """Return a token type for [[ and [."""
    raise NotImplementedError


class BToken(object):
  """Concrete class For [.

  Differences: uses -a and -o.  No ( ).

  Problem: In C++, you will have to use the parser at RUNTIME.  So it might
  have to be rewritten anyway.
  """
  def __init__(self, arg):
    self.arg = arg

  def BoolId(self):
    """Return a token type."""


#
# Word
#


class Word(_Node, _BTokenInterface):
  """A word or an operator."""

  def __init__(self):
    _Node.__init__(self, Id.Word_Compound)

  def __repr__(self):
    # repr() always prints as a single line
    f = io.StringIO()
    self.PrintLine(f)
    return f.getvalue()

  def PrintTree(self, f):
    raise NotImplementedError

  def PrintLine(self, f):
    raise NotImplementedError

  def TokenPair(self):
    """
    Returns:
      Leftmost token and rightmost token.
    """
    raise NotImplementedError


class CompoundWord(Word):
  """A word that is a sequence of WordPart instances"""

  def __init__(self, parts=None):
    Word.__init__(self)
    self.parts = parts or []  # public, mutable

  def __eq__(self, other):
    return self.parts == other.parts

  def PrintLine(self, f):
    s = '{' + ' '.join(repr(p) for p in self.parts) + '}'
    f.write(s)

  def TokenPair(self):
    if self.parts:
      begin_token, _ = self.parts[0].TokenPair()
      _, end_token = self.parts[-1].TokenPair()
      return begin_token, end_token
    else:
      return None, None


class TokenWord(Word):
  """A word that is just a token.

  NOTES:
  - The token range for this token may be more than one.  For example: a
    Id.Op_Newline is a token word that the CommandParser needs to know about.
    It may "own" Id.Ignored_Comment and Id.Ignored_Space nodes preceding it.
    These are tokens the CommandParser does NOT need to know about.
  - the Id.Eof_Real TokenWord owns and trailing whitespace.
  """
  def __init__(self, token):
    Word.__init__(self)
    self.token = token

  def __eq__(self, other):
    return self.token == other.token

  def PrintLine(self, f):
    f.write('{%s %s}' % (
        IdName(self.token.id), EncodeTokenVal(self.token.val)))

  def TokenPair(self):
    return self.token, self.token

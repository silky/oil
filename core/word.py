#!/usr/bin/python
"""
word.py
"""

import sys

from core.id_kind import Id
from osh import ast

word_e = ast.word_e


def _EvalWordPart(part):
  """Evaluate a WordPart at PARSE TIME.

  Used for:
  
  1. here doc delimiters
  2. function names
  3. for loop variable names
  4. Compiling constant regex words at parse time
  5. a special case for ${a////c} to see if we got a leading slash in the
  pattern.

  Returns:
    3-tuple of
      ok: bool, success.  If there are parts that can't be statically
        evaluated, then we return false.
      value: a string (not Value)
      quoted: whether any part of the word was quoted
  """
  if part.id == Id.Right_ArrayLiteral:
    # Array literals aren't good for any of our use cases.  TODO: Rename
    # EvalWordToString?
    return False, '', False

  elif part.id == Id.Lit_Chars:
    return True, part.token.val, False

  elif part.id == Id.Lit_EscapedChar:
    val = part.token.val
    assert len(val) == 2, val  # e.g. \*
    assert val[0] == '\\'
    s = val[1]
    return True, s, True

  elif part.id == Id.Left_SingleQuote:
    s = ''.join(t.val for t in part.tokens)
    return True, s, True

  elif part.id == Id.Left_DoubleQuote:
    ret = ''
    for p in part.parts:
      ok, s, _ = _EvalWordPart(p)
      if not ok:
        return False, '', True
      ret += s

    return True, ret, True  # At least one part was quoted!

  elif part.id in (
      Id.Left_CommandSub, Id.Left_VarSub, Id.Lit_Tilde, Id.Left_ArithSub,
      Id.Left_ArithSub2):
    return False, '', False

  else:
    raise AssertionError(part.id)


def StaticEval(w):
  """Evaluate a Word at PARSE TIME.
  """
  ret = ''
  quoted = False
  for part in w.parts:
    ok, s, q = _EvalWordPart(part)
    if not ok:
      return False, '', quoted
    if q:
      quoted = True  # at least one part was quoted
    ret += s
  return True, ret, quoted



# Move from cmd_parse
def TildeDetect(w):
  pass


def AsFuncName(w):
  pass


def AsArithVarName(w):
  """Returns a string if this word looks like an arith var; otherwise False."""
  if len(w.parts) != 1:
    return ""

  return PartArithVarLikeName(w.parts[0])


def HasArrayPart(w):
  """Used in cmd_parse."""
  for part in w.parts:
    if part.id == Id.Right_ArrayLiteral:
      return True
  return False


def LooksLikeAssignment(w):
  pass


def AssignmentBuiltinId(w):
  #assert isinstance(w, ast.CompoundWord)
  pass


# Polymorphic between TokenWord and CompoundWord

def ArithId(node):
  if node.tag == word_e.TokenWord:
    return node.token.id

  assert node.tag == word_e.CompoundWord


def BooldId(node):
  if node.tag == word_e.TokenWord:
    return node.token.id

  # Assume it's a CompoundWord
  assert node.tag == word_e.CompoundWord


def CommandId(node):
  if node.tag == word_e.TokenWord:
    return node.token.id

  # Assume it's a CompoundWord
  assert node.tag == word_e.CompoundWord

#!/usr/bin/python
"""
word.py
"""

import sys

from osh import ast
from core.id_kind import Id
from core.tokens import Token

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
  """Evaluate a CompoundWord at PARSE TIME.
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


def TildeDetect(word):
  """Detect tilde expansion.

  If it needs to include a TildeSubPart, return a new word.  Otherwise return
  None.

  NOTE: This algorithm would be a simpler if
  1. We could assume some regex for user names.
  2. We didn't need to do brace expansion first, like {~foo,~bar}
  OR
  - If Lit_Slash were special (it is in the VAROP states, but not OUTER
  state).  We could introduce another lexer mode after you hit Lit_Tilde?

  So we have to scan all LiteralPart instances until they contain a '/'.

  http://unix.stackexchange.com/questions/157426/what-is-the-regex-to-validate-linux-users
  "It is usually recommended to only use usernames that begin with a lower
  case letter or an underscore, followed by lower case letters, digits,
  underscores, or dashes. They can end with a dollar sign. In regular
  expression terms: [a-z_][a-z0-9_-]*[$]?

  On Debian, the only constraints are that usernames must neither start with
  a dash ('-') nor contain a colon (':') or a whitespace (space: ' ', end
  of line: '\n', tabulation: '\t', etc.). Note that using a slash ('/') may
  break the default algorithm for the definition of the user's home
  directory.
  """
  from core.word_node import CompoundWord, TildeSubPart, LiteralPart

  if not word.parts:
    return None
  part0 = word.parts[0]
  if part0.id != Id.Lit_Chars:
    return None
  if part0.token.id != Id.Lit_Tilde:
    return None

  prefix = ''
  found_slash = False
  # search for the next /
  for i in range(1, len(word.parts)):
    # Not a literal part, and we did NOT find a slash.  So there is no
    # TildeSub applied.  This would be something like ~X$var, ~$var,
    # ~$(echo), etc..  The slash is necessary.
    if word.parts[i].id != Id.Lit_Chars:
      return None
    val = word.parts[i].token.val
    p = val.find('/')

    if p == -1:  # no slash yet
      prefix += val

    elif p >= 0:
      # e.g. for ~foo!bar/baz, extract "bar"
      # NOTE: requires downcast to LiteralPart
      pre, post = val[:p], val[p:]
      prefix += pre
      tilde_part = TildeSubPart(prefix)
      remainder_part = LiteralPart(Token(Id.Lit_Chars, post))
      found_slash = True
      break

  w = CompoundWord()
  if found_slash:
    w.parts.append(tilde_part)
    w.parts.append(remainder_part)
    j = i + 1
    while j < len(word.parts):
      w.parts.append(word.parts[j])
      j += 1
  else:
    # The whole thing is a tilde sub, e.g. ~foo or ~foo!bar
    w.parts.append(TildeSubPart(prefix))
  return w


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
  from core.word_node import CompoundWord, SingleQuotedPart
  assert isinstance(w, CompoundWord)
  if len(w.parts) == 0:
    return False

  part0 = w.parts[0]
  if part0.id != Id.Lit_Chars:  # TODO: Turn this into a tag test
    return False

  if part0.token.id != Id.Lit_VarLike:
    return False

  assert part0.token.val.endswith('=')
  name = part0.token.val[:-1]

  rhs = CompoundWord()
  if len(w.parts) == 1:
    # NOTE: This is necesssary so that EmptyUnquoted elision isn't
    # applied.  EMPTY= is like EMPTY=''.
    rhs.parts.append(SingleQuotedPart())
  else:
    for p in w.parts[1:]:
      rhs.parts.append(p)
  return name, rhs


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

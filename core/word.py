#!/usr/bin/python
"""
word.py
"""

import sys

from osh import ast

word_e = ast.word_e


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


def StaticEval(w):
  pass


# Used in word_eval
def IsSubst(w):
  pass


def AssignmentBuiltinId(w):
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

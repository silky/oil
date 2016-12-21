#!/usr/bin/python
"""
word.py
"""

import sys


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




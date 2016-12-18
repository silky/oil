#!/usr/bin/python
"""
format.py

Like encode.py, but uses text instead of binary.

For pretty-printing.


"""

import sys

from asdl import asdl_parse as asdl


class ColorOutput:
  def __init__(self, f):
    self.f = f


class TextOutput(ColorOutput):
  """TextOutput put obeys the color interface, but outputs nothing."""
  def __init__(self, f):
    ColorOutput.__init__(self, f)


class HtmlOutput(ColorOutput):
  # This one can have wider columns
  def __init__(self, f):
    ColorOutput.__init__(self, f)


class AnsiOutput(ColorOutput):
  # Generally 80 column output

  def __init__(self, f):
    ColorOutput.__init__(self, f)


def PrintArray(obj_list, out):
  """
  Args:
    obj_list: py_meta.Obj
  """
  pass


INDENT = 2
def PrintObj(obj, out, max_col=80):
  """
  Args:
    obj: py_meta.Obj
    params
    out: Print a single line, or multiple lines an indents?

  NOTES:

  ArithBinary
    op_id
    left
    right

  vs
  (ArithBinary op_id left right)

  {} for words, [] for wordpart?  What about tokens?  I think each node has to
  be able to override the behavior.  How to do this though?  Free functions?
  """
  print(obj.__class__.__name__)
  for name in obj.FIELDS:
    #print(name)
    field_val = getattr(obj, name)
    desc = obj.DESCRIPTOR_LOOKUP[name]
    if isinstance(desc, asdl.IntType):
      pass
    elif isinstance(desc, asdl.Sum) and asdl.is_simple(desc):
      pass
    elif isinstance(desc, asdl.StrType):
      pass
    elif isinstance(desc, asdl.ArrayType):
      pass
    elif isinstance(desc, asdl.MaybeType):
      # Because it's optional, print the name.  Same with bool?
      pass
    else:
      # Recursive call for child records.  Write children before parents.
      PrintObj(field_val, out, max_col=max_col-INDENT)

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
    self.lines = []

  def Write(self, line):
    self.lines.append(line)


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


def PrintArray(obj_list, lines, max_col=80, indent=0):
  """
  Args:
    obj_list: py_meta.Obj
  """
  for obj in reversed(obj_list):
    PrintObj(obj, lines, max_col, indent)


INDENT = 2
def PrintObj(obj, lines, max_col=80, indent=0):
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
  ind = ' ' * indent
  line = ind + obj.__class__.__name__
  # Reverse order since we are appending to lines and then reversing.
  for name in reversed(obj.FIELDS):
    #print(name)
    field_val = getattr(obj, name)
    desc = obj.DESCRIPTOR_LOOKUP[name]
    if isinstance(desc, asdl.IntType):
      # TODO: How to check for overflow?
      line += ' %s' % field_val
    elif isinstance(desc, asdl.Sum) and asdl.is_simple(desc):
      pass
    elif isinstance(desc, asdl.StrType):
      line += ' %s' % field_val
    elif isinstance(desc, asdl.ArrayType):
      PrintArray(field_val, lines, max_col=max_col-INDENT, indent=indent+INDENT)
    elif isinstance(desc, asdl.MaybeType):
      # Because it's optional, print the name.  Same with bool?
      pass
    else:
      # Recursive call for child records.  Write children before parents.

      # Children can't be written directly to 'out'.  We have to know if they
      # will fit first.
      child_lines = []
      PrintObj(field_val, child_lines, max_col=max_col-INDENT, indent=indent+INDENT)
      lines.extend(child_lines)

  #out.Write(line)
  lines.append(line)


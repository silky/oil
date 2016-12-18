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

  Common case:
  ls /foo /bar -> (Com {[ls]} {[/foo]} {[/bar]})

  Or use color for this?
  """
  # These lines can be possibly COMBINED all into one.  () can replace
  # indentation?
  child_parts = []

  # Reverse order since we are appending to lines and then reversing.
  for name in reversed(obj.FIELDS):
    #print(name)
    field_val = getattr(obj, name)
    desc = obj.DESCRIPTOR_LOOKUP[name]
    if isinstance(desc, asdl.IntType):
      # TODO: How to check for overflow?
      child_parts.append(str(field_val))

    elif isinstance(desc, asdl.Sum) and asdl.is_simple(desc):
      pass

    elif isinstance(desc, asdl.StrType):
      child_parts.append(field_val)

    elif isinstance(desc, asdl.ArrayType):
      # Hm does an array need the field name?  I can have multiple arrays like
      # redirects, more_env, and words.  Is there a way to make "words"
      # special?
      #child_parts = []
      #PrintArray(field_val, child_parts, max_col=max_col-INDENT,
      #    indent=indent+INDENT)
      obj_list = field_val
      for child_obj in reversed(obj_list):
        PrintObj(child_obj, child_parts, max_col, indent)

    elif isinstance(desc, asdl.MaybeType):
      # Because it's optional, print the name.  Same with bool?
      pass
    else:
      # Recursive call for child records.  Write children before parents.

      # Children can't be written directly to 'out'.  We have to know if they
      # will fit first.
      child_parts = []
      PrintObj(field_val, child_parts, max_col=max_col-INDENT, indent=indent+INDENT)
      lines.extend(child_parts)

  # TODO: Add up all the length of child_parts
  # And consolidate it into a single one if it fits in max_col?

  print([len(p) for p in child_parts])

  ind = ' ' * indent
  line = ind + obj.__class__.__name__

  #out.Write(line)
  lines.extend(child_parts)
  lines.append(line)


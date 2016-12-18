#!/usr/bin/python
"""
format.py

Like encode.py, but uses text instead of binary.

For pretty-printing.
"""

import io
import sys

from asdl import asdl_parse as asdl


class ColorOutput:
  """
  API:

  PushColor() ?
  PopColor()?

  Things that should be color: raw text, like "ls" and '/foo/bar"

  certain kinds of nodes.

  Should we have both a background color and a foreground color?
  """
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
  """
  HTML one can have wider columns.  Maybe not even fixed-width font.
  Hm yeah indentation should be logical then?

  Color: HTML spans
  """
  def __init__(self, f):
    ColorOutput.__init__(self, f)


class AnsiOutput(ColorOutput):
  """
  Generally 80 column output

  Color: html code and restore

  """

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

def MakeTree(obj, max_col=80, depth=0):
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

  Invariant:
    an individual field is never split up?

  (ArithBinary (Plus) (ArithBinary (Plus) (Const 1) (Const 2)) (Const 3))

  # If it's a simple sum, no tag
  (ArithBinary Plus (ArithBinary Plus (Const 1) (Const 2)) (Const 3))

  vs.

  ArithBinary
    Plus
    ArithBinary
      Plus
      Const 1
      Const 2
    Const 3
  """
  # These lines can be possibly COMBINED all into one.  () can replace
  # indentation?
  parts = [obj.__class__.__name__]

  # Reverse order since we are appending to lines and then reversing.
  for name in obj.FIELDS:
    #print(name)
    field_val = getattr(obj, name)
    desc = obj.DESCRIPTOR_LOOKUP[name]
    if isinstance(desc, asdl.IntType):
      # TODO: How to check for overflow?
      parts.append(str(field_val))

    elif isinstance(desc, asdl.Sum) and asdl.is_simple(desc):
      # Hm the second
      parts.append(field_val.name)

    elif isinstance(desc, asdl.StrType):
      parts.append(field_val)

    elif isinstance(desc, asdl.ArrayType):
      # Hm does an array need the field name?  I can have multiple arrays like
      # redirects, more_env, and words.  Is there a way to make "words"
      # special?
      #child_parts = []
      #PrintArray(field_val, child_parts, max_col=max_col-INDENT,
      #    indent=indent+INDENT)
      obj_list = field_val
      for child_obj in reversed(obj_list):
        t = MakeTree(child_obj, max_col, depth)
        parts.append(t)

    elif isinstance(desc, asdl.MaybeType):
      # Because it's optional, print the name.  Same with bool?
      pass
    else:
      # Recursive call for child records.  Write children before parents.

      # Children can't be written directly to 'out'.  We have to know if they
      # will fit first.
      t = MakeTree(field_val, max_col=max_col-INDENT, depth=depth+1)
      parts.append(t)

  # TODO: Add up all the length of child_parts
  # And consolidate it into a single one if it fits in max_col?

  # I think it should be [head, ...tail] format.  Maybe (head, ...tail)
  # head, tail = foo[0], foo[1:]
  #
  # And then you CHOOSE between indentatino or parens to denote structure (())
  #
  # return (string or tuple)
  # string means: I can be combined with other strings
  # tuple: I already determined that one of my children is too long.  So the
  # whole structure must be kept in tact.  no wrapping.

  # If any part is a tuple, then put everything on its own separate line.

  has_multiline = any(isinstance(p, list) for p in parts)
  if has_multiline:
    return parts

  # All strings
  total_len = sum(len(p) for p in parts)
  if total_len < 80:
    # TODO: Use () here
    f = io.StringIO()
    PrintSingle(parts, f)
    return f.getvalue()

  return parts


def PrintTree(node, f, indent=0):
  ind = ' ' * indent
  if isinstance(node, str):
    print(ind + node, file=f)
  elif isinstance(node, list):
    # Assume the first entry is always a string
    print(ind + node[0], file=f)
    for child in node[1:]:
      PrintTree(child, f, indent=indent+INDENT)
  else:
    raise AssertionError(node)


# TODO: Should take ColorOutput instead of a file?

def PrintSingle(parts, f):
  f.write('(')
  n = len(parts)
  for i, p in enumerate(parts):
    if isinstance(p, str):
      f.write(p)
    elif isinstance(p, list):
      # Assume the first entry is always a string
      f.write(ind + node[0])
      PrintSingle(node[1:], f)
    else:
      raise AssertionError(node)
    if i != n - 1:
      f.write(' ')
  f.write(')')

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


INDENT = 2

def MakeTree(obj, max_col=80, depth=0):
  """
  Args:
    obj: py_meta.Obj
    params
    out: Print a single line, or multiple lines an indents?

  NOTES:

  {} for words, [] for wordpart?  What about tokens?  I think each node has to
  be able to override the behavior.  How to do this though?  Free functions?

  Common case:
  ls /foo /bar -> (Com {[ls]} {[/foo]} {[/bar]})
  Or use color for this?

  (ArithBinary Plus (ArithBinary Plus (Const 1) (Const 2)) (Const 3))

  vs.

  ArithBinary
    Plus
    ArithBinary
      Plus
      Const 1
      Const 2
    Const 3

  Algorithm:
  - Create a parts list, like ['ArithUnary', '1', '2']
  - If any of the children are lists themselves...

  """
  # HACK to incorporate old AST nodes.  Remove when the whole thing is
  # converted.
  from asdl import py_meta
  if not isinstance(obj, py_meta.CompoundObj):
    #raise AssertionError(obj)
    parts = [repr(obj)]
    return parts

  # These lines can be possibly COMBINED all into one.  () can replace
  # indentation?
  parts = [obj.__class__.__name__]

  for name in obj.FIELDS:
    #print(name)
    try:
      field_val = getattr(obj, name)
    except AttributeError:
      parts.append('%s=?' % name)
      continue

    desc = obj.DESCRIPTOR_LOOKUP[name]
    if isinstance(desc, asdl.IntType):
      # TODO: How to check for overflow?
      parts.append(str(field_val))

    elif isinstance(desc, asdl.Sum) and asdl.is_simple(desc):
      # HACK for now to reflect that Id is an integer.
      if isinstance(field_val, int):
        parts.append(str(field_val))
      else:
        parts.append(field_val.name)

    elif isinstance(desc, asdl.StrType):
      parts.append(field_val)

    elif isinstance(desc, asdl.ArrayType):
      # Hm does an array need the field name?  I can have multiple arrays like
      # redirects, more_env, and words.  Is there a way to make "words"
      # special?
      obj_list = field_val
      #parts.append('[')  # TODO: How to indicate list?
      for child_obj in obj_list:
        t = MakeTree(child_obj, max_col, depth)
        parts.append(t)
      #parts.append(']')

    elif isinstance(desc, asdl.MaybeType):
      # Because it's optional, print the name.  Same with bool?
      pass

    else:
      # Recursive call for child records.  Write children before parents.

      # Children can't be written directly to 'out'.  We have to know if they
      # will fit first.
      t = MakeTree(field_val, max_col=max_col-INDENT, depth=depth+1)
      parts.append(t)

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

  # TODO: This is to aggressive?
  #has_multiline = any(isinstance(p, list) for p in parts)
  #for p in parts:
  #  if isinstance(p, list):
  #    print('LIST', p)
  #if has_multiline:
  #  return parts

  def RecursiveStringLength(pnode):
    if isinstance(pnode, list):
      total_len = 0
      for child in pnode:
        total_len += RecursiveStringLength(child)
      return total_len
    elif isinstance(pnode, str):
      return len(pnode)
    else:
      raise AssertionError(node)

  # All strings
  #total_len = sum(len(p) for p in parts)
  total_len = RecursiveStringLength(parts)
  #print('TOTAL LEN', total_len)

  if total_len < 100:  # Could use a better heuristic to account for ()
    f = io.StringIO()
    PrintSingle(parts, f)
    #print('RETURNING', f.getvalue())
    return f.getvalue()  # a single string

  return parts


def PrintTree(node, f, indent=0):
  ind = ' ' * indent
  if isinstance(node, str):
    print(ind + node, file=f)
  elif isinstance(node, list):
    # Assume the first entry is always a string.
    # We could also insert patterns here... e.g. if it is a word, then use {},
    # and WordPart, use [], without any qualifier?
    # But I will have StaticWord/DynamicWord/UnsafeWord.

    print(ind + '(' + node[0], file=f)
    for child in node[1:]:
      PrintTree(child, f, indent=indent+INDENT)
    print(ind + ')', file=f)
  else:
    raise AssertionError(node)


# TODO: Should take ColorOutput instead of a file?

def PrintSingle(parts, f, indent=0):
  """Print to a single line, used in MakeTree."""
  ind = ' ' * indent
  f.write('(')
  n = len(parts)
  for i, p in enumerate(parts):
    if isinstance(p, str):
      f.write(p)
    elif isinstance(p, list):
      # Assume the first entry is always a string
      f.write(ind + p[0])
      PrintSingle(p[1:], f)
    else:
      raise AssertionError(p)
    if i != n - 1:
      f.write(' ')
  f.write(')')

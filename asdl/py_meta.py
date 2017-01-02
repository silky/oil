#!/usr/bin/env python3
"""
py_meta.py

Parse an ASDL file, and generate Python classes using metaprogramming.
All objects descends from Obj, which allows them to be dynamically type-checked
and serialized.  Objects hold type descriptors, which are defined in asdl.py.

Usage:
  from osh import ast

  n1 = ast.ArithVar()
  n2 = ast.ArrayLiteralPart()

API Notes:

The Python AST module doesn't make any distinction between simple and compound
sum types.  (Simple types have no constructors with fields.)

C++ has to make this distinction for reasons of representation.  It's more
efficient to hold an enum value than a pointer to a class with an enum value.
In Python I guess that's not quite true.

So in order to serialize the correct bytes for C++, our Python metaclass
implementation has to differ from what's generated by asdl_c.py.  More simply
put: an op is Add() and not Add, an instance of a class, not an integer value.
"""

import io
import sys

from asdl import format as fmt
from asdl import asdl_parse as asdl  # ALIAS for nodes


def _CheckType(value, expected_desc):
  """Is value of type expected_desc?

  Args:
    value: Obj or primitive type
    expected_desc: instance of asdl.Product, asl.Sum, asdl.StrType,
      asdl.IntType, ArrayType, MaybeType, etc.
  """
  if isinstance(expected_desc, asdl.MaybeType):
    if value is None:
      return True
    return _CheckType(value, expected_desc.desc)

  if isinstance(expected_desc, asdl.ArrayType):
    if not isinstance(value, list):
      return False
    # Now check all entries
    for item in value:
      if not _CheckType(item, expected_desc.desc):
        return False
    return True

  if isinstance(expected_desc, asdl.StrType):
    return isinstance(value, str)

  if isinstance(expected_desc, asdl.IntType):
    return isinstance(value, int)

  try:
    actual_desc = value.__class__.DESCRIPTOR
  except AttributeError:
    return False  # it's not of the right type

  if isinstance(expected_desc, asdl.Product):
    return actual_desc is expected_desc

  if isinstance(expected_desc, asdl.Sum):
    if asdl.is_simple(expected_desc):
      return actual_desc is expected_desc
    else:
      for cons in expected_desc.types:
        #print("CHECKING desc %s against %s" % (desc, cons))
        # It has to be one of the alternatives
        if actual_desc is cons:
          return True

  return False


class Obj:
  # NOTE: We're using CAPS for these static fields, since they are constant at
  # runtime after metaprogramming.
  DESCRIPTOR = None  # Used for type checking


class SimpleObj(Obj):
  """An enum value.

  Other simple objects: int, str, maybe later a float.
  """

  def __init__(self, enum_id, name):
    self.enum_id = enum_id
    self.name = name

  def __repr__(self):
    return '<%s %s %s>' % (self.__class__.__name__, self.name, self.enum_id)


class CompoundObj(Obj):
  """A compound object with fields, e.g. a Product or Constructor.

  Uses some metaprogramming.
  """
  FIELDS = []  # ordered list of field names
  DESCRIPTOR_LOOKUP = {}  # field name: (asdl.Type | int | str)

  # Always set for constructor types, which are subclasses of sum types.  Never
  # set for product types.
  tag = None

  def __init__(self, *args, **kwargs):
    # The user must specify ALL required fields or NONE.
    self._assigned = {f: False for f in self.FIELDS}
    self._SetDefaults()
    if args or kwargs:
      self._Init(args, kwargs)

  def __eq__(self, other):
    if self.tag != other.tag:
      return False

    for name in self.FIELDS:
      left = getattr(self, name)
      right = getattr(other, name)
      if left != right:
        return False

    return True

  def _SetDefaults(self):
    for name in self.FIELDS:
      #print("%r wasn't assigned" % name)
      desc = self.DESCRIPTOR_LOOKUP[name]
      # item_desc = desc.desc
      if isinstance(desc, asdl.MaybeType):
        self.__setattr__(name, None)  # Maybe values can be None
      elif isinstance(desc, asdl.ArrayType):
        self.__setattr__(name, [])

  def _Init(self, args, kwargs):
    for i, val in enumerate(args):
      name = self.FIELDS[i]
      self.__setattr__(name, val)

    for name, val in kwargs.items():
      if self._assigned[name]:
        raise AssertionError('Duplicate assignment of field %r' % name)
      self.__setattr__(name, val)

    for name in self.FIELDS:
      if not self._assigned[name]:
        # If anything was set, then required fields raise an error.
        raise ValueError("Field %r is required and wasn't initialized" % name)

  def CheckUnassigned(self):
    """See if there are unassigned fields, for later encoding."""
    unassigned = []
    for name in self.FIELDS:
      if not self._assigned[name]:
        desc = self.DESCRIPTOR_LOOKUP[name]
        if not isinstance(desc, asdl.MaybeType):
          unassigned.append(name)
    if unassigned:
      raise ValueError("Fields %r were't be assigned" % unassigned)

  def __setattr__(self, name, value):
    if name == '_assigned':
      self.__dict__[name] = value
      return
    try:
      desc = self.DESCRIPTOR_LOOKUP[name]
    except KeyError:
      raise AttributeError('Object of type %r has no attribute %r' %
                           (self.__class__.__name__, name))
    if False:  # Disable type checking for now
    #if not _CheckType(value, desc):
      raise AssertionError("Field %r should be of type %s, got %r" %
                           (name, desc, value))

    self._assigned[name] = True  # check this later when encoding
    self.__dict__[name] = value

  def __repr__(self):
    #import pprint
    #return '<%s %s>' % (self.__class__.__name__, pprint.pformat(self.__dict__))
    f = io.StringIO()
    tree = fmt.MakeTree(self)
    fmt.PrintTree(tree, f)
    return f.getvalue()

  # For backward compatibility.  TODO: Get rid of this.
  def DebugString(self):
    return self.__repr__()


def _MakeFieldDescriptors(module, fields):
  desc_lookup = {}
  for f in fields:
    # look up type by name
    primitive_desc = asdl.DESCRIPTORS_BY_NAME.get(f.type)

    desc = primitive_desc or module.types[f.type]
    # It's either a primitive type or sum type
    if primitive_desc is None:
      assert (isinstance(desc, asdl.Sum) or
              isinstance(desc, asdl.Product)), desc

    # Wrap descriptor here.  Then we can type check.
    # And then encode too.
    assert not (f.opt and f.seq), f
    if f.opt:
      desc = asdl.MaybeType(desc)

    if f.seq:
      desc = asdl.ArrayType(desc)

    desc_lookup[f.name] = desc

  class_attr = {
      'FIELDS': [f.name for f in fields],
      'DESCRIPTOR_LOOKUP': desc_lookup,
  }
  return class_attr


def MakeTypes(module, root):
  """
  Args:
    module: asdl.Module
    root: an object/package to add types to
  """
  for defn in module.dfns:
    typ = defn.value

    #print('TYPE', defn.name, typ)
    if isinstance(typ, asdl.Sum):
      if asdl.is_simple(typ):
        # An object without fields, which can be stored inline.
        class_attr = {'DESCRIPTOR': typ}  # asdl.Sum
        cls = type(defn.name, (SimpleObj, ), class_attr)
        #print('CLASS', cls)
        setattr(root, defn.name, cls)

        for i, cons in enumerate(typ.types):
          enum_id = i + 1
          name = cons.name
          val = cls(enum_id, cons.name)  # Instantiate SimpleObj subtype
          # Set a static attribute like op_id.Plus, op_id.Minus.
          setattr(cls, name, val)
      else:
        tag_num = {}

        # e.g. for arith_expr
        base_class = type(defn.name, (CompoundObj, ), {})
        setattr(root, defn.name, base_class)

        # Make a type and a enum tag for each alternative.
        for i, cons in enumerate(typ.types):
          tag = i + 1  # zero reserved?
          tag_num[cons.name] = tag  # for enum

          class_attr = _MakeFieldDescriptors(module, cons.fields)
          class_attr['DESCRIPTOR'] = cons
          # TODO: Allow setting these integers.  We're reusing ID 0 for every
          # sum type, but that's OK because fields are strongly typed.
          class_attr['tag'] = tag

          cls = type(cons.name, (base_class, ), class_attr)
          setattr(root, cons.name, cls)

        # e.g. arith_expr_e.Const == 1
        enum_name = defn.name + '_e'
        tag_enum = type(enum_name, (), tag_num)
        setattr(root, enum_name, tag_enum)

    elif isinstance(typ, asdl.Product):
      class_attr = _MakeFieldDescriptors(module, typ.fields)
      class_attr['DESCRIPTOR'] = typ

      cls = type(defn.name, (CompoundObj, ), class_attr)
      setattr(root, defn.name, cls)

    else:
      raise AssertionError(typ)

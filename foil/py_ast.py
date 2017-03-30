#!/usr/bin/env python3
"""
Wrapper for Python.asdl.
"""

import os
import sys

from asdl import py_meta
from asdl import asdl_ as asdl

def _ParseAndMakeTypes(schema_path, root):
  module = asdl.parse(schema_path)

  app_types = {}

  # Check for type errors
  if not asdl.check(module, app_types):
    raise AssertionError('ASDL file is invalid')
  py_meta.MakeTypes(module, root, app_types)


bin_dir = os.path.dirname(os.path.abspath(sys.argv[0]))  # ~/git/oil/bin
schema_path = os.path.join(bin_dir, '../foil/Python.asdl')  # ~/git/oil/osh

root = sys.modules[__name__]

_ParseAndMakeTypes(schema_path, root)

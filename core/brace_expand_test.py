#!/usr/bin/env python3
"""
brace_expand_test.py: Tests for brace_expand.py
"""

import unittest

from core import brace_expand  # module under test
from osh import word_parse_test


# Silly wrapper
def _assertReadWord(*args):
  return word_parse_test._assertReadWord(*args)


class BraceExpandTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def testFoo(self):
    w = _assertReadWord(self, '{a,b,c}')
    brace_expand.BraceDetect(w)

    #w = _assertReadWord(self, '{{a,b}')


if __name__ == '__main__':
  unittest.main()

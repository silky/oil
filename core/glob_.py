#!/usr/bin/env python3
"""
glob_.py
"""

try:
  from core import libc
except ImportError:
  from core import fake_libc as libc

# Pipeline sketch:
#
# data: CompoundWord ->
#       BraceExpand(words, out) uses words.LooksLikeBraceExpansion(w) ->

# data: [CompoundWord] ->
#       ev.EvalCompoundWord()  # does both substitution and splitting 
#                              # should we separate these things?
#                              # because splitting depends on quoting too
#                              # get rid of IsSubst
#       heterogeneous WordPart to homogeneous Value
# data: WordValue!  -> 
#   LooksLikeGlob(word_val) -- echo \? vs ? -- the first is NOT a glob.
#    This is a WordPart like '?'
#
#   WordFramer(ifs).JoinSplitElide(out)
#     Appends to the given array of WordValue
#
# data: WordValue with split_or_elide all false? ->
#
#       globber.Expand() ->
#
# data: argv array

# Key point: none of these algorithms operate on strings?
# - LooksLikeBraceExpansion, BraceExpand: operates on array of WordPart
# - Split(): operates on array of PartValue?
# - LooksLikeGlob(), GlobExpand(): operates on INDIVIDUAL PartValue ?
#   - it has flags

# Splitting happens before globbing:
#
# pat='*.py *.sh'
# echo $pat  # split into two glob patterns, then expand!

# Parts must be glob-escaped separately:
# echo "core"/*.py
# echo "?core"/*.py


class WordValue:
  def __init__(self, parts):
    # Parallel arrays:
    self.parts = []  # PartValue, string or array?
                     # Arrays are the result of evaluating "$@" and "${a[@]}"
    self.split_or_elide = []  # only substitutions
                              # e.g. $a$b should be elided
                              # clear this flag after splitting?
    self.do_glob = []  # literals and substitutions
                       # maybe have a thing to turn it off?

  def ShouldGlob(self):
    """Should the word be passed to glob()?"""
    return any(self.do_glob)

  def ShouldElide(self):
    """Should the word be passed to glob()?"""
    # TODO: all parts empty and unquoted
    return False


# Glob Helpers for WordParts.
# NOTE: Escaping / doesn't work, because it's not a filename character.
# ! : - are metachars within character classes
GLOB_META_CHARS = r'\*?[]-:!'

def GlobEscape(s):
  """
  For SingleQuotedPart, DoubleQuotedPart, and EscapedLiteralPart
  """
  escaped = ''
  for c in s:
    if c in GLOB_META_CHARS:
      escaped += '\\'
    escaped += c
  return escaped


def _GlobUnescape(s):  # used by cmd_exec
  """
  If there is no glob match, just unescape the string.
  """
  unescaped = ''
  i = 0
  n = len(s)
  while i < n:
    c = s[i]
    if c == '\\':
      assert i != n - 1, 'There should be no trailing single backslash!'
      i += 1
      c2 = s[i]
      if c2 in GLOB_META_CHARS:
        unescaped += c2
      else:
        raise AssertionError("Unexpected escaped character %r" % c2)
    else:
      unescaped += c
    i += 1
  return unescaped


class Globber:
  """Expand glob patterns into a list of filenames.

  Issues:

  1. Unicode encoding of file system.  On Unix, filenames are just bytes.  The
    encoding is "out of line"

    Have a global var that will set LOCALE environment variable and other libc
    global options before glob?
    @glob('*.py', encoding='foo')

    Default is utf-8 or what?

    set fs-encoding = 'f'
    echo *.py
    set fs-encoding = 'f'

  2. Telling whether a word looks like a glob or not.

    TODO: Only try to glob if there are any glob metacharacters.
    Or maybe it is a conservative "avoid glob" heuristic?
   
    Non-glob but with glob characters:
    echo ][
    echo []  # empty
    echo []LICENSE  # empty
    echo [L]ICENSE  # this one is good
    So yeah you need to test the validity somehow.
   
    PROBLEM: nullglob forces us to know exactly what's a glob and what's
    not?  Same with faillglob;
    Write a test for nullglob!  It will tell you what is not
   
    Other shells don't need this code -- you can't tell from the outside
    whether they call glob() or not!
   
    No other shells have it, but I want it in oil.  How does bash do the
    detection?

    ANSWER: INTERNAL_GLOB_PATTERN_P in lib/glob/globloop.c
    Tests for ? * a single instance of [], and any instance of 
    +( @( or !(.  And skips over \x
    I don't need to do that because I tokenized.  OK this is good: the
    algorithm is pretty easy.
   
    compiled to internal_glob_pattern_p
    and internal_glob_wpattern_p
    glob_pattern_p
    there is also an unquoted_glob_pattern_p, extglob_pattern_p,
  """
  def __init__(self, exec_opts):
    # TODO: separate into set_opts.glob_opts, and sh_opts.glob_opts?  Only if
    # other shels use the same options as bash though.

    self.noglob = False  # set -f

    # shopt: why the difference?  No command line switch I guess.
    self.dotglob = False  # dotfiles are matched
    self.failglob = False  # no matches is an error
    self.globstar = False  # ** for directories
    # globasciiranges - ascii or unicode char classes (unicode by default)
    # nocaseglob
    self.nullglob = False  # no matches evaluates to empty, otherwise
    # extglob: the !() syntax

    # TODO: Figure out which ones are in other shells, and only support those?
    # - Include globstar since I use it, and zsh has it.

  def Expand(self, argv):
    result = []
    for arg in argv:
      try:
        #g = glob.glob(arg)  # Bad Python glob
        # PROBLEM: / is significant and can't be escaped!  Hav eto avoid globbing it.
        g = libc.glob(arg)
      except Exception as e:
        # - [C\-D] is invalid in Python?  Regex compilation error.
        # - [:punct:] not supported
        print("Error expanding glob %r: %s" % (arg, e))
        raise
      #print('G', arg, g)

      if g:
        result.extend(g)
      else:
        u = _GlobUnescape(arg)
        result.append(u)
    return result

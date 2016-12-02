#!/bin/bash
#
# Miscellaneous scripts that don't belong elsewhere.
#
# Usage:
#   ./run.sh <function name>

set -o nounset
set -o pipefail
set -o errexit

# TODO: Move this to make file
build-ast() {
  mkdir -p _gen

  # Extract AST spec from source code.
  #bin/oil print-ast > _gen/oil-ast.txt

  # Print it
  bin/oil compile run.sh foo
  #
  tools/gen_ast.py --lang cpp _gen/oil-ast.txt > _gen/oil-ast.cpp

  # Hm I'm not sure if this has enough info?  There is some layout information
  # in the AST.
  # Yeah it doesn't associate Id with node.
  # Or maybe you should generate
  # Hm yeah I guess you should do that.
  #
  # Maybe you can generate one node per LAYOUT in C++, but one node per ID in
  # ML.  Yeah I think that makes sense.  Hm.

  # PROBLEM WITH ML: How do you encode comments/whitespace?
  # SourceLocation?

  tools/gen_ast.py --lang ml _gen/oil-ast.txt > _gen/oil-ast.cpp
}

make-bin-links() {
  mkdir -p bin
  for link in oil osh sh wok boil; do
    ln -s -f --verbose oil.py bin/$link
  done
}

"$@"

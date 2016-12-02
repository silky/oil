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
  bin/oil compile run.sh foo
  tools/gen_ast.py
}

make-bin-links() {
  mkdir -p bin
  for link in oil osh sh wok boil; do
    ln -s -f --verbose oil.py bin/$link
  done
}

"$@"

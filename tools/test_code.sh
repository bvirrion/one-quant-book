#!/usr/bin/env bash
# Run every code test of the book (or of one chapter: tools/test_code.sh markets-1/07-pnl).
#   python : ruff + pytest on code/<ch>/           (tests/test_*.py)
#   C++    : every code/<ch>/cpp/*_test.cpp built with -std=c++20 -Wall -Wextra -Werror and run
#   Rust   : cargo clippy -D warnings + cargo test in every dir holding a Cargo.toml
#   LaTeX  : every \omcode{path}{a}{b} points at an existing file and a..b is inside it
set -uo pipefail
cd "$(dirname "$0")/.."
# Many small matrix products: BLAS threads only add overhead (a 12-second model took 6.5 minutes with them).
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
PY=.venv/bin/python
sel="${1:-}"
roots=()
if [ -n "$sel" ]; then roots=("code/$sel"); else roots=(code); fi
fail=0
say(){ printf '\n== %s\n' "$*"; }

say "ruff"
$PY -m ruff check -q "${roots[@]}" || fail=1

say "pytest"
# NOT `find | grep -q .`: under pipefail grep exits at the first line, find dies
# of SIGPIPE, the pipeline is "false" and the suite was silently skipped.
npy=$(find "${roots[@]}" -name 'test_*.py' | wc -l)
if [ "$npy" -gt 0 ]; then
  echo "$npy test files"
  $PY -m pytest -q -p no:cacheprovider "${roots[@]}" || fail=1
else echo "(no python tests)"; fi

say "C++"
n=0
while IFS= read -r t; do
  n=$((n+1)); d=$(dirname "$t"); mkdir -p "$d/bin"; exe="$d/bin/$(basename "${t%.cpp}")"
  # timeout: a hung lock-free stress test must fail, not hang CI (Book 13).
  if g++ -std=c++20 -O2 -Wall -Wextra -Werror -I"$d" "$t" -o "$exe" && timeout 600 "$exe"; then
    echo "ok   $t"; else echo "FAIL $t"; fail=1; fi
done < <(find "${roots[@]}" -name '*_test.cpp' | sort)
[ $n -eq 0 ] && echo "(no C++ tests)"

say "Rust"
n=0
while IFS= read -r c; do
  n=$((n+1)); d=$(dirname "$c")
  if (cd "$d" && cargo clippy -q --all-targets -- -D warnings && cargo test 2>&1 | grep -E "^test result|FAILED|panicked"); then
    echo "ok   $d"; else echo "FAIL $d"; fail=1; fi
done < <(find "${roots[@]}" -name Cargo.toml -not -path '*/target/*' | sort)
[ $n -eq 0 ] && echo "(no Rust crates)"

say "\\omcode ranges"
$PY tools/check_omcode.py "$sel" || fail=1

say "module names"
$PY tools/check_module_names.py || fail=1

say "chart CSVs"
$PY tools/check_figdata.py || fail=1

[ $fail -eq 0 ] && echo && echo "TEST-CODE: GREEN" || { echo; echo "TEST-CODE: RED"; exit 1; }

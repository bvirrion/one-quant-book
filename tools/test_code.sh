#!/usr/bin/env bash
# Run every code test of the book (or of one chapter: tools/test_code.sh markets-1/07-pnl).
# OQB_TESTS=fast (make test-fast, CI) skips the tests marked `reference`: they reproduce a number the
# book prints, and their digits are exact only on the machine that wrote them.
#   python : ruff + pytest on code/<ch>/           (tests/test_*.py)
#   C++    : every code/<ch>/cpp/*_test.cpp built with -std=c++20 -Wall -Wextra -Werror and run
#   Rust   : cargo clippy -D warnings + cargo test in every dir holding a Cargo.toml
#   LaTeX  : every \omcode{path}{a}{b} points at an existing file and a..b is inside it
set -uo pipefail
cd "$(dirname "$0")/.."
# Many small matrix products: BLAS threads only add overhead (a 12-second model took 6.5 minutes with them).
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}" OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
# Same floating-point kernels on every x86-64 machine as on the one that wrote the numbers (Haswell-class
# AVX2, no AVX-512; each pin is what this machine picks anyway): other kernels sum in another order.
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-Haswell}" ATEN_CPU_CAPABILITY="${ATEN_CPU_CAPABILITY:-avx2}" \
  ONEDNN_MAX_CPU_ISA="${ONEDNN_MAX_CPU_ISA:-AVX2}" \
  NPY_DISABLE_CPU_FEATURES="${NPY_DISABLE_CPU_FEATURES-AVX512F AVX512CD AVX512_KNL AVX512_KNM AVX512_SKX AVX512_CLX AVX512_CNL AVX512_ICL}"
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
  # One pytest process per chapter (or firm component): memory is freed between them. One process for a
  # whole book peaked at 15.6 GB (strategies-1) against 3.9 GB for its largest chapter, and CI runners have 7.
  mark=(); [ "${OQB_TESTS:-all}" = fast ] && mark=(-m "not reference")
  npass=0; nbad=0
  while IFS= read -r d; do
    out=$($PY -m pytest -q -p no:cacheprovider "${mark[@]}" "$d" 2>&1); rc=$?
    # 5 = every test of the directory deselected: nothing ran, nothing failed.
    if [ $rc -eq 0 ] || [ $rc -eq 5 ]; then
      npass=$((npass+1)); echo "ok   $d: $(tail -n 1 <<<"$out")"
    else
      nbad=$((nbad+1)); fail=1; echo "FAIL $d"; echo "$out"
    fi
  done < <(find "${roots[@]}" -type d -name tests -printf '%h\n' | sort -u)
  echo "pytest: $npass directories green, $nbad failing"
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

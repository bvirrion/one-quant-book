#!/usr/bin/env bash
# Quality gates (WRITING_A_QUANT_BOOK.md section 7).
#   tools/gates.sh chapter <slug>/<NN-chapter>   per-chapter gates (no LaTeX build)
#   tools/gates.sh sources <slug>/<NN-chapter>   dated boxes <-> ledger, ledger rows complete
#   tools/gates.sh firms   <slug>/<NN-chapter>   named-firm lines <-> ledger
#   tools/gates.sh log [slug]                    0 errors / 0 undefined / 0 overfull (default: every book)
#   tools/gates.sh book <slug>                   all of the above over every chapter + book-level checks
set -uo pipefail
cd "$(dirname "$0")/.."
# slug -> book number; the entry file is found from the number.
declare -A BOOKNO=([markets-1]=1 [markets-2]=2 [markets-3]=3 [methods]=4 [derivatives]=5
  [rates-credit-risk]=6 [research]=7 [strategies-1]=8 [strategies-2]=9 [microstructure]=10
  [hft]=11 [ml]=12 [low-latency]=13 [networks]=14 [platforms]=15 [firm]=16 [industry]=17 [interviews]=18)
entry(){ local f; for f in one_quant_book_"$(printf %02d "${BOOKNO[$1]}")"_*.tex; do echo "${f%.tex}"; return; done; }
fail=0
bad(){ echo "  FAIL: $*"; fail=1; }

sources(){ local ch="$1" C="parts/$1.tex" Ld="sources/$1.md"
  [ -f "$Ld" ] || { bad "no ledger $Ld"; return; }
  # every dated box label is cited in the ledger
  grep -o 'label{dat:[^}]*}' "$C" | sed 's/label{//;s/}//' | while read -r d; do
    grep -qF "$d" "$Ld" || echo "  FAIL: dated box $d has no ledger row"; done | tee /tmp/.g$$ ; [ -s /tmp/.g$$ ] && fail=1
  # every dated box has a dat: label
  local nb nl; nb=$(grep -c 'begin{dated}' "$C"); nl=$(grep -c 'label{dat:' "$C")
  [ "$nb" = "$nl" ] || bad "$nb dated boxes but $nl dat: labels in $C"
  # every ledger fact row (starts with '| F') has a URL and an access date
  awk -F'|' '/^\| *F[0-9]+/{ if ($0 !~ /https?:\/\//) print "  FAIL: no URL: " $2; if ($0 !~ /20[0-9][0-9]-[01][0-9]-[0-3][0-9]/) print "  FAIL: no access date: " $2 }' "$Ld" | tee /tmp/.g$$; [ -s /tmp/.g$$ ] && fail=1
  rm -f /tmp/.g$$
  echo "  sources: $(grep -c '^| *F[0-9]' "$Ld") ledger rows, $nb dated boxes"
}

firms(){ local C="parts/$1.tex" S="parts/${1%/*}/solutions/${1##*/}.tex" Ld="sources/$1.md"
  [ -f tools/firm_names.txt ] || return 0
  while IFS= read -r name; do
    case "$name" in ''|'#'*) continue;; esac
    # -w: whole words only ("Virtu" must not fire on "Virtual")
    if grep -qwF -- "$name" "$C" "$S" 2>/dev/null; then
      grep -qF -- "$name" "$Ld" 2>/dev/null || bad "'$name' named in ${1} but absent from its ledger"
    fi
  done < tools/firm_names.txt
}

chapter(){ local ch="$1" C="parts/$1.tex" S="parts/${1%/*}/solutions/${1##*/}.tex"
  echo "== $ch"
  [ -f "$C" ] && [ -f "$S" ] || { bad "missing $C or $S"; return; }
  d=$(diff <(grep -o 'label{\(exo\|pb\|iq\):[^}]*}' "$C" | sed 's/label{//;s/}//') \
           <(grep -o 'begin{solution}{[^}]*}' "$S" | sed 's/begin{solution}{//;s/}//'))
  [ -z "$d" ] || { bad "exercise/solution mismatch"; echo "$d" | sed 's/^/    /'; }
  q=$(cat "$C" "$S" | grep -c '"'); [ "$q" = 0 ] || bad "$q lines with straight quotes"
  o=$(grep -o '``' "$C" "$S" | wc -l); c=$(grep -o "''" "$C" "$S" | wc -l); [ "$o" = "$c" ] || bad "quote balance: $o open, $c close"
  grep -n '\.\.\.' "$C" "$S" | grep -v '\\dots\|\\foreach' && bad "drafty ..."
  grep -n 'begin{lstlisting}' "$C" "$S" && bad "inline lstlisting"
  grep -n 'end{[a-z]*>' "$C" "$S" && bad "\\end{...> typo"
  grep -n 'omterm' "$C" "$S" >/dev/null; true
  e=$(grep -c 'begin{exercise}' "$C"); [ "$e" = 8 ] || bad "$e exercises (want 8)"
  s1=$(grep -c 'begin{exercise}\[\$\\star\$\]' "$C"); s2=$(grep -c 'begin{exercise}\[\$\\star\\star\$\]' "$C"); s3=$(grep -c 'begin{exercise}\[\$\\star\\star\\star\$\]' "$C")
  [ "$s1/$s2/$s3" = "3/3/2" ] || bad "star ramp $s1/$s2/$s3 (want 3/3/2)"
  p=$(grep -c 'begin{problem}' "$C"); [ "$p" = 1 ] || bad "$p weekend problems (want 1)"
  i=$(grep -c 'begin{interviewq}' "$C"); { [ "$i" -ge 5 ] && [ "$i" -le 8 ]; } || bad "$i interview questions (want 5-8)"
  grep -q 'begin{omsources}' "$C" || bad "no omsources"
  grep -q 'label{tut:' "$C" || bad "no tutorial"
  grep -q 'label{bld:' "$C" || bad "no build"
  t="code/$ch/tests/test_solutions.py"; [ -f "$t" ] || bad "no $t"
  sources "$ch"; firms "$ch"
  echo "  lines: body $(wc -l < "$C"), solutions $(wc -l < "$S"); figures $(grep -c 'begin{omfigure}' "$C"); listings $(grep -c 'omcode{' "$C"); dated $(grep -c 'begin{dated}' "$C")"
}

# tools/gates.sh log [slug]  -- one book's log, or every built book's
log(){ local ents
  if [ -n "${1:-}" ]; then ents=("$(entry "$1")"); else ents=(); for f in one_quant_book_*.tex; do ents+=("${f%.tex}"); done; fi
  for E in "${ents[@]}"; do local L="build/$E.log"
    [ -f "$L" ] || { bad "no log $L"; continue; }
    e=$(grep -c '^!' "$L"); u=$(grep -ci 'undefined' "$L"); o=$(grep -c 'Overfull' "$L")
    echo "== log $E: errors $e / undefined $u / overfull $o"
    [ "$e/$u/$o" = "0/0/0" ] || fail=1
  done
}

case "${1:-}" in
  chapter) chapter "$2";;
  sources) sources "$2";;
  firms) firms "$2";;
  log) log "${2:-}";;
  book)
    for f in parts/"$2"/[0-9]*.tex; do chapter "$2/$(basename "${f%.tex}")"; done
    echo "== duplicate labels"; grep -rho 'label{[^}]*}' parts/"$2"/ | sort | uniq -d | sed 's/^/  DUP /' | tee /tmp/.d$$; [ -s /tmp/.d$$ ] && fail=1; rm -f /tmp/.d$$
    echo "== terms defined twice (whole series)"
    # perl -0777: a \emph{…}\index{…} pair may span a line break (46 of Book 1-2's
    # 555 did; a line-based grep missed them all -- found by the Book 3 agent).
    harvest(){ perl -0777 -ne 'while(/\\emph\{([^}]*)\}\s*\\index\{([^}]*)\}/g){($t=$2)=~s/\s+/ /g; print "$t\n"}' parts/*/[0-9]*.tex; }
    nt=$(harvest | wc -l); echo "  $nt definitions harvested over $(ls -d parts/*/ | wc -l) books"
    [ "$nt" -gt 0 ] || bad "harvested no definitions"
    harvest | sort | uniq -d | sed 's/^/  TWICE /' | tee /tmp/.d$$; [ -s /tmp/.d$$ ] && fail=1; rm -f /tmp/.d$$
    echo "== problem numbering"; .venv/bin/python tools/check_problem_numbering.py parts/"$2" || fail=1
    echo "== term links"; .venv/bin/python tools/link_defined_terms.py --book "${BOOKNO[$2]}" --check | tail -1 | grep -q '^CHECK' && echo "  links match the config" || { echo "  STALE links"; fail=1; }
    log "$2";;
  *) sed -n 2,8p "$0"; exit 2;;
esac
[ $fail -eq 0 ] && echo "GATES: GREEN" || { echo "GATES: RED"; exit 1; }

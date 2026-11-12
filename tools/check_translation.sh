#!/bin/bash
# Structural gate for a translated edition.
#
#   bash tools/check_translation.sh markets-1 fr      # one book slug, one language
#   bash tools/check_translation.sh                   # every year x every
#                                                     # language present on disk
#
# Ported from One Earth and Space Sciences Book (2026-11-09) for the French
# editions of Books 1-5; gates 12-13 (chemistry) became the code twin.
#
# A clean pdflatex build proves almost nothing about a translation: \ominput
# silently falls back to the English body when a translated file is missing,
# and \omstr expands to nothing when a lang key is missing. Both failures
# build green. So completeness and structure are checked here, against the
# English source, file by file.
#
# Needs bash (process substitution), not sh.
cd "$(dirname "$0")/.." || exit 2

fail=0
bad() { fail=1; printf '  FAIL  %-44s %s\n' "$1" "$2"; }

check_year_lang() {
  local year=$1 lang=$2
  local dir="parts/$year" tdir="parts/$year/$lang"
  local sdir="parts/$year/solutions" tsdir="parts/$year/solutions/$lang"

  echo "== $year / $lang =="

  if [ ! -d "$tdir" ]; then
    bad "$year/$lang" "no translation directory"
    return
  fi

  # ---- 1. Completeness. The check a green build will NOT give you. --------
  for f in "$dir"/[0-9]*.tex; do
    b=$(basename "$f")
    [ -f "$tdir/$b" ]  || bad "chapter missing"   "$tdir/$b"
    # (an interview book's ch. 1 has no answers, so no English solutions file: none expected then)
    [ ! -f "$sdir/$b" ] || [ -f "$tsdir/$b" ] || bad "solutions missing" "$tsdir/$b"
  done
  for f in "$tdir"/[0-9]*.tex; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    [ -f "$dir/$b" ] || bad "extra chapter, no English twin" "$tdir/$b"
  done

  # ---- 2..4. Per-file structure, against the English original. ------------
  for f in "$dir"/[0-9]*.tex; do
    b=$(basename "$f")
    local t="$tdir/$b" ts="$tsdir/$b"
    [ -f "$t" ] || continue

    # 2. Labels: identical set, identical order. Never translated.
    if ! diff -q <(grep -o 'label{[^}]*}' "$f") \
                 <(grep -o 'label{[^}]*}' "$t") >/dev/null 2>&1; then
      bad "labels differ from English" "$b"
      diff <(grep -o 'label{[^}]*}' "$f") <(grep -o 'label{[^}]*}' "$t") \
        | head -6 | sed 's/^/          /'
    fi

    # 3. Exercise/problem/interview-question <-> solution parity (quant
    #    solutions answer exo:, pb: and iq: keys, in that order).
    if [ -f "$ts" ]; then
      if ! diff -q \
          <(grep -o 'label{\(exo\|pb\|iq\):[^}]*}' "$t" | sed 's/label{//;s/}//') \
          <(grep -o 'begin{solution}{[^}]*}'   "$ts" | sed 's/begin{solution}{//;s/}//') \
          >/dev/null 2>&1; then
        bad "exercise/solution keys mismatch" "$b"
      fi
    fi

    # 4. Environment and figure census must equal English: nothing dropped,
    #    nothing invented, figures preserved.
    for env in definition theorem proposition lemma corollary example remark \
               method notation exercise problem proof tikzpicture omfigure \
               axis tabular dated scope omsources tutorial tutsteps build \
               interviewq strategyfile predictorcard groupplot table; do
      ne=$(grep -c "begin{$env}" "$f")
      nt=$(grep -c "begin{$env}" "$t")
      [ "$ne" = "$nt" ] || bad "$env count ${ne}->${nt}" "$b"
      if [ -f "$ts" ]; then
        se=$(grep -c "begin{$env}" "$sdir/$b")
        st=$(grep -c "begin{$env}" "$ts")
        [ "$se" = "$st" ] || bad "$env count ${se}->${st} (solutions)" "$b"
      fi
    done
  done

  # ---- 5. Hygiene. -------------------------------------------------------
  if grep -rqn 'end{[a-z]*>' "$tdir" "$tsdir" 2>/dev/null; then
    bad "\\end{...> typo class" "$year/$lang"
  fi
  # "samples at={1,...,16}" is pgfplots syntax, not drafty prose; so is
  # \pgfplotsinvokeforeach{-40,-20,...,340} (Earth grade-7/03; es agent, 2026-10-25).
  if grep -rn '\.\.\.' "$tdir" "$tsdir" 2>/dev/null \
       | grep -qv '\\dots\|\\ldots\|\\cdots\|\\foreach\|\\pgfplotsinvokeforeach\|samples at\|xtick=\|ytick='; then
    bad "drafty ... in prose (use \\dots)" "$year/$lang"
  fi
  dup=$(grep -rho 'label{[^}]*}' "$tdir" "$tsdir" 2>/dev/null | sort | uniq -d)
  [ -z "$dup" ] || bad "duplicate labels" "$(echo "$dup" | head -3 | tr '\n' ' ')"

  # A line-broken \index{} key. TeX collapses the newline to a space, so the
  # key is RIGHT and the build is green -- but the entry splits in two the
  # moment the same term is also written unbroken somewhere, and NOTHING else
  # in this project compares index-key contents: the index census counts
  # entries, harvest.py collapses whitespace, and no prose gate reduces a key
  # to visible text. The English canon of Book 3 carried 18 of these and the
  # Spanish edition 2; the French agent found its own four only by an ad-hoc
  # scan. Wrapping a translated line is exactly what creates them, so this is
  # a translation-time class, not a canon-only one.
  nbi=$(grep -rc '\\index{[^}]*$' "$tdir" "$tsdir" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  [ "$nbi" = 0 ] || bad "line-broken \\index{} key ($nbi)" \
    "$(grep -rln '\\index{[^}]*$' "$tdir" "$tsdir" 2>/dev/null | head -3 | tr '\n' ' ')"

  # ---- 6. Encoding: UTF-8, and no TeX accent escapes (\'e, \`a).
  #         Books 1/2 mixed the two and it cost their term configs a double
  #         spelling of every accented word. Do not repeat it here.
  if grep -rqn "\\\\['\`^\"]{\?[aeiouAEIOU]" "$tdir" "$tsdir" 2>/dev/null; then
    bad "TeX accent escapes (use UTF-8)" "$year/$lang"
  fi

  # ---- 7. Script-specific prose hygiene. Gates 5 and 6 are Latin-oriented
  #         and score NOTHING on a non-Latin target: a Hindi or Arabic tree
  #         can pass every gate above and still be the raw machine
  #         translation it started as. Arabic additionally hides bidi control
  #         characters and Arabic presentation forms no Latin gate can see.
  if [ "$lang" = "hi" ]; then
    python3 tools/check_hindi_prose.py --quiet "$tdir" "$tsdir" \
      || bad "Devanagari prose hygiene" "$year/$lang"
  fi
  if [ "$lang" = "ar" ]; then
    python3 tools/check_arabic_prose.py --quiet "$tdir" "$tsdir" \
      || bad "Arabic prose hygiene" "$year/$lang"
  fi

  # ---- 8. Indonesian prose hygiene -- the opposite problem to gate 7.
  #         Indonesian is written in the SAME alphabet as the source, so a
  #         forgotten sentence, TikZ node, \text{...} or optional title is
  #         indistinguishable from correct output: a tree can be structurally
  #         perfect, build clean, and still be half English. The gate is a
  #         curated list of English words that are NOT words of Indonesian.
  if [ "$lang" = "id" ]; then
    python3 tools/check_indonesian_prose.py --quiet "$tdir" "$tsdir" \
      || bad "Indonesian prose hygiene" "$year/$lang"
  fi

  # ---- 9. The twin comparison, for every Latin-script target. No word list
  #         can separate an English word from a French one, so this asks a
  #         question needing no per-language knowledge at all: is this
  #         fragment BYTE-IDENTICAL to its English twin and does it contain a
  #         lowercase word? Optional titles, \text{}, TikZ nodes, dup lines.
  case "$lang" in fr|nl|es|pt|id)
    python3 tools/check_latin_prose.py --quiet "$tdir" "$tsdir" \
      || bad "twin-comparison prose gate" "$year/$lang"
  ;; esac

  # ---- 10. Orphan lines: an English source line whose content the previous
  #          sentence's translation ABSORBED, so it fell outside every patch
  #          range and was copied through verbatim -- by design, which is
  #          exactly why no other gate here objects to it.
  python3 tools/check_orphan_lines.py --quiet "$tdir" "$tsdir" \
    || bad "orphan English line" "$year/$lang"

  # ---- 11. The weekend problem's answers must be numbered 1..k for k
  #          questions. That numbering is PROSE: gate 3 compares
  #          \begin{solution}{key} sequences and an answer paragraph has no
  #          key, id_apply compares a translation against its twin so a defect
  #          in BOTH is invisible, and every prose gate asks whether words are
  #          foreign, never whether a run of integers is complete. Book 3's
  #          ENGLISH canon shipped 25 questions with 24 answers and three
  #          translators found it by reading. Proposed by the French Book 3
  #          agent, 2026-09-06. It cannot see a permutation -- see the
  #          script's docstring, which says so explicitly.
  python3 tools/check_problem_numbering.py --quiet "$tdir" \
    || bad "weekend-problem answer numbering" "$year/$lang"

  # ---- 12. Code twin (One Quant Book): the ordered \omcode path/lines, the
  #          dated-box dates and the \texttt identifiers of every file must
  #          equal its English twin's, ON DISK. id_apply checks them at write
  #          time; a post-write edit is seen by nothing else, and a changed
  #          line number prints the wrong lines of a tested file in a green build.
  python3 tools/check_quant_twin.py --quiet "$tdir" "$tsdir" \
    || bad "code twin (\\omcode / dated / \\texttt)" "$year/$lang"
}

if [ $# -eq 2 ]; then
  check_year_lang "$1" "$2"
else
  for year in markets-1 markets-2 markets-3 methods derivatives \
              rates-credit-risk research strategies-1 strategies-2 \
              microstructure hft ml low-latency networks platforms desk \
              industry interviews-1 interviews-2 interviews-3; do
    for lang in fr nl es pt hi ar id; do
      # Skip years that have no translation directory yet.
      [ -d "parts/$year/$lang" ] || continue
      check_year_lang "$year" "$lang"
    done
  done
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "TRANSLATION GATE: FAILED"
  exit 1
fi
echo "TRANSLATION GATE: PASSED"

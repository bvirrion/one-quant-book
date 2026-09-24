#!/usr/bin/env bash
# tools/figpage.sh "<a few words of the caption>" [out.png]
# Finds the page carrying those words and renders that page alone at 130 dpi.
# Book 1 by default; OQB_BOOK=2 tools/figpage.sh ... for another book.
set -euo pipefail
cd "$(dirname "$0")/.."
pdf=$(ls build/one_quant_book_"$(printf %02d "${OQB_BOOK:-1}")"_*.pdf)
words="$1"; out="${2:-/tmp/figpage}"
n=$(pdfinfo "$pdf" | awk '/^Pages/{print $2}')
for p in $(seq 1 "$n"); do
  if pdftotext -f "$p" -l "$p" "$pdf" - | tr '\n' ' ' | grep -qF "$words"; then
    pdftoppm -png -r 130 -f "$p" -l "$p" -singlefile "$pdf" "${out%.png}"
    echo "page $p -> ${out%.png}.png"; exit 0
  fi
done
echo "not found: $words" >&2; exit 1

# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

`one-quant-book/` — the **One Quant Book** series of the One Course project:
eighteen English-only LaTeX books covering quantitative finance end to end
(markets, methods, derivatives, risk, research, strategies, microstructure,
HFT, machine learning, low-latency software, networks, platforms, the firm,
the industry, interviews).

**Status (2026-09-24): Books 1 and 2 are written; Books 3–18 are outline only.**
*One Quant Book 1 — Markets I: The Ecosystem and Exchange-Traded Markets*
(`one_quant_book_01_markets_1.tex`, slug `markets-1`, label prefix `m1`):
31 chapters, 374 pages, 121 figures, 78 listings included from tested files,
49 dated boxes, 165 web-verified ledger rows, 1,647 term links.
*One Quant Book 2 — Markets II: Rates, FX and Credit*
(`one_quant_book_02_markets_2.tex`, slug `markets-2`, label prefix `m2`):
31 chapters in six Parts (money and bonds, swaps and beyond, FX, credit,
access, craft), 363 pages, 126 figures, 73 listings, 37 dated boxes, 226
web-verified ledger rows, 1,388 term links; three running-project components
in C++20 and Rust as well as Python (`bond`, `cds`, `pblimits`).
Both books: gates 0 errors / 0 undefined / 0 overfull, `tools/gates.sh book
markets-1` and `markets-2` green (the series-wide "defined twice" check covers
both), `make test-code` green (670 Python tests, seven C++20 and seven Rust
builds), `make figdata` reproduces every chart CSV. Uncommitted.
The bootstrap exists: `styles/onequant.sty`, `Makefile`, `tools/` (gates,
term linker, figure cropper, code and CSV checks, `omcode_ends.py`), `.venv`,
CI. The running project lives in `code/firm/` (61 components). Working notes:
`sources/markets-1/PROGRESS.md`, `sources/markets-2/PROGRESS.md`.

## Commands

```sh
make                          # build the book(s) into build/
make test-code                # ruff + pytest + g++ -std=c++20 + cargo + listing ranges + chart CSVs
make figdata                  # regenerate every chart CSV (must leave no diff)
tools/gates.sh chapter markets-2/NN-slug
tools/gates.sh book markets-2 # all chapters + duplicate labels + terms defined twice + problem numbering + links + log
python3 tools/link_defined_terms.py --book 2 --unwrap --apply && python3 tools/link_defined_terms.py --book 2 --apply
OQB_BOOK=2 .venv/bin/python tools/figcrop.py "Figure 23.4." out.png   # then READ the image (default book 1)
.venv/bin/python tools/omcode_ends.py markets-2/23                   # first/last line of every listing
```

## Read before doing anything

1. `../CLAUDE.md` and `../book_style.md` — workspace rules and the family
   style.
2. `OUTLINE.md` — premises, the eighteen books, the running project, reading
   paths; `outline/*.md` — chapters, summaries, page budgets per book.
3. `WRITING_A_QUANT_BOOK.md` — **how to write one of the books**: what
   changes from the family style, repo layout and label prefixes, the
   bootstrap, the four-phase workflow, per-item rules (procedure / checklist /
   exit condition), quality gates, known traps.

## Rules that never change

- Never create git commits; leave the working tree for the user.
- No subagents when writing a book.
- A model's memory is not a source: every checkable external fact goes
  through the source ledger; volatile facts live in `dated` boxes.
- A practice is attributed to a named firm only with a citable public source.
- No code is printed unless it is included from a tested file.
- Every title starts "One Quant Book N — ".

# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

`one-quant-book/` — the **One Quant Book** series of the One Course project:
eighteen English-only LaTeX books covering quantitative finance end to end
(markets, methods, derivatives, risk, research, strategies, microstructure,
HFT, machine learning, low-latency software, networks, platforms, the firm,
the industry, interviews).

**Status (2026-09-25): Books 1–9 are written; Books 10–18 are outline only.**
Books 1–6 are committed; Books 7 (Research Craft), 8 (Strategies I: Equities and
Futures) and 9 (Strategies II: Volatility, Relative Value, Macro and the Bank Desks),
written 2026-09-24/25 in the main session, no subagents, per the user's ruling, are
uncommitted. Books 3–6 were written in one parallel batch, one agent per
book (`sources/BATCH_BOOKS_3-6.md`; series definition map
`sources/SERIES_DEFINITIONS.md`; cross-book code interface
`code/firm/INTERFACES.md`).

| # | Entry file | Slug / prefix | Ch. | Pages | Figures | Listings | Dated | Ledger | Links |
|---|---|---|---|---|---|---|---|---|---|
| 1 Markets I | `one_quant_book_01_markets_1.tex` | `markets-1` / `m1` | 31 | 374 | 121 | 78 | 49 | 165 | 1,714 |
| 2 Markets II: Rates, FX, Credit | `one_quant_book_02_markets_2.tex` | `markets-2` / `m2` | 31 | 363 | 126 | 73 | 37 | 226 | 1,388 |
| 3 Markets III: Commodities, Energy, Crypto | `one_quant_book_03_markets_3.tex` | `markets-3` / `m3` | 29 | 332 | 109 | 56 | 79 | 277 | 1,267 |
| 4 Quantitative Methods | `one_quant_book_04_methods.tex` | `methods` / `qm` | 29 | 351 | 118 | 59 | 0 | 253 | 1,739 |
| 5 Derivatives and Volatility | `one_quant_book_05_derivatives.tex` | `derivatives` / `dv` | 28 | 348 | 113 | 70 | 9 | 154 | 1,378 |
| 6 Rates, Credit, XVA and Risk | `one_quant_book_06_rates_credit_risk.tex` | `rates-credit-risk` / `rc` | 29 | 314 | 107 | 55 | 32 | 160 | 824 |
| 7 Research Craft | `one_quant_book_07_research.tex` | `research` / `rs` | 29 | 345 | 86 | 67 | 3 | 177 | 1,306 |
| 8 Strategies I: Equities and Futures | `one_quant_book_08_strategies_1.tex` | `strategies-1` / `s1` | 29 | 330 | 54 | 57 | 13 | 140 | 597 |
| 9 Strategies II: Vol, RV, Macro, Bank Desks | `one_quant_book_09_strategies_2.tex` | `strategies-2` / `s2` | 29 | 333 | 57 | 59 | 5 | 98 | 262 |

Books 1–6: gates 0 errors / 0 undefined / 0 overfull, `make gates` green (the
series-wide "defined twice" check: 1,646 terms, none twice), `make test-code`
green (1,775 Python tests, 19 C++20 and 20 Rust builds, 391 listing ranges), `make figdata` reproduces every chart CSV. Book 7 alone: 0/0/0, 240 Python tests
(115 chapter, 125 firm), figdata reproduced with no diff. Book 8 alone: 0/0/0, 218
Python tests (126 chapter, 92 firm), 118 strategy files, figdata reproduced with no
diff. Book 9 alone: 0/0/0, 226 Python tests (132 chapter, 94 firm), 118 strategy
files, figdata reproduced with no diff; real data only from public-domain or openly
licensed series, derived statistics in `data/strategies-2/` (`LICENSES.md`). Book 4 ch. 1 prints the series
notation (`CONTRIBUTING.md`, "Series notation"). The running project in
`code/firm/` has 174 components (204 with Book 7's thirty, `INTERFACES.md` §4:
backtester levels 1–3, synthetic universe and order book, performance, markouts,
equity risk model, portfolio construction, costs, capacity, workflow; 234 with Book
8's thirty strategy components, §5, including the synthetic futures universe
`synthfut`; 264 with Book 9's thirty, §6, several built on earlier books' engines); Book 5's `pricing` library (Python, core in
C++20 and Rust) is what Book 6's `riskengine` runs on. The bootstrap:
`styles/onequant.sty`, `Makefile`, `tools/` (gates, term linker, figure cropper,
code and CSV checks, `omcode_ends.py`), `.venv` (numpy + pandas, no scipy), CI.
Working notes: `sources/<slug>/PROGRESS.md` per book.

## Commands

```sh
make                          # build the book(s) into build/
make test-code                # ruff + pytest + g++ -std=c++20 + cargo + listing ranges + chart CSVs
make figdata                  # regenerate every chart CSV (must leave no diff)
tools/gates.sh chapter markets-2/NN-slug
tools/gates.sh book markets-2 # (any slug) all chapters + duplicate labels + terms defined twice + problem numbering + links + log
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
- Subagents: at most one per book, at most four books written per batch
  (user rule, 2026-09-24); never one agent per chapter. The main session
  makes every shared-file edit and reconciles the batch.
- A model's memory is not a source: every checkable external fact goes
  through the source ledger; volatile facts live in `dated` boxes.
- A practice is attributed to a named firm only with a citable public source.
- No code is printed unless it is included from a tested file.
- Every title starts "One Quant Book N — ".

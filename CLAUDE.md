# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

`one-quant-book/` — the **One Quant Book** series of the One Course project:
twenty LaTeX books, written in English, covering quantitative finance end to end
(markets, methods, derivatives, risk, research, strategies, microstructure,
HFT, machine learning, low-latency software, networks, platforms, the firm,
the industry, interviews). **Books 1–10 also ship in French** (pilot tier, below); the
other ten are English-only.

**Status (2026-11-03): all twenty books are written.** Books 18, 19 and 20 are the interview books, written 2026-11-02/03
in one parallel batch of three (one Opus 5.5 agent per book), which replaced the old 220-page Book 18: 1,789 new questions, long
linked answers at the back, no lessons. Their rules are `sources/INTERVIEW_BOOKS.md`, their chapters `outline/interviews.md`, their
run file `sources/BATCH_BOOKS_18-20.md`, and their gate `tools/check_interview_book.py`. Books 14–16 were written
2026-09-28/29 in one parallel batch of three, one agent per book (user rule for Books 14–18: at most three
books at a time, batches {14, 15, 16} then {17, 18}, both done 2026-09-28/29; `sources/BATCH_BOOKS_14-16.md`, `sources/BATCH_BOOKS_17-18.md`).
Book 16's slug is `desk`, not `firm` (`code/firm/` is the running project).
Books 1–9 are committed (7–9, written 2026-09-24/25 in the main session with no
subagents per the user's ruling, in 2322893). **Books 10–13 were written 2026-09-25/26 in
one parallel batch, one agent per book** (committed as PP-114) (`sources/BATCH_BOOKS_10-13.md`;
the exchange simulator all four share, `firm.exchsim`, is specified in
`code/firm/INTERFACES.md` §7 and documented in `code/firm/exchsim/PROTOCOL.md` and `STATUS.md`). Books 3–6 were written in one parallel batch, one agent per
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
| 10 Microstructure and Execution | `one_quant_book_10_microstructure.tex` | `microstructure` / `mx` | 28 | 303 | 70 | 55 | 14 | 178 | 720 |
| 11 Market Making and HFT | `one_quant_book_11_hft.tex` | `hft` / `hf` | 29 | 329 | 68 | 59 | 19 | 118 | 361 |
| 12 Machine Learning for Markets | `one_quant_book_12_ml.tex` | `ml` / `ml` | 29 | 348 | 58 | 87 | 3 | 168 | 1,000 |
| 13 Low-Latency Software | `one_quant_book_13_low_latency.tex` | `low-latency` / `ll` | 26 | 314 | 72 | 80 | 13 | 120 | 606 |
| 14 Networks, Hardware, Infrastructure | `one_quant_book_14_networks.tex` | `networks` / `nw` | 29 | 349 | 96 | 65 | 40 | 220 | 685 |
| 15 Research, Data and Risk Platforms | `one_quant_book_15_platforms.tex` | `platforms` / `pl` | 30 | 367 | 110 | 103 | 27 | 122 | 702 |
| 16 The Desk and the Firm | `one_quant_book_16_desk.tex` | `desk` / `fm` | 30 | 347 | 108 | 40 | 32 | 182 | 854 |
| 17 The Industry: Firms, Roles and Careers | `one_quant_book_17_industry.tex` | `industry` / `in` | 30 | 339 | 86 | 38 | 52 | 293 | 620 |
| 18 Interviews I: Maths, Probability and Speed | `one_quant_book_18_interviews_1.tex` | `interviews-1` / `iv1` | 33 | 393 | 11 | 0 | 2 | 20 | 0 |
| 19 Interviews II: Markets, Trading Games and the Final Round | `one_quant_book_19_interviews_2.tex` | `interviews-2` / `iv2` | 21 | 348 | 0 | 0 | 11 | 65 | 0 |
| 20 Interviews III: Code | `one_quant_book_20_interviews_3.tex` | `interviews-3` / `iv3` | 9 | 391 | 0 | 399 | 0 | 239 | 0 |

Books 1–6: gates 0 errors / 0 undefined / 0 overfull, `make gates` green (the
series-wide "defined twice" check: 1,646 terms, none twice), `make test-code`
green (1,775 Python tests, 19 C++20 and 20 Rust builds, 391 listing ranges), `make figdata` reproduces every chart CSV. Book 7 alone: 0/0/0, 240 Python tests
(115 chapter, 125 firm), figdata reproduced with no diff. Book 8 alone: 0/0/0, 218
Python tests (126 chapter, 92 firm), 118 strategy files, figdata reproduced with no
diff. Book 9 alone: 0/0/0, 226 Python tests (132 chapter, 94 firm), 118 strategy
files, figdata reproduced with no diff; real data only from public-domain or openly
licensed series, derived statistics in `data/strategies-2/` (`LICENSES.md`). Books 10–13 alone (each checked by the main session): 0/0/0, `tools/gates.sh book` green
(2,753 definitions over 13 books, none twice), per-book `make test-code` green (Book 10: 107
chapter + 108 firm tests, C++20 engine and server, Rust crate; Book 11: 97 + 111, 75 strategy files;
Book 12: 135 + 129, C++20/Rust inference twins; Book 13: 94 + 96, 21 C++20 and 20 Rust components),
figdata reproduced with no diff; Book 13's latency charts are *measured* (`bench_*.py` →
`measured_*.csv` + `.meta`, not regenerated by `make figdata`). Book 4 ch. 1 prints the series
notation (`CONTRIBUTING.md`, "Series notation"). The running project in
`code/firm/` has 174 components (204 with Book 7's thirty, `INTERFACES.md` §4:
backtester levels 1–3, synthetic universe and order book, performance, markouts,
equity risk model, portfolio construction, costs, capacity, workflow; 234 with Book
8's thirty strategy components, §5, including the synthetic futures universe
`synthfut`; 264 with Book 9's thirty, §6, several built on earlier books' engines); Book 5's `pricing` library (Python, core in
C++20 and Rust) is what Book 6's `riskengine` runs on. The bootstrap:
`styles/onequant.sty`, `Makefile`, `tools/` (gates, term linker, figure cropper,
code and CSV checks, `omcode_ends.py`), `.venv` (numpy + pandas; since the Books 10–13 batch also scipy, scikit-learn, LightGBM, statsmodels and PyTorch CPU — user ruling 2026-09-25).
Versions are pinned in `requirements.txt`, which `make venv` installs. To add a library, install it, run the tests, then re-freeze with `python3 -m pip --python .venv/bin/python freeze`.
CI (`.github/workflows/ci.yml`) runs on tags and manual runs only (user ruling 2026-09-26). It uses Python 3.10 with those pins and Rust 1.97.1, and runs one matrix job per code root: `make test-fast`, which skips the tests marked `reference`. Those tests either reproduce the book's exact printed numbers with a full-size run (the heavy chapters), or assert digits that move with the processor's floating-point kernels. Every chapter keeps a small `test_small_runs` or other unmarked test that CI runs (user ruling 2026-09-27: CI tests the code, not the book's digits). A `v*` tag also publishes a GitHub release with all twenty PDFs, each versioned and under its plain name (job `release`, after `code` and `book` pass); a manual run never releases. Chart regeneration is not in CI: `make reproduce` runs everything, `reference` tests and figdata included, on the machine that wrote the book.
Books 14–16 alone (each checked by the main session): 0/0/0, `tools/gates.sh book` green (3,383 definitions
over 16 books, none twice), per-book `make test-code` green (Book 14: 122 chapter + 102 firm tests, C++20 twins,
a Rust crate, SystemVerilog under Verilator 4.038 and Icarus 11, which `make venv` does not install: `apt install
verilator iverilog python3-dev`; Book 15: 128 + 165, DuckDB/Polars/Arrow/pybind11 in the venv, a C++20 and Rust
tick-store reader, 17 measured charts re-measured on a quiet machine; Book 16: 156 + 94), figdata reproduced with
no diff, and every figure checked on its own page. Since 2026-09-29 `onequant.sty` prints pgfplots thousands
with a thin space, and 1,853 hand-typed comma thousands in Books 2, 3, 6, 8–12 and 16 became `\,`.
Books 17–18 alone (each checked by the main session): 0/0/0, `tools/gates.sh book` green (3,540 definitions over
18 books, none twice), per-book `make test-code` green (Book 17: 139 chapter + 99 firm tests; public data only as
small derived tables in `data/industry/` with `LICENSES.md`, firm-level only, pay cells with fewer than ten filings or
three employers suppressed, no individual's pay).
Books 18–20 alone (each checked by the main session): 0/0/0, `check_interview_book.py <slug> --final` and `--cross` green, pytest on
each code root green (753, 620 and 386 tests, each with an originality test against Books 1–17 and the harvest). Book 20 prints what g++ 11.4 does, so its CI job
installs g++-11; Java, .NET, Rust nightly and the local EVM (`build/iv38/node`) are optional and their tests skip without them.
Fresh expert readers have read every answer in the three books, in two rounds on 2026-11-03: 252 defects in 1,789 answers (Book 18 69, Book 19 66, Book 20 117), logged as
fixed. A reader's finding is rechecked by script before it is applied, as some proposed replacement text was itself wrong. `tools/check_omcode.py` does not notice a range that stops inside a block.
Working notes: `sources/<slug>/PROGRESS.md` per book.

**French pilot editions of Books 1–5 (2026-11-09/10).** Made by the pilot method (`../pilot_translation_instruction.md`):
one tool-less Haiku 5.5 call per section (effort medium), but run with five Opus 5.5 coordinator subagents, one per
book, against the pilot method's one-coordinator rule; they made most of the run's ~13 % of a weekly plan.
Self-scored from a 20-passage sample, not read in full: Book 1 88 (403 pp), Book 2 88 (393), Book 3 87 (354), Book 4
88 (372), Book 5 88 (366); all 0/0/0 under TeX Live 2026 and `tools/check_translation.sh <slug> fr` green. Run file
`sources/TRANSLATION_BOOKS_1-5_FR.md` (with the wave findings), one per book `sources/TRANSLATION_BOOK_N_FR.md`, scores
`translation_scores/book_N/fr/`, glossaries `sources/GLOSSARY_BOOK_N_FR.md`, term configs `tools/term_config/bookN_fr.py`.
Entries `one_quant_book_0N_*_fr.tex` (babel French on pdfTeX, `shorthands=off`); `\ominput` reads `parts/<slug>/fr/`
when it exists; UI strings in `styles/lang/fr.tex`. Gate 12 (`tools/check_quant_twin.py`) compares each translated
file's `\omcode` triples, dated-box dates, `\texttt` identifiers and math spans with its English twin, on disk.
Terminology follows French desk usage (`../pilot_translation/langs/series/one-quant-book.fr.md`). English canon: no
fresh-reader pass, solutions not recomputed.

**French pilot editions of Books 6–10 (2026-11-11).** Made by the same method, this time as written: **one coordinator,
the main session, for all five books, and no subagents of any kind**. That makes it the first whole-book run of that
shape. The Haiku 5.5 section calls ran at most three books at once: 1,497 calls, $10.9 at list price. The weekly plan went from
74 % to 78 % by the last book's close, against about 13 % for Books 1–5. Self-scored 88 each from a 20-passage sample:
Book 6 343 pp, Book 7 370, Book 8 356, Book 9 356, Book 10 327; all 0/0/0 under TeX Live 2026 and
`check_translation.sh` green. Run file `sources/TRANSLATION_BOOKS_6-10_FR.md`, one per book
`sources/TRANSLATION_BOOK_N_FR.md`. The shared sweeps are in `draft/pilot-quant-fr/` and take a slug (`fix_common.py`,
`typo_apply.py`, `iqroles_fr.py`, `wkend_labels.py`, `quotes_fr.py`, `numfile.py`, `index_join.py`, …). Books 1–5 still
carry two defect classes this run found and fixed only in Books 6–10: weekend-problem part labels in six forms, and the
mid price as *point médian* / *cours médian*. Not done: the HTML reader for the French books.

## Commands

```sh
make                          # build the book(s) into build/
make test-code                # ruff + pytest + g++ -std=c++20 + cargo + listing ranges + chart CSVs
make test-fast                # the same without `reference` tests (what CI runs)
make reproduce                # test-code + figdata, must leave no diff (before a release)
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
2. `OUTLINE.md` — premises, the twenty books, the running project, reading
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
- The user's e-mail address never appears in the repository, a user agent or a request. If a source asks for
  it, do not use that source (user rule, 2026-09-29). Documents already cited from such a site (SEC, BLS, DOL)
  stay cited; their files may be fetched only from mirrors that ask for nothing, such as the Internet Archive.
- No code is printed unless it is included from a tested file.
- Every title starts "One Quant Book N — ".

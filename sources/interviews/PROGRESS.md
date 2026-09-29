# One Quant Book 18 — The Interview Book: progress

Slug `interviews`, label prefix `iv`, teaching-module prefix `iv_`, entry file
`one_quant_book_18_interviews.tex`, 29 chapters in five parts (`part.iv.process`, `part.iv.quant`,
`part.iv.research`, `part.iv.programming`, `part.iv.person`). Written in the Books 17–18 batch
(`sources/BATCH_BOOKS_17-18.md`), one agent per book, alongside Book 17 (`industry`).

## Status

| Phase | State | Date |
|---|---|---|
| A — plan | done: briefs (`tools/briefs/book18.py`), 29 ledgers with briefs, `DEFINITIONS.md` (47 terms, 46 after the sync), skeleton 0/0/0 (43 pp) | 2026-09-28 |
| sync | done: decisions in `sources/BATCH_BOOKS_17-18.md` and `SERIES_DEFINITIONS.md` applied (briefs, map, plan) | 2026-09-29 |
| B — write | done: 29 chapters, each through `tools/gates.sh chapter` and `make test-code CH=` before the next | 2026-09-29 |
| C — whole-book passes | done: worked answers (23 chapters), 4 more figures, ch. 29 follow-ups and scorecards, originality gate, term links, per-figure check, comma scan | 2026-09-29 |
| D — deliver | done: 220 pp, 0/0/0, `gates.sh book` green, `make test-code CH=interviews` green, figdata no diff | 2026-09-29 |

## Shape (user ruling 2026-09-28)

New questions only; nothing reprinted, harvested or indexed from Books 1–17. Each chapter: hook; method
lesson of 2–4 pp (families, method per family, worked `example` boxes); one bank of `interviewq` ramped one
to three stars, each with `\iqroles{…}` and `\iqfirm{…}`; `omsources`. No exercises, weekend problem,
tutorial or build (ch. 21 may keep a one-page oracle-testing tutorial). Part I and ch. 28: 8–12 questions;
ch. 29: six transcribed mock interviews, three `interviewq` each. Every solution ends with `\iqlookfor{…}`.
`tools/gates.sh chapter` enforces 6–18 questions, roles, firm types, look-fors and `omsources`.

## Phase A checks (2026-09-28)

- Definition map (47 terms) checked against the multi-line `\index` harvest of Books 1–16 (3,383
  definitions): no exact, plural or word-subset collision.
- Every `uses` owner in Books 1–16 verified against the harvest by script (book and chapter).
  Found while checking: *machine-learning engineer* is already Book 12 ch. 28's term, not Book 17's; the
  briefs point to Book 12. *quant developer* is Book 16 ch. 21's and *structured interview* Book 16 ch. 10's.
- Terms owned by Book 17 are marked `(B17.nn, outline)` in the briefs and are to be confirmed at the sync:
  the role titles (trader, quant researcher, bank quant, software engineer, portfolio manager, risk
  manager), *total compensation*, *sign-on bonus*, *guaranteed bonus*, *notice period*, *internship*,
  *graduate programme*, *trading competition*. Book 17's briefs were not on disk when this map was made.
- Chapters with no new term (13–17, 23–25, 27) say so in their ledgers; they use Books 1–16's vocabulary.

## Question plan

| # | Chapter | Questions | Stars 1/2/3 | Terms |
|---|---|---|---|---|
| 1 | What Each Interview Tests, by Role | 8 | 3/3/2 | 3 |
| 2 | The Process by Firm Type | 8 | 3/3/2 | 2 |
| 3 | Applications | 8 | 3/3/2 | 3 |
| 4 | Online Assessments | 10 | 3/4/3 | 3 |
| 5 | Phone and Technical Screens | 8 | 3/3/2 | 3 |
| 6 | The Final Round and Trading Games | 10 | 3/4/3 | 4 |
| 7 | Offers, Compensation and Non-Competes | 10 | 3/4/3 | 3 |
| 8 | Mental Arithmetic | 14 | 5/5/4 | 2 |
| 9 | Estimation | 13 | 4/5/4 | 2 |
| 10 | Probability I | 14 | 5/5/4 | 2 |
| 11 | Probability II | 14 | 5/5/4 | 2 |
| 12 | Brainteasers and Logic | 14 | 5/5/4 | 3 |
| 13 | Betting and Market-Making Games | 14 | 5/5/4 | 0 |
| 14 | Statistics | 13 | 4/5/4 | 0 |
| 15 | Linear Algebra and Calculus | 13 | 4/5/4 | 0 |
| 16 | Stochastic Calculus | 13 | 4/5/4 | 0 |
| 17 | Options and Derivatives | 14 | 5/5/4 | 0 |
| 18 | Fixed Income and Markets | 13 | 4/5/4 | 1 |
| 19 | Machine Learning | 13 | 4/5/4 | 1 |
| 20 | Research Case Studies and Take-Homes | 12 | 4/5/3 | 2 |
| 21 | Algorithms and Data Structures | 14 | 5/5/4 | 3 |
| 22 | C++ | 14 | 5/5/4 | 1 |
| 23 | Rust | 13 | 4/5/4 | 0 |
| 24 | Python | 13 | 4/5/4 | 0 |
| 25 | Concurrency, Operating Systems and Networks | 13 | 4/5/4 | 0 |
| 26 | System Design | 13 | 4/5/4 | 2 |
| 27 | SQL and Data | 13 | 4/5/4 | 0 |
| 28 | Behavioural and Fit | 10 | 3/4/3 | 3 |
| 29 | Mock Interviews | 18 | 6/6/6 | 1 |
| | **Total** | **357** | **118/134/105** | **46** |

Sync (2026-09-29): every bank capped at 14; Part II and IV banks 13-14; ch. 29 keeps six transcripts of three;
about 355 questions and ~240-250 pp. *Return offer* moved to Book 17 (46 terms).

## Calibration target

~8 pp a chapter all-in: ~300 body lines (hook ⅓ p, lesson 2–4 pp, bank 1–1.5 pp, `omsources`) and ~200
solution lines (≈ 3 pp at 68 lines a page, 12–15 lines a solution including the look-for). Ch. 29 ~18 pp.
Book ≈ 28 × 8 + 18 + ~15 front and back matter ≈ 255 pp against the outline's ~240 (+6 %). Checkpoints at
ch. 10 and ch. 20: a chapter under ~6.5 pp all-in means the lesson has been squeezed; one over ~9.5 means
the solutions are too long.

## Checkpoint at chapter 10 (2026-09-29)

- Chapters 1-10: 45 body pages (arabic 2-47, part divider excluded) and about 17 solution pages: 6.2 pages a
  chapter all-in. Part I (8-10 questions) runs 6.3, Part II so far (13-14 questions) 6.5-7.
- Projection at this density: 29 x 6.2 + ch. 29's extra ~10 + ~12 front and back = about 205 pp, 15-18 % under
  the 240-250 target. Correction for chapters 11-29: lessons at 3-4 pp with a second worked example per section,
  solutions with the full argument (12-15 lines), and the listings of Part IV; expected landing about 235 pp.
- Web searches so far: 8 (plus about 40 direct fetches: Crossref, OpenAlex, legislation.gov.uk, eCFR,
  publications.europa.eu, leginfo, gov.uk API, firms' careers pages).
- Figures so far: 7 (2.1, 4.1, 6.1, 7.1, 8.1, 9.1, 10.1), each checked on its own page when drawn; fixed: 2.1
  (overlapping boxes, then an overfull box label), 8.1 (curves clipped by the y range), 10.1 (block too close to
  the second heading).
- The appendix title printed "Solutions to the Exercises"; the entry file now renews `\omsolutionspart` to
  "Solutions to the Interview Questions" (Book 18 only).

## Checkpoint at chapter 20 (2026-09-29)

- Chapters 1-20: about 88 body pages (arabic 2-91, three part dividers excluded) and about 35 solution pages:
  6.2 pages a chapter all-in, unchanged since chapter 10 although chapters 11-20 carry 12-14 questions and longer
  lessons (their solutions run 90-110 lines against 80 in Part I).
- Projection: 20 x 6.2 + 7 programming chapters at ~7.5 (listings print large) + ch. 28 ~5.5 + ch. 29 ~18 + ~12
  front and back = about 212 pp, 12-15 % under the 240-250 target. Correction: Part IV lessons at 4 pp with printed
  listings of tested answers, and ch. 29 at 18-20 pp; if the book still lands under 225 pp, the Phase C pass adds a
  worked example to the shortest lessons (chapters 3, 5, 14, 18).
- Web searches so far: 11. Figures so far: 15, each checked on its own page when drawn (fixed: 2.1, 8.1, 10.1,
  15.1 ticks and caption, 18.1 arrow, 20.1 ticks).

## Originality procedure (binding for Phase B)

1. Write each question from its family's idea (the lesson's method), in a new setting (desk, venue, book,
   feed) with new numbers, so its answer differs from any version the author remembers. Never fetch or
   consult an interview-question book or website while drafting; no such text is ever a source.
2. A classic puzzle appears only as a variant whose answer differs from the folklore one (three hat colours,
   a different coin count, a different day count), and its first publication is cited in `omsources`
   (Crossref / library catalogue rows in the ledger), never an interview book.
3. No question or solution is attributed to a firm, not even "a firm like …"; `\iqfirm{…}` names only a firm
   type.
4. `code/interviews/originality/tests/test_originality.py` extracts every `interviewq`, `exercise`,
   `problem` and solution text of Books 1–17 and every Book 18 question and solution, normalises them (TeX
   stripped, lower case, numbers kept) and fails on any shared 8-word shingle; it prints the count it
   compared (a gate that saw nothing has not passed). The shingle size and the exemption list (formula-only
   n-grams, "what is the interviewer looking for") are set in Phase B and reported.

## How each kind of answer is tested

| Kind | Test |
|---|---|
| exact probability, counting, algebra | `fractions.Fraction` or sympy; exhaustive enumeration of the sample space; first-step linear systems solved exactly |
| probabilistic claims | also simulated over many seeds with a tolerance (never one path); fast set < 20 s, full size `reference` |
| stochastic-calculus answers | sympy for the Itô algebra; Monte Carlo over seeds, with the time step divided by four as a stability check |
| estimation (ch. 9) | the chain's product equals the printed estimate (from printed factors); the ledgered reference value lies inside the printed interval |
| process arithmetic (ch. 1–4, 7, 28) | pass rates, offer values, scoring rules asserted exactly; qualitative answers carry no test |
| Python coding | the answer file against a brute-force oracle on thousands of random inputs from fixed seeds; complexity claims by operation counts, never timings |
| C++20 coding | `*_test.cpp` built by `tools/test_code.sh` (`-std=c++20 -O2 -Wall -Wextra -Werror`), same randomised cases as the Python oracle |
| C++ output prediction | pytest compiles each snippet at `-O0` and `-O2` and asserts stdout; implementation-defined values asserted for x86-64 Linux, stated as such |
| undefined behaviour | stated in the solution, never "tested": the snippet is built with `-fsanitize=address,undefined` (ThreadSanitizer for races) and the test asserts the sanitizer's diagnosis, no output |
| Rust coding | a dependency-free Cargo crate, `cargo clippy -D warnings` + `cargo test` |
| Rust compile-fail | pytest runs `rustc --edition 2021` on the snippet and asserts the error code (E0502, E0499, E0382, E0106, E0515) |
| Python output prediction | the snippet run in a subprocess with the venv interpreter (3.10), stdout asserted; implementation details of CPython stated as such |
| SQL | `.sql` files run on DuckDB (and SQLite where the dialect allows) on generated fixtures with planted ties and NULLs, compared with pandas / Polars references |
| ML (ch. 19) | scikit-learn on generated data; claimed effects (leak inflation, lasso instability) asserted over seeds |

## Source plan

Few external facts: Part I (firms' own published process descriptions, selection research, recruitment law:
NYC LL144, EU AI Act Annex III, UK agency regulations, Equality Act / ADA), ch. 7 (FTC non-compete rule and
Ryan LLC v. FTC, California 16600/16600.5, UK non-compete policy, pay-transparency and salary-history laws,
PRA/FCA remuneration changes, a university's offer-deadline policy), ch. 9's reference values (OCC/Cboe
option volume, BIS 2025 FX turnover, listed-company count, consolidated share volume, a peak feed rate, UN
population), ch. 22–25's language and protocol standards, and the first publications of classic puzzles
(ch. 10–12) via Crossref. Estimate ~50 web searches; primary URLs fetched directly; several rows reusable by
pointer from Book 2 (BIS, games), Books 13–14 (feed rates) and Book 16 (selection research, remuneration,
covenants). Firms are named only in Part I dated boxes, only for their own published process description,
each with a ledger row.

## Notation beyond CONTRIBUTING.md

All local and declared in the chapter: $L, U$ interval bounds and $c$ stated coverage (ch. 9); $p_k$ stage
pass rates (ch. 1–2); $V_{\mathrm{offer}}$, $\pi_{\mathrm{leave}}$ (ch. 7); $n$ input size and $O(\cdot)$
(ch. 21, 26; $n$ is otherwise a sample size). Game quotes use the series' $b, a$ and $m$; $\lambda$ stays an
intensity (message rate in ch. 26).

## Phase C (2026-09-29)

- Page count after Phase B: 206 pp (138 body, 59 solutions). Correction: a `Worked answers` section (1-3 `example`
  boxes answered aloud, every number asserted in the chapter's `test_worked_answers`) in chapters 1-6, 8-21, 25, 26
  and 28; four more charts (1.1 loop pass rate, 3.1 best of k, 14.1 years for power, 28.1 tail frequency, each with a
  `fig_iv_*.py` and a CSV test); ch. 29 grew from 6 to 11 pp with one follow-up per question, the not-hired trader's
  transcript promised by the hook, and a scorecard table. Result: 220 pp.
- Originality gate (`code/interviews/originality/tests/test_originality.py`): 8-word shingles after stripping TeX
  (labels, refs, `\iqroles`, `\iqfirm`, `\omcode` removed; lower case; numbers kept); a shingle counts only if it has
  at least five alphabetic words of three letters or more; exempt phrases: "what the interviewer is looking for",
  "one quant book". Compares 805 Book 18 texts (357 questions, 357 solutions, 91 examples) with 14,597
  `interviewq`/`exercise`/`problem`/`solution`/`example` texts of Books 1-17. First run: 35 shared runs; two were real
  near-duplicates written from memory (ch. 13: "a market on the sum of two dice", Book 2 ch. 30; "pays 2 to 1 and
  wins with probability 0.4", Book 2 ch. 29) and were rewritten with new settings and numbers (the gap between two
  dice; a 3-to-1 wager at 0.35); the rest were stock phrases ("what are the mean and standard deviation of") and
  were reworded. Also found by the reread: ch. 5's first worked answer duplicated ch. 10's question 13 (two arrivals
  within ten seconds) and was replaced. Now 0 shared runs.
- Term links: `--unwrap --apply` then `--apply`: 49 linkable terms, 56 links in 23 files; no STOP/DROP curation
  needed (the terms are interview vocabulary, not ordinary English); `--check` clean.
- figures: 23 checked, 0 fixed in this pass (9 were fixed when drawn in Phase B: 2.1, 8.1, 10.1, 15.1, 18.1, 20.1,
  25.1, 26.1, 26.2). The ch. 29 scorecard table overflowed by 57 pt and was set in `\footnotesize`.
- PDF comma scan (`pdftotext -layout | grep -P '(?<![\d.,])\d{1,3}(,\d{3})+(?![\d,])'`): no match.

## Defects found (to report, not fixed here)

The four below were reported in Phase A and fixed by the main session at the sync.


- `parts/desk/10-hiring-and-compensation.tex:23-24` says the series' interview questions are collected by
  One Quant Book 18 ("One Quant Book 18 collects them."). The ruling of 2026-09-28 is new questions only.
  Fix: "One Quant Book 18 applies the same format to new questions."
- `OUTLINE.md:120-121` ("Book 18 is last because it harvests the per-chapter interview questions") and
  `WRITING_A_QUANT_BOOK.md:403` ("Book 18 later harvests them by label") contradict the same ruling.
- `tools/make_briefs.py` writes "- **Defines.** ." for a chapter with no new term; worked around by editing
  the nine ledgers.
- `tools/gates.sh chapter` counts `\iqroles` and `\iqfirm` only on the `\begin{interviewq}` line and the one
  after it (`grep -A1`); a question whose tags wrap to a third line fails. Book 18 keeps the tags on the
  `\begin` line.

## Traps and calibration (for the shared docs)

- **Calibration.** The new-questions-only shape lands at about 7.6 pp a chapter all-in (220 pp / 29), not the 8 planned:
  a 13-question bank with 12-15-line solutions prints in 1.5 + 2 pp, and lessons of 3-4 pp. The outline's ~240 would
  need either more questions per chapter (capped at 14 by the sync) or padding; the book stops at 220.
- **Unquoted heredoc eats TeX.** A Python edit passed through `<<EOF` (unquoted, to expand a shell variable) turned
  `$e_3` and `$1` into empty strings in two chapters; the build failed with "Missing $ inserted". Always `<<'EOF'`
  for anything containing TeX, and pass paths as literals.
- **Insert-after-anchor helpers must search from the anchor's own line.** A helper that looked for the next
  assessor note after the anchor put each follow-up one exchange late; repaired by removing the inserted blocks in
  reverse order of insertion (later blocks had landed inside earlier ones).
- **ThreadSanitizer and ASLR, second form.** Besides "unexpected memory mapping", a TSan binary can die at start-up
  with SIGSEGV and no output (return code -11). The chapter's helper now reruns under `setarch $(uname -m) -R` on
  either symptom.
- **ruff B905.** `zip()` without `strict=` fails the series' ruff config; pairwise `zip(a, a[1:])` needs
  `strict=False`.
- **Writing from memory reproduces the series.** Two questions matched Book 2 almost word for word although neither
  was consulted while drafting: the originality gate is necessary, not decorative, and must run on examples too.
- **grep is ugrep here.** `/usr/bin/grep -a` for logs and PCRE.

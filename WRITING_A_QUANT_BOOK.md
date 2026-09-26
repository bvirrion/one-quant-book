# How to write one of the One Quant Books

Instructions for writing **one book** of the One Quant Book series, start to
finish. Every rule is spelled out per item as **Procedure / Checklist / Exit
condition**, so that "done" is never a matter of taste.

Status: written 2026-09-18; revised 2026-09-19 after Book 1 was written in
full. The numbers in [Calibration](#calibration) are measured on Book 1, and
the [known traps](#9-known-traps-add-to-this-list-as-books-are-written) are
the ones it actually fell into.

## 0. Read first, in this order

1. `../CLAUDE.md` — workspace rules (never commit; work from inside the repo).
2. `../book_style.md` — the One Course family style. **Everything there
   applies unless section 1 below overrides it.**
3. `OUTLINE.md` — premises, the eighteen books, the running project, the
   three-level access rule, reading paths.
4. The book's section in `outline/*.md` — its parts, chapters, summaries,
   page budgets and planned strategy-file counts.
5. This file.
6. One finished chapter of `../one-math-book` (university volume) and one of
   `../one-physics-book`, for voice and density.

Working rules that never change:

- **One author per book.** A book may be written by one subagent (user rule,
  2026-09-24), and at most **four books per batch**; never one agent per
  chapter — one book, one voice, one context. In a batch the main session
  makes every shared-file edit up front (entry files, `styles/`, `latexmkrc`,
  `tools/termlink/books.py`, part titles, notation), reconciles the books'
  definition maps before any chapter is written, and runs the series-wide
  gates at the end. Book agents write only files under their own slug, treat
  other shared files as append-only, and run no git command but
  `status`/`diff`/`log`.
- **Never create git commits.** Leave the working tree for the user.
- **English only.** No `<lang>/` trees, no translation tooling.

## 1. What carries over from `book_style.md`, and what changes

| Topic | Family rule | Quant series |
|---|---|---|
| Five books by school year | yes | **No.** Eighteen books by strand; no years, no level guard. |
| Reader | a pupil or student | A professional-to-be who codes in C++, Rust and Python and has master's-level mathematics. Never teach language basics or undergraduate mathematics. |
| Statement environments, colours, `[Titled]` + labelled | yes | Unchanged, plus the new environments of section 5. |
| Rigor, `\admitted`, `Partial proof` | yes | Unchanged. "Proved in" pointers are prose: "One Quant Book 4". |
| New terms `\emph{term}\index{term}` in a `definition` | yes | Unchanged — this is still what the term linker harvests. |
| `\omterm` links generated, never hand-written | yes | Unchanged. `AMBIG_POLICY = "drop"` (university setting). Expect heavy `STOP` curation: *spread, book, fill, cross, leg, roll, fix, print, size, lift, hit, float, call, put, strike, margin, basis, curve, carry, short, long, close, open*. |
| Cross-volume references prose-only | yes | Unchanged. Write "One Quant Book 10", never a `\cref` into another book. |
| No curriculum or country names | yes | Not applicable — but see "Naming firms" (section 6.2). |
| Visuals: schematic / AI illustration / photograph | science books | **Charts and schematics first.** See section 6.8. |
| Exercises: count and ramp | 8–15 | **8 per chapter**, ramped 3×★, 3×★★, 2×★★★. |
| Weekend problem | high-school and university | **Every chapter**, ~20 questions, Parts I–IV, one named quantified result. |
| Quality gates: 0 errors / 0 undefined / 0 overfull | yes | Unchanged, **plus** the code, source and number gates of section 7. |
| Translations | seven languages | None. |

## 2. Repository layout

Books are renumbered more easily than they are renamed (the outline was
renumbered twice in its first day). Therefore **numbers appear only in the
entry-file name and the printed title; directories and label prefixes use a
stable strand slug.**

```
one_quant_book_<NN>_<slug>.tex        entry file, NN = 01…18
styles/onequant.sty                   the ONLY place packages/macros live
styles/lang/en.tex                    UI strings (kept for family parity)
frontmatter/                          title page, colophon, preface, credits
parts/<slug>/part.tex                 \part declarations + \ominput lines
parts/<slug>/NN-chapter-slug.tex      chapter
parts/<slug>/solutions/NN-chapter-slug.tex
code/<slug>/NN-chapter-slug/          python/  cpp/  rust/  tests/  README.md
code/firm/                            the running project (grows across books)
data/<slug>/                          small, licensed or synthetic datasets + LICENSES.md
figdata/<slug>/NN-chapter-slug/       CSVs that pgfplots charts read (script-generated)
images/<slug>/                        photographs + CREDITS.md;  ai/ + PROMPTS.md
sources/<slug>/NN-chapter-slug.md     the source ledger (section 6.1)
tools/                                termlink, gates, figure-page finder
```

| Book | Slug | Label prefix |
|---|---|---|
| 1 Markets I | `markets-1` | `m1` |
| 2 Markets II | `markets-2` | `m2` |
| 3 Markets III | `markets-3` | `m3` |
| 4 Quantitative Methods | `methods` | `qm` |
| 5 Derivatives and Volatility | `derivatives` | `dv` |
| 6 Rates, Credit, XVA and Risk | `rates-credit-risk` | `rc` |
| 7 Research Craft | `research` | `rs` |
| 8 Strategies I | `strategies-1` | `s1` |
| 9 Strategies II | `strategies-2` | `s2` |
| 10 Microstructure and Execution | `microstructure` | `mx` |
| 11 Market Making and HFT | `hft` | `hf` |
| 12 Machine Learning for Markets | `ml` | `ml` |
| 13 Low-Latency Software | `low-latency` | `ll` |
| 14 Networks, Hardware, Infrastructure | `networks` | `nw` |
| 15 Research, Data and Risk Platforms | `platforms` | `pl` |
| 16 The Desk and the Firm | `firm` | `fm` |
| 17 The Industry | `industry` | `in` |
| 18 The Interview Book | `interviews` | `iv` |

Labels: `<type>:<prefix>:<chapter-slug>:<name>`. Types from the family
(`ch def thm prop lem cor met ex rem not exo pb`) plus:

| Type | For |
|---|---|
| `strat:` | a strategy file |
| `pred:` | a predictor card |
| `tut:` | a tutorial |
| `bld:` | a build |
| `iq:` | an interview question (has a solution, like `exo:`) |
| `lst:` | a code listing |
| `dat:` | a dated box |

The printed title of every book starts **"One Quant Book N — "**; `\bookline`
carries the same string.

## 3. Once per series: the bootstrap (before Book 1, chapter 1)

**Procedure.** Copy from `../one-biology-book` (the newest toolchain) and strip
what the series does not need:

1. `styles/onebiology.sty` → `styles/onequant.sty`; keep brand, theorem
   environments, `omfigure`, `solution`, `\omsolutionlinks`, `\omlinkpad`,
   `\omterm`; **remove** babel/fontspec/bidi multi-language dispatch.
2. Add to the style file, and nowhere else: `listings` (with C++, Rust,
   Python styles in the semantic palette), and the environments
   `strategyfile`, `predictorcard`, `tutorial`, `build`, `interviewq`,
   `dated` (takes a `YYYY-MM` argument, prints "As of <month year>"),
   `omsources`; the macro `\omcode{<path>}{<first>}{<last>}{<caption>}`
   wrapping `\lstinputlisting`.
3. `frontmatter/` with the One Course preface adapted (subject swapped), a
   colophon carrying the **not-investment-advice** and **public-sources-only**
   notices, and an Image Credits page.
4. `latexmkrc`, `Makefile` (targets: `all`, `test-code`, `figdata`, `gates`).
5. `tools/termlink/`, `tools/link_defined_terms.py`, `tools/term_config/`.
6. `tools/gates.sh` implementing section 7; CI that runs `make test-code`
   and the LaTeX build.
7. `THEME.md` (copy), `CONTRIBUTING.md`, `CLAUDE.md`.

**Exit condition.** An entry file with one placeholder chapter containing one
of every environment builds at 0 errors / 0 undefined / 0 overfull;
`make test-code` runs one Python, one C++ and one Rust test green.

## 4. Writing one book: the workflow

### Phase A — Plan (no prose yet)

**Procedure.**
1. Re-read the book's outline. For each chapter write a **chapter brief** at
   the top of its source ledger (`sources/<slug>/NN-….md`): the hook scene;
   the 3–5 sections; the terms it will *define*; the terms it *uses* from
   earlier chapters or books; its strategy files / predictor cards by name;
   the tutorial; the build and which piece of `code/firm/` it adds; the
   weekend problem's story and named result; data needed.
2. Build the book's **definition map**: every term, the single chapter that
   defines it. A term is defined **once** in the series — search earlier
   books' `\index{}` entries before claiming one.
3. Freeze chapter order. If a brief shows a chapter is two chapters, or two
   are one, change `outline/*.md` **first** and tell the user.
4. Create `parts/<slug>/part.tex`, empty chapter and solutions files, the
   entry file, and add it to `latexmkrc`.

**Exit condition.** Every chapter has a brief; no term has two defining
chapters; the skeleton builds green.

### Phase B — Write, chapter by chapter, in order

For each chapter, in this order: **sources → lesson → code → figures →
exercises/problem/interview questions → solutions → chapter gates.** Do not
start chapter N+1 until chapter N passes its gates (section 7.1). Details per
item in section 6.

### Phase C — Whole-book passes (after the last chapter)

1. Term links: `python3 tools/link_defined_terms.py --book N --unwrap --apply`
   then `--apply`; curate `STOP` / `EXTRA_PROTECT`; rebuild.
2. Full gates (section 7.2).
3. Per-image double-check of **every** figure (family rule: one page per
   figure at ~130 dpi, never a contact sheet).
4. Numbers pass: re-run every solution's arithmetic (section 6.12).
5. Dated-box pass: every `dated` box re-verified if older than 60 days.
6. Read the book once front to back for voice, repetition and forward
   references that should be backward.

### Phase D — Deliver

Report to the user: page count against the outline budget; chapter count;
counts of figures / listings / strategy files / dated boxes; gate results;
anything excluded as unverifiable (section 6.1); defects found in *earlier*
books. Update the root `CLAUDE.md` entry and write the memory note. No commit.

## 5. Chapter anatomy and page budget

A chapter is ~13 pages all-in (≈ 9.5 body + 3.5 solutions).

| # | Block | Budget | Notes |
|---|---|---|---|
| 1 | `\chapter` + hook | ⅓ p | A concrete scene: a desk, a venue, an incident, a number on a screen. No "in this chapter we will". |
| 2 | Lesson: 3–5 `\section`s | 5–6 pp | definitions / theorems / propositions / methods / examples / remarks; an example after every substantial definition; a `method` box per standard technique. |
| 3 | `strategyfile` / `predictorcard` boxes | inside the lesson | only in chapters the outline marks; ⅔–1 p each. |
| 4 | `\section{Tutorial: …}` | 1–1½ pp | guided, reader types along; ends on a figure or table the reader reproduces. |
| 5 | `\section{Build: …}` | ½–1 p | a specification, not a solution. |
| 6 | `\section{Exercises}` | 1 p | 8, ramped 3/3/2. |
| 7 | `\section{Problem: <Title>}` | 1–1½ pp | one weekend problem, ~20 questions. |
| 8 | `\section{Interview questions}` | ½ p | 5–8 `interviewq`. |
| 9 | `omsources` | ¼ p | the chapter's sources and further reading. |

Chapters whose outline title starts "Build:" invert the ratio: lesson 3 pp,
build 5 pp.

## 6. Rules per item

### 6.1 Facts, numbers and the source ledger

The series' credibility rests on this rule. A model's memory is **not** a
source: it is a lead to be verified.

- **Procedure.** Before writing a chapter, list in its ledger every
  *checkable external fact* the chapter will state: venue rules, fee levels,
  contract specifications, locations, dates and sizes of incidents,
  regulatory requirements, firm facts, market statistics. For each, find a
  primary or reputable public source (rulebook, exchange notice, regulator or
  court document, filing, paper, conference talk, firm publication, quality
  press), fetch it, and record: `claim | source | URL | date accessed |
  quote or page`. Mechanisms and mathematics derived in the book need no
  entry.
- **Volatile facts** (anything that a venue, vendor or regulator can change:
  fees, tiers, rate limits, regions, programme terms, prices, headcounts, pay)
  go in a `dated` box, never in running text. The running text states the
  durable mechanism.
- **Unverifiable.** If no public source is found: state the mechanism
  generically ("some venues offer…"), or drop it. Record it in the ledger
  under `EXCLUDED` and list it in the delivery report — the user may know a
  source.
- **Checklist.** Every number with a unit of money, time, distance or count
  that is not computed in the book has a ledger row. Every `dated` box has a
  `dat:` label and a ledger row no older than 60 days at delivery.
- **Exit condition.** `tools/gates.sh sources <chapter>` reports zero `dated`
  boxes without ledger rows and zero ledger rows without a URL and access
  date.

### 6.2 Naming firms

- **Procedure.** A sentence may attribute a practice, number or event to a
  named firm **only** if the ledger holds a citable public source for exactly
  that attribution. Otherwise write the category: "a large options market
  maker", "a multi-manager platform". Criticism (fines, lawsuits) only from
  court or regulatory records, stated neutrally, with the outcome.
- **Never:** insider or confidential information; rumours; interview
  questions attributed to a firm; a living person's private details.
- **Exit condition.** Every line matched by the firm-name gate (section 7)
  has a ledger row whose `claim` covers it.

### 6.3 Strategy files

- **Procedure.** Use the `strategyfile` environment with these nine fields,
  in this order, all present:
  1. *Who pays you, and why* — the counterparty and the economic reason.
  2. *Instruments and venues.*
  3. *Signal* — exact formulas, with the chapter's notation.
  4. *Sizing and execution.*
  5. *Costs* — fees, rebates, financing, borrow, impact.
  6. *How it dies* — crowding, regime, tail; name the historical episode.
  7. *Horizon, capacity, infrastructure.*
  8. *Backtest honestly* — the right fidelity level (Book 7) and the classic
     self-deception for this strategy.
  9. *Sources.*
- State plainly when the public evidence says a strategy has decayed. Never
  promise returns; never print a Sharpe ratio without its source, period and
  cost assumptions.
- Manipulative strategies (Book 9 ch. 29 and wherever they appear) are
  written as *how it works → why it is illegal or contested → the enforcement
  case → the surveillance detector*. No operational recipe beyond what the
  public enforcement record already contains.
- **Exit condition.** The chapter's count matches the outline's bracketed
  number (or the outline is updated); every file has nine fields and a
  `strat:` label; major files are implemented in the tutorial or the build.

### 6.4 Predictor cards (Book 7 and wherever predictors are introduced)

Fields: definition (formula) · inputs and their timestamps · rationale ·
horizon and measured half-life (on the book's simulator or free data, with
the script in `code/`) · normalisation · known failure modes · sources.
**Exit condition:** the half-life figure is produced by a tested script.

### 6.5 Code listings

- **Procedure.** Write the code first, in
  `code/<slug>/NN-chapter-slug/{python,cpp,rust}/`, with tests in `tests/`.
  Print it with `\omcode{path}{first}{last}{caption}` and an `lst:` label.
  **Never paste code into a chapter file.**
- Languages: **Python** for research, statistics, pricing prototypes and
  charts; **C++** (C++20 — the toolchain is g++ 11, `-std=c++20`) as the printed systems language; **Rust** twin of
  every systems build in the companion tree, printed only in chapters about
  Rust. Books 13–14 print both where the contrast teaches something.
- A printed listing is ≤ 40 lines and shows the idea; the file may be longer.
  Code is warning-free (`-Wall -Wextra -Werror`, `clippy -D warnings`,
  `ruff`), formatted, deterministic (fixed seeds), and needs no paid data or
  network access to pass its tests.
- **Exit condition.** `make test-code` green; zero `\begin{lstlisting}` in
  `parts/`; every `\omcode` path exists and its line range is inside the
  file.

### 6.6 Tutorials

- **Procedure.** State the goal in one sentence and the expected end state (a
  figure, a table, a number). Number the steps. Each step: what to do, the
  listing or command, what the reader should see. End with "what to change
  next" (two variations that become exercises).
- **Exit condition.** Following the printed steps from a clean checkout of
  `code/` reproduces the printed end state; the script that does so is a
  test.

### 6.7 Builds (the running project)

- **Procedure.** A build is a **specification**: purpose, interface
  (types/functions/messages), behaviour rules, acceptance tests the reader
  runs (`code/firm/<component>/tests/`), performance target where relevant,
  stretch goals. The reference implementation lives in `code/firm/` but is
  **not printed**; the chapter prints at most the interface and one subtle
  excerpt.
- Each build must plug into the pieces built earlier (OUTLINE.md, "The
  running project"). Never break an earlier book's acceptance tests.
- **Exit condition.** Reference implementation passes its acceptance tests in
  C++ and Rust (or Python where the outline says research code); earlier
  builds' tests still pass.

### 6.8 Figures

- **Charts (pgfplots) are the default visual.** Every chart of data is
  generated: a script in `code/` writes a CSV to `figdata/`, pgfplots reads
  it. No hand-typed data points. Source of the data (simulator, free dataset
  and its licence, or a cited publication) goes in the caption's last clause.
- **Schematics (TikZ)** for structure: order books, message flows,
  architectures, network maps, payoff diagrams, timelines of an incident.
- **Photographs** only for a specific real thing worth seeing as it is (a
  trading floor of a given era, a microwave tower, a data-centre hall, a
  historic document), free licence verified, `CREDITS.md` row per file.
- **AI illustrations: rare**, never for a real identifiable place, firm,
  person or screen; JPEG only (family recipe).
- **Maps** (Book 14): TikZ over coordinates computed by script; distances and
  light-times in the figure are computed, not typed.
- Family rules in full force: no overlapping text; **check every figure
  individually on its rendered page**; and **correct in the field** — here:
  bids below asks, queues in time priority, payoff kinks at the strike,
  Greeks with the right sign, log axes labelled as such, a yield curve's
  maturities in order, packet flows in the right direction, the right side of
  the book consumed by the right aggressor.
- Budget: ~4 figures per chapter, at least one chart of data where the
  chapter has data.
- **Exit condition.** Every figure inspected on its own page at ~130 dpi and
  logged clean; every chart's CSV is regenerated by `make figdata` with no
  diff.

### 6.9 Mathematics and notation

- Book 4 ch. 1 fixes the series notation; every other book follows it.
  Before Book 4 exists, follow the notation table in `CONTRIBUTING.md`.
- Derive what is derivable in the space available; otherwise `\admitted` plus
  where it is honestly proved (a book of this series, or a cited text in
  `omsources`).
- Money and market units via `siunitx`: declare `\bp` (basis point), `\tick`,
  currencies as ISO codes (`\qty{1.5}{\bp}`, `USD~2.4~million`); latencies
  with `\qty{}{\micro\second}`; decimal point; thousands separated by thin
  spaces; never "k"/"mm" in prose.
- Tickers, order types as they appear on a wire, message fields, function and
  file names: `\texttt`.

### 6.10 Exercises

- 8 per chapter, `exo:` label first, ramp 3×★, 3×★★, 2×★★★, mixing:
  computation, order-of-magnitude, reasoning about a mechanism, reading a
  figure or an order-book snapshot, a small coding task (answer is a number
  the test suite confirms), and "find the flaw" (a backtest, a pricing
  argument, a design).
- **Exit condition.** Label/solution diff empty (section 7.1).

### 6.11 Weekend problem

- One per chapter: `\begin{problem}[{Weekend problem --- <story>}]`, `pb:`
  label first, Parts I–IV, ~20 questions, enumerates continued with
  `[resume]`, building to **one named, quantified result**. The story is a
  real or realistic desk situation; when it is a real episode, its facts are
  in the ledger.

### 6.12 Interview questions and solutions

- 5–8 `interviewq` per chapter, `iq:` label first, tagged with stars and with
  roles (`trader, researcher, developer, mle, bank`). They test the chapter's
  ideas in interview form — they are not recycled exercises. Never attributed
  to a firm. Book 18 later harvests them by label.
- **Solutions file**: opens with the family's `\section*{Chapter \ref{…} ---
  Title}` line; then `\begin{solution}{<key>}` for every `exo:`, the `pb:`,
  and every `iq:`, in order. Terse but complete: the decisive step and the
  key numbers. Interview solutions add one line: *what the interviewer is
  looking for*.
- **Numbers gate.** Every numerical answer is recomputed by a script in
  `code/<slug>/NN-…/tests/test_solutions.py` that asserts the printed value
  to the printed precision. (Translation runs in the sister series kept
  finding solutions whose numbers their own formulas could not produce; this
  gate exists so that class of defect cannot ship.)
- **Exit condition.** Label/solution diff empty; `test_solutions.py` green.

### 6.13 Typography and prose

Family rules: `` ``…'' `` never `"`; `\dots` never `...`; concise, no filler;
precise subject vocabulary — a metaphor may illustrate a term, never replace
it. Desk jargon is introduced once, in a `definition`, with its plain
meaning, then used freely. No hype ("secret", "edge they don't want you to
know"); no promises of profit.

## 7. Quality gates

### 7.1 Per chapter (before starting the next one)

```sh
latexmk one_quant_book_<NN>_<slug>.tex
L=build/one_quant_book_<NN>_<slug>.log
grep -c '^!' $L; grep -ci 'undefined' $L; grep -c 'Overfull' $L      # 0 / 0 / 0

C=parts/<slug>/NN-chapter-slug.tex; S=parts/<slug>/solutions/NN-chapter-slug.tex
diff <(grep -o 'label{\(exo\|pb\|iq\):[^}]*}' $C | sed 's/label{//;s/}//') \
     <(grep -o 'begin{solution}{[^}]*}' $S | sed 's/begin{solution}{//;s/}//')   # empty
grep -c '"' $C $S                                   # 0 straight quotes
grep -n '\.\.\.' $C $S | grep -v '\\dots\|\\foreach' # nothing
grep -n 'begin{lstlisting}' $C $S                   # nothing
grep -c 'begin{exercise}' $C                        # 8
make test-code CH=<slug>/NN-chapter-slug            # green (code, tutorial, solutions)
tools/gates.sh sources <slug>/NN-chapter-slug       # dated boxes ↔ ledger
tools/gates.sh firms   <slug>/NN-chapter-slug       # named-firm lines ↔ ledger
```

Then render and read every figure of the chapter.

### 7.2 Per book (Phase C)

All of 7.1 over every chapter, plus: duplicate labels
(`grep -rho 'label{[^}]*}' parts/<slug>/ | sort | uniq -d` → nothing);
`\end{…>` typo class; term linker run with `--unwrap --apply` then `--apply`
and the build still 0/0/0; terms defined twice across the series (compare
`\index{}` harvests of all written books → nothing); `make figdata` leaves no
diff; every figure checked on its own page; page count within ±8 % of the
outline budget or the difference explained.

## 8. Calibration

**Measured on Book 1, chapters 1–3 (2026-09-18).**

| | body lines | body pages | solutions lines | solutions pages | all-in |
|---|---|---|---|---|---|
| ch. 1 | 555 | 10 | 157 | 2.0 | 12.0 |
| ch. 2 | 510 | 9 | 157 | 2.0 | 11.0 |
| ch. 3 | 502 | 9 | 160 | 2.7 | 11.7 |

- **Body: ~55 source lines per page** (not 70: four figures, boxed
  environments and listings included from files all print larger than their
  source). **Solutions: ~68 lines per page.**
- A chapter with 4 figures, 2 listings, 1–2 dated boxes, 8 exercises, a
  20-question problem and 6 interview questions lands at **~11.5 pages
  all-in** from ~520 body lines + ~160 solution lines.
- Page budgets in `outline/*.md` map to source lines as: 10 pp → 430 body
  lines; 12 pp → 520; 14 pp → 620; 16 pp → 720 (solutions ~160–200 in all
  cases). Chapters budgeted at 14–16 pp need a fifth section or a second
  tutorial step with a listing, not longer prose.
- At the chapter 1–3 density Book 1 would come to ~375 pp against an outline
  figure of ~428; the 14–16 pp chapters (9, 14, market-structure chapters)
  are expected to close most of the gap. Re-check at chapter 10.
- **Re-check at chapter 10 (2026-09-18):** ten chapters occupy 96 body pages
  and about 24 solution pages: **12.0 pages all-in per chapter**, steady since
  chapter 1. Projection for Book 1: 31 × 12.0 + 20 ≈ **392 pages**, against an
  outline figure of 428 (−8 %, inside the ±8 % gate). The outline's 14–16 pp
  chapters came out at 12–13 pp with the same content plan, so the outline's
  per-chapter figures overstate by about two pages where they exceed 12.
- **Final, Book 1 complete (2026-09-19): 374 pages** for 31 chapters — 121
  figures, 78 listings, 49 dated boxes, 248 exercises, 31 weekend problems, 186
  interview questions, 165 ledger rows, 1,647 term links (4.4 a page), 336
  Python tests, ~10,400 lines of tested code. That is **11.5 pages all-in per
  chapter plus ~18 pages of front and back matter**, −5 % against the chapter-10
  projection and −13 % against the outline's 428. Budget future books at
  **12 pages a chapter all-in**, whatever the outline's per-chapter figure
  says; `outline/markets.md` and `OUTLINE.md` now carry the measured total for
  Book 1. Later chapters ran shorter in source (400–460 body lines) for the
  same page count, because tables, dated boxes and wide figures print large.
- A full chapter cycle (sources → code → text → solutions → gates → figure
  checks) is the unit of work; nothing is batched across chapters.
- **Book 2 complete (2026-09-24): 363 pages** for 31 chapters (outline ~412,
  −12 %): 280 pages of chapters (9.0 body pages each, 355–605 body lines), 68 of
  solutions (2.2 each), ~15 of front and back matter — **11.2 pages all-in per
  chapter**, slightly below Book 1. 126 figures, 73 listings, 37 dated boxes,
  248 exercises, 31 weekend problems, 186 interview questions, 226 ledger rows,
  1,388 term links (3.8 a page), 334 new Python tests and three components also
  in C++20 and Rust. The ch. 3 and ch. 10 checkpoints projected 389 and 377
  pages; the Part V–VI chapters (access, craft) came out at 8–9 body pages.
  Budget a Markets-type book at **11–12 pages a chapter**; the outline's
  per-chapter figures overstate by 1–3 pages whenever they exceed 12.
- **Books 3–6, written in parallel (2026-09-24), one agent per book:**

  | Book | Chapters | Pages | Outline | pp/chapter all-in | Figures | Listings | Dated | Ledger rows | Links |
  |---|---|---|---|---|---|---|---|---|---|
  | 3 Markets III | 29 | 332 | ~386 | 11.4 | 109 | 56 | 79 | 277 | 1,267 |
  | 4 Methods | 29 | 351 | ~406 | 12.1 | 118 | 59 | 0 | 253 | 1,739 |
  | 5 Derivatives | 28 | 348 | ~386 | 12.4 | 113 | 70 | 9 | 154 | 1,378 |
  | 6 Rates, Credit, XVA, Risk | 29 | 314 | ~372 | 10.8 | 107 | 55 | 32 | 160 | 824 |

  The four agents' checkpoints agreed: at ch. 10 every book projected 10.4–10.8
  pages a chapter, and the books that pushed later chapters to 480–560 body
  lines (a fifth section, a second worked example) finished at 11.4–12.4;
  Book 6 kept 400–550 and finished at 10.8. All four land 10–16 % under
  the outline. The mathematical books run denser in pages per chapter (Books 4
  and 5 at 12.1–12.4), and their ledgers are bibliographic (papers, datasets,
  incident reports) rather than venue facts, with few or no dated boxes.
  Budget **11–12.5 pages a chapter**; a chapter under 420 body lines
  comes out at 8 body pages. Ledger size was set by the web-search budget,
  not the subject: Books 3 and 6 ran out of searches half-way and re-sourced
  61 and 33 dropped facts afterwards (see section 9). The whole batch —
  Phase A, sync, four books, two re-sourcing passes — ran in one day of wall
  time.

- **Book 7 complete (2026-09-25), written in the main session without
  subagents: 345 pages** for 29 chapters (outline ~398, −13 %): 262 pages of
  chapters (9.0 body pages each, 250–560 body lines), 68 of solutions (2.3
  each), ~15 of front and back matter — **11.4 pages all-in per chapter**.
  86 figures, 67 listings, 27 tables, 3 dated boxes, 16 predictor cards, 232
  exercises, 29 weekend problems, 174 interview questions, 177 ledger rows,
  1,306 term links (3.9 a page), 240 new Python tests (115 chapter, 125 in 30
  new `firm` components, two also in C++20 and Rust), ~11,100 lines of tested
  Python. The ch. 10 and ch. 20 checkpoints projected ~360 and ~350 pages.
  A research-methods book whose numbers all come from simulation has small
  ledgers (bibliographic rows, a few public datasets) and almost no dated
  boxes; its page count is driven by tables of simulated results, which print
  large for few source lines (chapters of 250–340 body lines still made 8–9
  body pages).

- **Book 8 complete (2026-09-25), written in the main session without
  subagents: 330 pages** for 29 chapters (outline ~388, −15 %): 252 pages of
  chapters (8.7 body pages each, 280–430 body lines), 66 of solutions (2.3
  each), ~12 of front and back matter — **11.0 pages all-in per chapter**.
  54 figures, 57 listings, 39 tables, 13 dated boxes, 118 strategy files (outline
  ~117), 232 exercises, 29 weekend problems, 174 interview questions, 140 ledger
  rows, 597 term links (1.8 a page: strategy vocabulary is mostly defined
  elsewhere), 218 new Python tests (126 chapter, 92 in 30 new `firm`
  components), ~7,100 lines of tested Python. The ch. 10 and ch. 20
  checkpoints projected ~340 pages each. A strategies book writes one to three
  figures a chapter because its results are tables of Sharpe ratios; its
  chapters of 280–430 body lines print at 8–10 body pages.

- **Book 9 complete (2026-09-25), written in the main session without
  subagents: 333 pages** for 29 chapters (outline ~382, −13 %): 255 pages of
  chapters (8.8 body pages each, 250–420 body lines), 64 of solutions (2.2
  each), ~14 of front and back matter — **11.0 pages all-in per chapter**.
  57 figures, 59 listings, 37 tables, 5 dated boxes, 118 strategy files (outline
  ~114), 232 exercises, 29 weekend problems, 174 interview questions, 98 ledger
  rows, 262 term links (0.8 a page), 226 new Python tests (132 chapter, 94 in 30
  new `firm` components), ~9,800 lines of tested Python. The ch. 10 and ch. 20
  checkpoints projected ~335 and ~325 pages. Real data came from public-domain
  or openly licensed series only (Cboe index histories as derived statistics,
  FRED/H.15/H.10/EIA, CFTC, TreasuryDirect, SMARD), recorded in
  `data/strategies-2/LICENSES.md`; bank-desk chapters (20–29) are synthetic and
  build on earlier books' engines (Book 5's autocallable and convertible
  pricers, Book 6's OAS and energy models, Book 7's cost model, Book 4's deflated
  Sharpe ratio).

- **Books 10–13, written in parallel (2026-09-25/26), one agent per book:**

  | Book | Chapters | Pages | Outline | pp/chapter all-in | Figures | Listings | Dated | Strategy files | Ledger rows | Links |
  |---|---|---|---|---|---|---|---|---|---|---|
  | 10 Microstructure and Execution | 28 | 303 | ~378 | 10.3 | 70 | 55 | 14 | — | 178 | 720 |
  | 11 Market Making and HFT | 29 | 330 | ~396 | 10.9 | 68 | 59 | 19 | 75 | 118 | 361 |
  | 12 Machine Learning for Markets | 29 | 348 | ~392 | 11.5 | 58 | 87 | 3 | — | 168 | 1,000 |
  | 13 Low-Latency Software | 26 | 314 | ~364 | 11.6 | 72 | 80 | 13 | — | 120 | 606 |

  The batch lands 11–20 % under the outline (Books 1–9: 10–16 %). Book 10 spent its first
  day on the shared exchange simulator (`firm.exchsim`, Python + C++20 + Rust, byte-identical on
  a 17,107-record fixture) and wrote shorter chapters afterwards; Book 11's Part II ran at 7–9 body
  pages until the main session asked for depth, after which chapters 22–29 printed at 8–10 with
  three figures each. Budget **10.5–11.5 pages a chapter** for a book of this kind and watch the
  ch. 10 checkpoint: a projection more than 15 % under the outline means chapters are being
  compressed, and a note to the agent at that point recovers pages cheaply. The whole batch —
  Step 0, Phase A, sync, four books, verification — took about eleven hours of wall time.

## 9. Known traps (add to this list as books are written)

- **Confident specifics from memory.** Fee levels, regions, rule numbers,
  dates and sizes are exactly what a language model states fluently and
  wrongly. The ledger rule (6.1) is the only defence; do not skip it for
  "well-known" facts.
- **The label-overlap defect** is invisible to every gate (family rule) —
  order-book and architecture schematics are dense and especially prone.
- **Homograph term links.** Market vocabulary is ordinary English (*book,
  spread, fill, cross*). Budget real time for `STOP`/`EXTRA_PROTECT`
  curation after the linker runs.
- **A term defined twice** in two books links wrongly in both. Check the
  definition map (Phase A) against all written books.
- **Code drift.** A listing's line range silently shifts when the file is
  edited. The `\omcode` range check in `make test-code` catches it — run it
  after any code edit, not only after chapter edits.
- **Figure references.** `omfigure` has no counter of its own: a bare
  `\label` inside it silently points at the enclosing section. Number a
  figure with `\omcaption{...}\label{fig:...}` (added to the style file in
  chapter 3) and only then `\cref` it.
- **`ybar interval` shifts bins.** pgfplots' interval bars drew a histogram
  two bins to the left of its data in chapter 1; the build was green. Plot
  `ybar` on bin centres and compare the rendered peak with the CSV.
- **Legends sit on curves.** Default legend placement landed on a plotted
  line in chapter 2. Put multi-curve legends below the axis
  (`legend columns=N, at={(0.5,-0.3)}, anchor=north`).
- **Arrow labels in narrow gaps.** A label on a short arrow between two
  boxes touches both boxes. Raise it above box height (`above=11pt`) or
  shorten it.
- **Module names collide across chapters.** All chapter tests run in one
  pytest session (`--import-mode=importlib`); teaching modules must have
  unique names, and running-project modules are `firm_<component>.py`.
- **A single seed is not a test.** A statistical property (mean adverse
  selection, 5 % loss frequency) is asserted over many seeds with a
  tolerance, never on one path; and the histogram printed in the book uses
  enough paths that its mean matches the proposition it illustrates (250
  days gave a misleading mean in chapter 1; 1 000 did not).
- **The model's cut-off is a trap even for 'latest' figures.** In chapter 1
  the web check returned FY2025 results and a newer industry report than the
  ones remembered. Always search for the most recent period before writing a
  dated box.
- **TikZ node names with a decimal point.** `\node (v\y)` inside a
  `\foreach \y in {1.8,...}` creates a node called `v1.8`, which TikZ reads as
  node `v1`, anchor `8`: a fatal error. Loop over letters for names and carry
  the coordinate as a second loop variable.
- **Commas inside CSV labels** break `yticklabels from table`; use
  semicolons or parentheses in chart labels. Since chapter 12
  `tools/check_figdata.py` (run by `make test-code`) rejects any chart CSV whose
  rows do not all have the header's number of fields.
- **Histogram bin edges on the values of interest.** Returns capped at exactly
  ±10 % sat on bin edges and landed in different bins on each side, giving
  spikes at −9.5 and +10.5. Centre bins on the special values (edges at
  half-integers), and check symmetry by eye.
- **A regulation can be proposed for repeal while you write about it.** The
  US order protection rule, the backbone of chapter 9, was proposed for
  rescission three months before the chapter was written, after the model's
  cut-off. For every rule a chapter leans on, search for the regulator's
  most recent release, not only for the rule.
- **Web fetch often cannot parse regulator PDFs.** They are saved under the
  session's `tool-results/`; run `pdftotext -layout` on the saved file and
  grep it. This recovered the exact figures for chapters 5, 6 and 9.
- **Accents and primes trip the quote gate.** `B\"orse` and `$\Delta''$` both
  contain the characters the straight-quote and quote-balance gates count.
  Type accented letters directly in UTF-8 (`Börse`) and write double primes as
  a subscript or `\prime\prime`.
- **Stale dated boxes.** A book written over weeks has boxes of different
  ages; the Phase C pass re-verifies anything older than 60 days.
- **A gate that saw nothing has not passed.** Two were found in Book 1's
  Phase C. `tools/test_code.sh` decided whether Python tests existed with
  `find … | grep -q .` under `set -o pipefail`: grep exits at the first line,
  find dies of SIGPIPE, the pipeline is false, and the script printed
  "(no python tests)" and went GREEN for the whole book without running
  pytest (the per-chapter `pytest` calls had been run by hand, so all 336
  passed when finally run together). `check_problem_numbering.py` printed
  "OK (0 chapters)" because it recognised only `bachelor-*`/`grade-*`
  directories. Both now count what they checked and fail on zero. When a new
  gate is added, make it print its count and read the count once.
- **`ruff check --fix >/dev/null` hides what it could not fix.** It hid two
  E501 and a B007 for two chapters. Run `ruff check code | tail -1` and read it.
- **A listing range can stay valid and show the wrong code** after an edit
  above it; `check_omcode` only checks bounds and length (max 40). After any
  edit to a listed file, print the first and last line of every `\omcode`
  range (the one-liner is in `sources/markets-1/PROGRESS.md`) and read them.
- **A toy model can carry the chapter's argument on a discretisation
  artefact.** Chapter 31's first crash model gave 8.6 % only because depth was
  refreshed once a minute; sub-stepped, it either did nothing or collapsed, and
  the "churn" feedback *reduced* the fall. The exercise that asked the reader
  to switch the feedbacks off one at a time is what exposed it. Rule: every
  simulation that a caption or a named result leans on gets (i) a test that
  the result is stable when the time step is divided by four, and (ii) an
  ablation of each mechanism the text credits, asserted in `test_solutions.py`.
- **The term linker's `EXTRA_PROTECT` must come before `BASE_PROTECT`.** The
  alternation is leftmost-first, so the generic `\begin{…}` rule consumed the
  opening of `omsources` and `dated` and the book's whole-environment masks
  never matched: links appeared inside the titles of other people's documents.
  Fixed in `tools/termlink/protect.py`. Book 1 masks `\texttt{}`, `\omcode`
  captions, `omsources`, `dated` titles, `\bfield{}` and the phrase
  "basis points". `tools/term_config/lang_en.py` was missing from the bootstrap.
- **Market vocabulary is ordinary English.** Unfiltered, 333 terms gave 4,650
  links (12 a page). About forty one-word terms (order, share, exchange,
  position, basis, premium, roll, tick, special, recall, agent, principal …)
  go in `STOP` with their capitalised forms (linked only in their defining
  chapter) or `DROP`; that brought Book 1 to 1,647.
- **A term defined in two chapters is dropped by the linker and fails the book
  gate** ("price limit", for shares in chapter 12 and futures in chapter 18).
  The later chapter re-uses the term with a `\cref` to the first definition
  and no `\emph{…}\index{…}` pair.
- **PGF:** a comma inside a `\foreach` item is fatal (brace the item);
  `xtick={1,...,16}` trips the ellipsis gate (write the list out); `booktabs`
  and the `groupplots` library had to be added to the style.
- **Sources that cannot be fetched by script:** cmegroup.com (specs, rulebook,
  fee schedules), theocc.com, the CFTC glossary, jpx.co.jp, some index-provider
  PDFs. Substitutes that worked: CFTC-hosted rule filings
  (`cftc.gov/filings/orgrules/…` + `pdftotext`), the CME client-systems wiki on
  atlassian.net, clearing-member and broker specification pages (logged as
  secondary sources), and for sec.gov PDFs `curl -A "<name> <email>"` then
  `pdftotext -layout`. A search engine's summary of a table can garble its
  columns (OPRA, chapter 24): take numbers from the document, not the summary.
- **Units and instants.** Two review catches that no gate sees: notional
  turnover printed in billions that was in trillions (chapter 27), and a
  problem that treated 15:00 Chicago and 16:00 New York as different instants
  (chapter 18). Put the unit in the test's variable name and convert every
  clock time to UTC before comparing.
- **Book 2 traps (2026-09-24).** Each cost at least one rebuild or a wrong
  number caught late:
  - *Data files have real holes and real misalignments.* FRED's CPI has no
    October 2025 (no prices collected during the 2025 lapse in
    appropriations), and the employment report for that month was never
    published; `paste` of a daily-with-weekends series against a business-day
    one misaligned rows. Join by date, and test every data file's row count.
  - *A PDF table flattened by `pdftotext` scrambles its columns.* The Lehman
    bond price "on the day of default" was first read as 13; it is 34. Rebuild
    each row from a second column (a return, a total) before quoting a cell.
  - *Check which quantity a closed form describes before simulating it.*
    $\alpha^{2/c-1}$ is the chance of ever falling to $\alpha$ of the start, not
    of the running peak; the first simulation disagreed completely.
  - *Compare settings on common random numbers.* The best market width of
    chapter 30 moved by more than its grid step between independent runs; deal
    once and replay every width on the same deals.
  - *Propositions drafted from memory fail on the build's conventions* (the
    sign of asset-swap spread minus Z-spread, the senior tranche's monotonicity
    in correlation). Run the code before stating a comparative claim.
  - *PGF:* a comma inside a `\legend` entry splits it and shifts every later
    label (brace it); a `/` inside a `\foreach` item splits it; a TikZ style
    named after a built-in key (`step`) is fatal; `/pgf/number format/.cd` in a
    tick-label style breaks once pgfplots adds a scale label (spell the keys
    out); `\captionof` does not exist (tables are `center` + `tabular`).
  - *Listings are capped at 40 lines;* split a long function into two ranges,
    and print both ends with `tools/omcode_ends.py` after every `ruff --fix`.
  - *Series-wide collisions:* *adverse selection* was planned again although
    Book 1 defines it; grep `\index{term}` over every written book before each
    chapter's definitions. Two terms planned in Phase A (*implied policy path*,
    *reverse repo facility*) were never given their definitions; the Phase C
    check of `DEFINITIONS.md` against the harvested `\index` entries found
    them.
  - *Linker density:* unfiltered, Book 2 got 2,166 links (7.5 a page).
    Everyday and very frequent words (*coupon, par, DV01, reserves, cap,
    floor, gilt, convexity, annuity …*) went in `STOP`, a few in `DROP`
    (*width, edge, turn, tail, pack, bundle, inventory*), and hyphenated
    compounds (*zero-coupon, fat-tailed*) in `EXTRA_PROTECT`: 1,388.
  - *Many regulator sites refuse scripted downloads* (BIS PDFs, SSRN, the
    Senate, the Swiss courts, spglobal.com). What worked: WebFetch's saved
    binary plus `pdftotext`, arXiv copies of papers, eCFR's API for rule text,
    law-firm client alerts for court holdings, and the Fed, SEC and BLS sites
    with a user agent.
- **Books 3–6 batch traps (2026-09-24, four books written in parallel).**
  - *The web-search budget is per session and shared by every subagent.* It
    defaulted to 200 WebSearch calls and ran out in the batch's first hours
    (Book 6 at ch. 11, Book 5 at ch. 12, Book 3 at ch. 15). Books 3 and 6
    then dropped 101 and 65 facts as unverifiable. Before a batch, set
    `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` (the user's settings now carry
    2000; the change took effect mid-session). Fallbacks that worked without
    search: the Crossref API (`api.crossref.org/works/<doi>`), the arXiv API,
    Wikipedia raw text (`?action=raw`) as a map to primary references,
    CourtListener's RECAP API, EDGAR full-text search with a user agent,
    GitBook/Mintlify `llms.txt` and `.md` page variants, GitHub raw docs, FRED
    CSVs (`fredgraph.csv?id=`), and `publications.europa.eu/resource/celex/<CELEX>`
    with `Accept: application/xhtml+xml` for EU law.
  - *Resolve the books' definition maps before any prose.* At the Phase A sync,
    Books 3–6 planned 1,790 terms; four collided (*equivalent martingale
    measure*, *risk-neutral measure*, *calibration*, *copula*), all resolved
    to Book 4 by one ownership rule; `sources/SERIES_DEFINITIONS.md` records
    the map. The series notation (`CONTRIBUTING.md`) and the Book 5 → Book 6
    pricing interface (`code/firm/INTERFACES.md`) were frozen at the same
    sync, and Book 6's risk engine then ran on Book 5's real library with no
    stub, although both books were written at the same time.
  - *Shared checks go red on another book's half-written files.* The
    repo-wide parts of `make test-code` (ruff over `code/`, module names,
    chart CSVs) read other agents' work in progress; rerun before
    investigating. `check_figdata.py` crashed on a transient empty CSV and now
    reports it instead.
  - *Overlapping `latexmk` runs on one entry file corrupt its `.aux`/`.toc`*,
    and a figure crop taken while another build rewrites the PDF can return a
    page of a different book: check the running header of every crop, never
    wrap `latexmk` in a short timeout, and recover by deleting the entry's
    `.aux .toc .out .fdb_latexmk` and rebuilding. Crops go to a per-book
    subdirectory of the (shared) scratchpad.
  - *`\label` after `\omcode` labelled the enclosing section, in every book.*
    `listings` typesets inside its own group, so `lst:` labels resolved to the
    section or tutorial step (Book 6 printed "Section 1.2" for a listing).
    `\omcode` now absorbs a directly following `\label` and passes it as
    `label=`; all six books were rebuilt and every `lst:` label resolves as a
    listing. No gate saw it: `\cref` to a wrong object is not "undefined".
  - *Gates fixed during the batch:* the "defined twice" harvest missed
    `\emph{…}\index{…}` pairs broken across a line (46 in Books 1–2; now a
    multi-line perl harvest); the firm-name gate matched substrings ("Virtu"
    in "Virtual", "Bitwise" in "bitwise reproducibility"; now whole words, and
    `#` comment lines are skipped); `make_briefs.py` stubs made an overfull
    `\vbox` at 28+ chapters (now `\mbox{}`). Still open: the quote-balance gate
    counts the prime pair `''` in mathematics as a closing quote (write
    `f^{\prime\prime}`); `make test-code` never runs the `fig_*.py` scripts, so
    a script broken by `ruff --fix` reordering its imports passes it and fails
    only `make figdata` — run both.
  - *Numbers:* a product printed from rounded factors must equal the printed
    factors' product (7.30 × 3 000 printed as 21 890, from the unrounded
    7.297; Book 3 ch. 5): print "about" or both values. Memorised numerical
    constants are facts too (a Rust `erfc` typed from memory did not compile
    and its coefficients were wrong): derive or test against a library. A
    Monte Carlo time grid must contain the period's start and end dates (a
    caplet came out 6 % low with a tight standard error). Least-squares
    Monte Carlo priced on its own training paths is biased above the dual
    bound. Monotone convex interpolation is not linear in its inputs: 1 bp
    bucket bumps summed to 866k against a 555k parallel DV01 (bump 0.01 bp and
    scale). A comparative claim drafted from intuition was backwards again
    (a high borrow fee makes early exercise of puts *less* likely: it acts as
    a dividend yield) — run the pricer before stating a direction.
  - *Running-project code:* Book 2's `firm_curve.bootstrap` bisected ln P in
    [−1, 0], silently wrong beyond P < 1/e (a 30-year at 4 %) and for negative
    rates; now [−5, 1]. `listings` cannot print UTF-8 (`€STR` in a listed
    docstring was fatal): write ASCII in code files. `ruff --fix` removes an
    import unused *at that moment*, and a function appended later fails at
    run time.
  - *Captions:* write them from the rendered figure (three drafted captions
    in one chapter described curves the chart did not show). Named theorems
    are not linker terms: keep them out of `defines`.
  - *PGF, again:* a comma in a `\legend` entry, `ybar interval` histograms,
    `xtick={1,...,11}` (write ticks out), axes in the tens of thousands need
    `xtick`, `xticklabels` and `scaled x ticks=false` together; `groupplots`
    rejects `bar width` in the group options (put it in each
    `\nextgroupplot`); a long label on the horizontal leg of a `-|` path runs
    over its start node.

- **Book 7 (Research Craft), written chapter by chapter in the main session:**
  - *Simulated evidence:* one simulated market is one draw. A planted effect
    was invisible in one seed and found in seven of ten; a design's single
    60-day experiment sat 2.7 standard errors from its truth. Report detection
    rates over seeds and designs as mean and spread over many runs. Changing a
    simulator's size (days, names) reruns the whole random stream: vary seeds,
    not lengths. Check that a planned demonstration can show its effect before
    writing it into a brief, and replace a hook the simulation does not
    reproduce with the pathology it does produce (Book 7's hooks for ch. 25 and
    26 were rewritten: "45 % of the book in two stocks" became a gross of 61
    times capital; "a third of the gross for one basis point" became 0.03 %,
    and 24 % for a redrawn forecast).
  - *Point in time inside the simulator:* `firm.synthmkt`'s `Panel.style_x`
    holds the last day's exposures (value moves daily, momentum monthly); a
    risk model on them looked calibrated with a momentum factor of 3.3 %
    volatility instead of 7.2 %. Use `point_in_time_styles`. A style whose
    exposure is constant during a warm-up has a zero-variance factor, and any
    ratio to its variance explodes (a regime multiplier of 2.5e7): start
    models when every exposure exists.
  - *Performance:* numpy's BLAS threads on many small matrices turned a
    12-second study into 6.5 minutes and 135 CPU-minutes; `tools/test_code.sh`
    and `tools/figdata.sh` now export `OPENBLAS_NUM_THREADS=1`. A figure
    script that imports numpy before its study module escapes a pin set inside
    the module.
  - *Estimators:* a homoskedastic standard error on a cost fit whose noise
    grows with order size was 2.9 standard errors off; use robust errors. The
    unweighted mean of cluster means estimates a different quantity from the
    rollout when clusters are unequal; weight by observations. A common shock
    across clusters makes the cluster-robust error too small until the analysis
    is stratified by it. An MA smoothing profile and its time reversal share
    their autocorrelations: restrict to invertible profiles. Hierarchical risk
    parity bisects by position in the dendrogram's order, not by cluster.
  - *Honesty in text:* say both halves of a mixed result (a ranking that
    correlates at 0.33 while its argmax concentrates noise); do not claim two
    simulated streams have equal volatility when crash-dominated volatility
    differs by seed; never print solver timings, which are machine-dependent.
  - *Linker:* a definition that emphasises a word other than its indexed term
    (`\emph{symmetrically}\index{symmetric orthogonalisation}`) becomes a
    one-word linkable term; emphasise exactly the indexed phrase.
  - *Rounding and typos, again:* 0.0825 → 0.082, 0.7885 → 0.788, 0.965 → 0.96:
    print from the test's rounding; `\end{solution>` was typed four times.

- **Book 8 (Strategies I), written chapter by chapter in the main session:**
  - *Planted effects are too strong at first, every time.* The first setting
    of a planted edge gave Sharpe ratios of 4 to 18 in eight chapters (options
    signals 7, alternative data 18, news 7.6, cross-asset diffusion 4–6, a
    trend book at 0.35 vol units 0.5 but a crash that drowned in noise). Tune
    the plant until the strategy's Sharpe ratio is in the range the public
    record suggests (0.3–1.5 after costs), then report the untoned version as
    an exercise; say in the text when a synthetic number is an upper bound.
  - *Real data contradicts hooks.* Three hooks from the outline (record
    speculative longs precede falls; "trillions" in volatility targeting; a
    pod shop's thresholds) had no citable source, and one was contradicted by
    the book's own data (CFTC corn positioning 2017–2026). Rewrite the hook
    around what the sources and data show.
  - *Simple versus log returns.* `firm.synthmkt`'s `ret` is simple: summing
    scaled simple returns as log increments gave high-volatility names a
    variance drag that looked like reversal after limit-up days. Compound with
    `log1p`.
  - *Generic futures series.* EIA contract 1 changes identity the day after
    each expiry; a spread on the generic series books the roll as P&L. Follow
    contracts by serial number (`firm.curvestrat.serials`). Contract 1 was
    negative on 20 April 2020: take logs only of contracts clear of expiry.
  - *Evaluation grid.* A weekly report evaluated on a weekly grid makes a
    three-day publication lag invisible (lag 0 and lag 3 fall between the same
    evaluation days); evaluate daily and correct t-statistics for overlap.
  - *pytest collects anything named `test_*`,* including a library function
    `test_rules` imported into a test file: name library functions otherwise.
  - *Intraday Sharpe ratios are meaningless* for thousands of trades a day
    with a positive mean (a "Sharpe ratio" of 500): report per-trade edge,
    hit rate and the share of days positive.
  - *Hindsight parameters:* when a filter or threshold is chosen after seeing
    the crisis it avoids (a storage filter chosen on 2020), print all the
    candidates and say which one hindsight picked.
  - *Message-level simulation is too slow for years of sessions:* use bars,
    and take the trading cost from a tape session (half the time-weighted
    spread).
  - *PGF:* a legend placed inside the axis covers bars and lines more often
    than not in these charts; put multi-entry legends below the axis
    (`legend columns`, `at={(0.5,-0.3)}`); `xtick={1,...,12}` trips the
    `...` gate; `scaled y ticks=false` for small ICs.
- **Book 9 (Strategies II), written chapter by chapter in the main session:**
  - *Measure path by path, not only in expectation.* Per-path present values of a
    security are not a risk measure (hedging them made the spread larger in ch.
    20); show hedged values against scenarios instead. Where a programme has a
    pathwise guarantee (rolling intrinsic never below the static hedge without
    costs), test the guarantee and then break it with costs, at equal costs for
    both programmes.
  - *Execution at the signal is a free lunch.* Index arbitrage executed at the
    observed mispricing never lost; a one-minute lag turned the edge into a race,
    five minutes into a loss. The same trap in daily data: Brent-WTI spot
    assessments close at different times, so a spread's daily changes
    autocorrelate (−0.36) and a same-close fade shows a Sharpe ratio of 0.85
    that becomes 0.32 a day late. Always rerun a rule a day (or a tick) later.
  - *Planted structure must leave room for the test to fail.* Tiering clients by
    mark-out alone did not beat the best flat price when every client of a type
    shared one competing quote; a surveillance detector caught 100 % of planted
    spoofers until legitimate look-alikes (deep-book providers, quote
    refreshers) were added. Plant the confounders the real world has.
  - *Calibrate to a published figure, and say so.* The QIS chapter's true Sharpe
    ratios were set so that the median backtest-to-live decay matched the 73 %
    reported for bank strategies; the text states the calibration.
  - *Sample estimation noise directly* (Sharpe ratio error 1/sqrt(T)) when only
    statistics are needed: 2,000 simulated product teams in under a second.
  - *Chapter gates run ruff on the chapter's code, not on `code/firm/`:* run
    `ruff check code/firm/<component>` after every edit to a firm module, then
    `omcode_ends.py` (docstring rewraps shift every listing below them).
  - *`\euro` inside math mode prints a pound sign;* write `$-$\euro250`. A
    straight quote in `\texttt{policy("flat", 0.8)}` fails the quote gate.
  - *Blocked sources:* justice.gov and EUR-Lex refuse automated fetches; cite
    the court opinion (media.ca7.uscourts.gov) and legislation.gov.uk's
    as-adopted EU text instead. FRED's daily Henry Hub series is sparse before
    2007. Crossref answers 429 when queried back to back: sleep between calls.
  - *Manipulation chapters* follow section 6.3 with nine fields renamed (who is
    harmed, how it works, why it is illegal, enforcement case, detector, how it
    is caught, evaluating the detector honestly); plant only the patterns in the
    enforcement records and model no manipulation's profit.
  - *A one-page index can overflow* (a 26 pt overfull vbox while `\output` is
    active with 74 entries); it cleared once the last chapters added entries.
    Recheck the log gate after the final chapter, not only per chapter.

- **Books 10–13 batch traps (2026-09-25/26, four books in parallel):**
  - *Resources.* Four agents plus a full-repo `make test-code` exhausted the 19 GB laptop (pytest
    OOM-killed; one generator at 8 GB). Put caps in the batch file from the start: ≤ ~1.5 GB and one
    core per process, BLAS/torch/LightGBM threads = 1, no multiprocessing or `make -j`, one heavy job
    per agent, `nice -n 19`, large generated data streamed to disk and made once, late; the main
    session runs only per-book checks while agents write. `pkill -f name` kills the shell whose own
    command line contains `name`: kill by PID.
  - *A result that depends on the BLAS thread count is not reproducible.* Book 4 ch. 25 printed 1,909
    conjugate-gradient iterations, the multithreaded count; under the `OPENBLAS_NUM_THREADS=1` pin that
    Book 7 added to `test_code.sh`/`figdata.sh` it is 1,884 (four threads: 1,900), so its test and its
    chart CSV had silently stopped reproducing. Print ill-conditioned iterative counts as "about", and
    run a new book's figure scripts under the pin before committing CSVs.
  - *Shared simulator first.* Freezing `firm.exchsim` at the sync (MoldUDP64 feed, SoupBinTCP/OUCH-style
    order entry, `schema.json`, golden fixtures, `STATUS.md`) let Book 13 generate its codecs, Book 11
    run its venue playbook and Book 12 serve a model on the same venue while all were written at once.
    Consumers still found costs the producer did not: `Ctx.working()` scans every order ever sent
    (O(n²) for a re-quoting agent), the throttle is per session and also throttles the tape background,
    and client order ids are per session (a multi-venue agent sets its own).
  - *Measured data* lives in `bench_*.py` → `measured_*.csv` + `.meta` (machine, compiler, load), never
    regenerated by `make figdata`; prose numbers from it need a final pass on a quiet machine, because
    measurements taken while other agents ran moved by more than their tests' tolerances.
  - *Quoting a CSV label does not make a comma safe:* pgfplots ignores CSV quoting, so
    `check_figdata.py` is right to reject any comma; `np.genfromtxt` breaks on them too.
  - *Module names are unique repo-wide* (`check_module_names.py`): generic helper names such as
    `make_fixture.py` collide across books; prefix them with the component.
  - *Honest nulls.* Book 10's execution algorithm does not beat TWAP on average (−0.15 bp, CI
    [−0.44, 0.14]); Book 12's order-book model loses its edge past about 100 ms because the simulated
    market updates about four times a second. Both were reported, not tuned away: a synthetic market
    whose event rate is far below a real one cannot show microsecond effects, and the text must say so.
  - *Simulator agents:* a market maker that quotes off a top of book that includes its own quotes walks
    them away; identify your own orders by the acknowledgement reference and set `ack_ns < data_ns`,
    or pending-quantity bookkeeping oscillates into a requote storm; a multi-venue algorithm must read
    the consolidated touch; count pending cancels at once, or a "never beyond the order" control
    blocks the catch-up cross; compare execution algorithms all-in (fees moved −0.47 to −0.15 bp).
  - *Statistics:* trade-sign autocorrelation counts one sign per aggressive order, not per print;
    first-alarm delays of a drift monitor at one false page a month are dominated by false alarms —
    report a blind monitor's column; calibrate a CUSUM on long no-failure history; an always-valid
    test with a 3-day standard error needs a burn-in; `firm.perp.funding_payment` is paid by the holder.
  - *Systems (Book 13):* keep listed lines under ~104 characters (the overfull warning names the
    included file's lines); a clock read costs ~18 ns with `rdtscp`; attribute stage latency on the
    first order of each event; stop allocation counters before copying results out of the thread;
    derive identifiers from the journal, never a per-process counter; CI's g++ is 13 while local is
    11.4 — stay `-Werror`-clean on both, runtime-dispatch AVX2.
  - *Earlier-book defects found:* Book 6 `firm.modelval.binomial_tail` overflows for n in the
    thousands; Book 7 `firm_abtest.msprt` warns on overflow for overwhelming statistics; the firm-name
    gate still fires on the ordinary word "Bitwise" at the start of a sentence.

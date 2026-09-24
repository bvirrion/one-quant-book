# Book 1 — progress and working conventions (resume here)

Plan: `~/.claude/plans/read-you-writing-a-quant-book-md-instruc-wondrous-acorn.md`.
User decisions: whole book, no stop; full source ledger (every checkable fact web-verified).

## Status

| ch | state |
|---|---|
| bootstrap | done (style, envs, Makefile, gates, CI, venv) |
| Phase A | done (31 briefs in `sources/markets-1/NN-*.md`, DEFINITIONS.md, skeleton) |
| 1–30 | **done**: text, solutions, code, tests, ledger, gates green, figures checked (FIGURES.md) |
| 31 | **done** (toy crash model rebuilt once: see its ledger EXCLUDED) |
| Phase C | **done** 2026-09-19: linker (1,647 links, STOP/DROP/EXTRA_PROTECT curated), `gates.sh book` green, figdata stable, 336 tests, listing first/last lines read, forward book references checked against OUTLINE (3 fixed), flagged facts resolved (1987 skew, KOSPI, CL tick) |
| Phase D | **done** 2026-09-19: docs, calibration, traps, memory; `code/_specimen` deleted |
| open for a human | CME fee levels in ch. 30 come from a broker page (secondary); CME announced fee changes from 2026-10-01; ITCH `P` message layout recalled, not checked; outline ch. 12 mentions Taiwan with no verified content in the text beyond one qualitative clause |

## Per-chapter cycle (what "done" means)

1. WebSearch/WebFetch the brief's "facts to verify" → decide dated boxes.
2. `code/markets-1/NN-slug/python/<unique_module>.py` + `fig_*.py` + `tests/test_<module>.py`;
   build under `code/firm/<component>/firm_<component>.py` + `tests/`.
3. Chapter tex: hook; 3–5 sections; definitions with `\emph{t}\index{t}` for every term in the
   brief's Defines list (terms may be added; keep DEFINITIONS.md unique); 4 figures with
   `\omcaption{...}\label{fig:...}`; tutorial (`\section{Tutorial: ...}\label{tut:...}` +
   `tutorial`/`tutsteps` + `\omcode`); build (`\label{bld:...}` + `build`/`\bfield`);
   `omsources`; 8 exercises 3/3/2 (7 = Coding, 8 = Find the flaw); one 20-question problem in
   Parts I–IV with a **named result** as question 19; 6 interview questions with `\iqroles`.
4. Compute every number with a script, then `tests/test_solutions.py` asserts them.
5. Solutions tex (`\iqlookfor` closes each interview solution).
6. Ledger rows `| F<n> | claim | source | URL | 2026-MM-DD | evidence | used in |` + EXCLUDED list.
7. `latexmk -silent …; tools/gates.sh log; tools/gates.sh chapter markets-1/NN-slug; make test-code`.
   (The one remaining `Overfull \vbox` is the empty-solutions stub artifact; it goes when all
   solutions exist.)
8. `tools/figcrop.py "<caption words>" out [height_pt]` per figure, read, fix, log in FIGURES.md.

## Conventions learned (also in WRITING_A_QUANT_BOOK.md §9)

- No straight quotes anywhere (not even inside `\texttt`); no `...`.
- Legends below the axis; arrow labels `above=11pt` in narrow gaps; explicit `xtick` on wide
  money axes; histograms as `ybar` on bin centres.
- Illustrative parameters are labelled illustrative; real numbers only from the ledger.
- Named firms must appear in the chapter's ledger (`tools/firm_names.txt` gate).
- Body target: 12 pp → ~520 lines, 14 pp → ~620, 16 pp → ~720; solutions 160–200.

## Notes for Phase D (traps found after chapter 13)

- **Never pipe `ruff check --fix` to /dev/null**: it hid two E501 and a B007 for two chapters; `make test-code` went RED only when run in full. Run `ruff check code | tail -1` and read it.
- **A listing range can stay valid and point at the wrong code** after an edit above it (chapter 21: `rolled_index` moved from 41 to 45, `check_omcode` still green). After any edit to a listed file, print the first and last line of every `\omcode` range (one-liner in the chapter-21 session) and check that each starts at a `def`/`class`/constant and ends at a `return`. Candidate for a stricter `check_omcode.py`.
- A comma inside a `\foreach` item (`Friday, later`) is a fatal PGF error: brace the item.
- `xtick={1,...,16}` trips the ellipsis gate: write the list out.
- `booktabs` was not loaded by the style until chapter 18 (first table).
- CME's own pages (contract specs, rulebook PDFs, articles) cannot be fetched by script (JSON error page / timeouts). Workable substitutes: CFTC-hosted rule filings (`cftc.gov/filings/orgrules/...`, pdftotext), the CME client-systems wiki on atlassian.net, Eurex and ICE product pages, which fetch normally.

# Book 2 — progress and working conventions (resume here)

Plan: `~/.claude/plans/read-one-quant-book-writing-a-quant-book-spicy-wadler.md`.
User decisions (2026-09-23): same run mode as Book 1 — whole book, no stop; full
source ledger (every checkable fact web-verified).

## Status

| ch | state |
|---|---|
| Step 0 (tooling made book-aware) | done 2026-09-23 |
| Phase A | done 2026-09-23 (31 briefs, DEFINITIONS.md 271 terms, no Book 1 collision, skeleton) |
| 1-6 | done 2026-09-23: text, solutions, code (rfr, mmyield, bond in Python + C++20 + Rust, tsyauction, repo, ctd), ledgers, gates green, figures checked |
| 7-31 | done 2026-09-23: sovspread, meetings, curve, ccpbasis, breakeven, prepay, normalvol, fxpairs, lastlook, fxfwd, fixflow, ndf, fxsmile, settlerisk, spreads, rfq, cds (Py+C++20+Rust), tranche, waterfall, recovery, pblimits (C++20+Rust+Py), clearcost, sizing, mmgame, macrocal; same gates; ch. 11 found the October 2025 CPI gap (shutdown) and reproduced Treasury's contingency index 325.604 |

| Phase C | done 2026-09-24: linker curated (2,166 -> 1,388 links), two missing definitions added (implied policy path, reverse repo facility), cross-book references fixed (Books 13, 16, 5 and 6), gates book markets-1 and markets-2 green, make figdata reproducible, make test-code green (670 tests) |
| Phase D | done 2026-09-24: 363 pp; outline/markets.md, OUTLINE.md, CLAUDE.md, WRITING_A_QUANT_BOOK.md sections 8-9, root CLAUDE.md, memory note updated; nothing committed |

## Per-chapter cycle

Same as `sources/markets-1/PROGRESS.md`. Figures: `OQB_BOOK=2 tools/figcrop.py …`.
Gates: `tools/gates.sh chapter markets-2/NN-slug`, `tools/gates.sh log markets-2`,
`make test-code CH=markets-2/NN-slug`.

## Calibration

- After ch. 3 (2026-09-23): body 10 / 9 / 9 pp, solutions 2.3 / 2.8 / 2.6 pp: **11.9 pp all-in per
  chapter** (body 603 / 494 / 468 lines, solutions 206 / 177 / 160). Projection 31 x 11.9 + 20 = ~389 pp
  against the outline's ~412 (-6 %, inside the gate). Same density as Book 1; keep going.
- After ch. 10 (2026-09-23): chapter starts 2/12/21/30/40/49/58/67/76/84/92 -> body 10, 9, 9, 10, 9,
  9, 9, 9, 8, 8 pp (90 for ten chapters) plus ~2.5 pp of solutions each: **11.5 pp all-in**.
  Projection 31 x 11.5 + 20 = ~377 pp, -8.5 % against 412: at the edge of the gate. Chapters 9 and
  10 came out at 8 body pages (394 body lines in ch. 10); aim for 9-10 body pages (450-550 body
  lines) from ch. 11 on, by depth (worked examples, one more figure where it teaches), not padding.
- After ch. 20 (2026-09-23): chapters 11-20 took 89 body pages (8.9 each), 179 for twenty chapters;
  the PDF is 252 pages with eleven solution stubs. All-in still ~11.5 pp/chapter, projection ~377 pp
  (-8.5% against 412). Chapters that came out short (13, 15, 17, 18, 19, 20) were brought to four
  figures and ~430-470 body lines before closing; Part IV (credit) and Part V carry more numbers and
  should run to 9-10 pages.

## Tools added for Book 2

- `tools/omcode_ends.py [filter]` prints the first and last line of every listing range (the Book 1
  trap "a range can stay valid and show the wrong code"). Run it after any edit to a listed file,
  and after every `ruff check --fix`, which can delete blank lines and shift ranges (it did in ch. 3).
- `tools/check_omcode.py <filter>` now also matches the chapter file's path, so a chapter whose
  listings live in `code/firm/` is not checked over zero listings.

## Traps met in Book 2 (for WRITING_A_QUANT_BOOK.md section 9 at delivery)

- `paste` of FRED series with different calendars (daily-with-weekends target range against
  business-day SOFR) silently misaligned rows; join by date (ch. 5).
- The numbers gate caught four off-by-one roundings in chapters 5 and 6 (327,831 vs 327,830;
  99.13 vs 99.14; 0.528 vs 0.527): write the printed number from the test's output, not from an
  earlier exploratory print.
- Book 1's ledger already held the ZN contract grade "6y6m to under 8y" from a 2025 CBOT filing:
  the model's memory said 6.5 to 10 years. Always reuse and re-read the earlier ledger.
- Fraction glyphs: `\textseveneighths` does not exist; write coupons as decimals (4.125%).
- FRED series can have holes that are real events: CPIAUCNS has no October 2025 (BLS collected no
  prices during the 2025 lapse in appropriations). Test the row count of every data file, and let
  estimators skip incomplete years explicitly (ch. 11).
- `{1,...,12}` in pgfplots `xtick` trips the "drafty ..." gate: write the list out.
- Phase A's "no Book 1 collision" check missed one: *adverse selection* is defined in Book 1, ch. 1, and
  was planned again for Book 2, ch. 15 (now a use; *mark-out* defined instead). Grep
  `\index{term}` over parts/markets-1 before writing each chapter's definitions.
- A number quoted in prose but not asserted slipped (13: "216%" for 215.2). Assert every number the
  text prints, including those in figure annotations and captions.
- A `/` inside a TikZ `\foreach` item (e.g. "WM/Reuters") splits the item: brace it or draw the
  nodes explicitly (ch. 17). The same trap as Book 1's `\foreach` in axes, in another guise.
- `\captionof` is not available (no caption package): tables follow Book 1, `center` + `tabular` with
  a footnotesize note, referred to as "the table below" (ch. 18).
- A proposition drafted from memory ("the asset-swap spread exceeds the Z-spread below par, falls
  short above") was false for the build's conventions: the numbers showed the gap is not signed by
  price. Run the code before stating a comparative claim, and state only what it shows (ch. 21).
- Licensed index data (ICE BofA, Moody's spreads on FRED) are not redistributed: public substitutes
  (Treasury HQM curve) are used and the dated box says so (ch. 21).
- A figure budget of ~4: chapters 5 and 6 first came out with three; count before the gates.
- Parse a PDF table's columns before quoting one cell: pdftotext flattened SR372's Table 2 and the
  Lehman "day of default" price was first read as 13 (it is 34; 13 is the day before the auction).
  Re-derive each row from a second column (here the return column, -62%) (ch. 23).
- A comma inside a pgfplots \legend entry splits it: every later label shifts by one and the
  last disappears. Brace entries with commas (ch. 28). A TikZ style must not be named after a
  built-in key ("step" was fatal, ch. 25). \omcode ranges are capped at 40 lines: split long
  functions into two listings (ch. 25).
- Check which quantity a closed form describes before simulating it: alpha^(2/c-1) is the chance
  of ever falling to alpha of the START, not of the running peak (drawdowns from the peak recur
  almost surely); the first simulation disagreed completely and exposed it (ch. 29).
- Compare widths (or any parameter) on common random numbers: deal once, replay every setting on
  the same deals; the argmax of independent runs moved by more than its own step (ch. 30).
- "/pgf/number format/.cd" inside yticklabel style breaks when pgfplots adds a tick-scale label:
  spell the keys in full (ch. 30). Chapter 30's numbers gate takes ~40 s: simulation-heavy.

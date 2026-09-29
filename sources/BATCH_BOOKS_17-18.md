# Batch run: One Quant Books 17, 18 (prepared 2026-09-29)

Two books are written in parallel in this one working tree, one agent per book. The user's rule for Books
14–18 (2026-09-28) is one subagent per book and **at most three books at the same time**, in batches
{14, 15, 16} and then {17, 18}. This file is owned by the main session; book agents read it and never edit it.
The ownership, git, build, test-scoping, module-prefix, cross-reference and crop rules of
`sources/BATCH_BOOKS_14-16.md` ("Ownership rules", 1–11) apply here word for word. Read them there.

| Book | Entry file | Slug | Label prefix | Teaching-module prefix | Chapters |
|---|---|---|---|---|---|
| 17 The Industry: Firms, Roles and Careers | `one_quant_book_17_industry.tex` | `industry` | `in` | `in_` | 30 |
| 18 The Interview Book | `one_quant_book_18_interviews.tex` | `interviews` | `iv` | `iv_` | 29 |

Already done by the main session (Step 0b):
- the two entry files, `latexmkrc`, `tools/termlink/books.py` (`--book 17`, `--book 18`), the `Makefile`
  gate list, and the slug map in `tools/gates.sh`;
- part-title keys in `styles/lang/en.tex`;
- linker configs `tools/term_config/book{17,18}_en.py`, copied from Book 16's;
- `\iqfirm{…}` in `onequant.sty`, and the Book 18 branch of `tools/gates.sh chapter`;
- `openpyxl` installed in `.venv` and pinned (Book 17's spreadsheets; read them in `read_only` mode, streamed);
- `tools/make_briefs.py`: `tutorial`, `build` and `problem` are optional, and there is a new optional `bank`
  field (Book 18).

Part keys (use them in `tools/briefs/book<N>.py`, `PARTS`, in the shape of `tools/briefs/book16.py`):

- Book 17: `part.in.landscape`, `part.in.money`, `part.in.roles`, `part.in.life`
- Book 18: `part.iv.process`, `part.iv.quant`, `part.iv.research`, `part.iv.programming`, `part.iv.person`

## User rulings for this batch

1. **Book 18 asks new questions only** (2026-09-28). It does not reprint, harvest or index the interview
   questions of Books 1–17.
2. **Book 18's chapter shape.**
   - The hook, then a short **method lesson** of 2–4 pp: the families of questions, the method for each,
     and worked examples as `example` boxes.
   - Then **one bank of about 12–15 `interviewq`**, ramped ★ → ★★★. Every question carries
     `\iqroles{…}` (from `trader, researcher, developer, mle, bank, risk`) and `\iqfirm{…}` (firm type:
     market maker, proprietary firm, multi-manager fund, systematic fund, bank, asset manager,
     crypto firm, any).
   - Then `omsources`.
   - There are **no** `Exercises`, weekend problem, tutorial or build sections. A programming chapter
     may keep a short tutorial if it earns its place.
   - Part I and ch. 28 carry 8–12 questions. **Ch. 29** is six transcribed mock interviews with assessor
     commentary; its questions are `interviewq` inside the transcripts.
   - The gate accepts 6–18 per chapter, and requires `\iqroles` and `\iqfirm` on every question and an
     `\iqlookfor{…}` in every solution.
   - Target **~8 pp a chapter all-in, ~240 pp** for the book.
3. **Book 17 numbers.** Every number is dated, sourced to a public document and given as a range. Firm
   profiles use only public sources: filings, annual reports, regulatory disclosures, the firms' own
   publications and reputable press. There is one ledger row per named-firm attribution.
4. **No proprietary tools when an open one exists** (user preference, 2026-09-28).

## Book-specific rules

**Book 17 (industry):**
- **Pay data.**
  - US: the Department of Labor's LCA disclosure data (public domain). Derive small statistics, such as
    ranges by employer type, role family and year, with a script under `code/industry/`.
  - Commit only the derived tables, under `data/industry/` with `LICENSES.md`. The raw files (hundreds of
    MB) are downloaded to the scratchpad, streamed, and never committed.
  - Other sources are filed per-employee costs (company registries, 10-K/20-F), UK and EU banks'
    remuneration disclosures and regulators' high-earner reports, each with its caveats stated.
  - Ranges only, never a single "typical salary". Never an individual's pay or private details.
- **The filings tutorial (ch. 11)** reads a committed snapshot of public filings (Companies House
  accounts, EDGAR 10-K/20-F extracts), with sources and licences. Tests are offline.
- **Firm names:** every line naming a firm has a ledger row whose claim covers it (the firm-name gate).
  Criticism comes only from court or regulatory records, stated neutrally with the outcome. Headcounts,
  offices and AUM go in dated boxes.
- **No rankings of firms by prestige** and no "best employer" lists. Where a league table is cited (banks,
  ch. 7), name its publisher and date.

**Book 18 (interviews):**
- **Original wording.** Classic puzzles are folklore, but never copy the text or solution of a
  published interview book or website. Where a puzzle has a known origin, cite it in `omsources`.
- **Never attribute a question to a firm**, not even "a firm like …".
- **Tests.** Every numeric answer is asserted by `code/interviews/NN-…/tests/test_solutions.py`, by exact
  computation, simulation over many seeds, or both. Coding answers are real files, tested in Python and
  compiled and tested in C++20/Rust where the question is in that language. The ch. 22 "what does this
  print" questions are compiled and their output asserted, with undefined behaviour stated, never
  "tested".
- **Few new terms.** Mathematics, markets, ML and systems vocabulary belongs to Books 1–16. Book 18 uses
  it with prose pointers ("One Quant Book 4, chapter 10") and defines only interview-process and method
  terms.
- **Ch. 7 (offers)** uses Book 16's compensation and restrictive-covenant terms (bonus pool, deferred
  compensation, clawback, non-compete clause, garden leave …) and Book 17's pay-structure terms. It gives
  no legal advice.

## Term ownership

- **Books 1–16 keep their terms.** Harvest before claiming anything (ownership rule 10 of the 14–16 file).
- Book 16 already owns the compensation-policy, restrictive-covenant, business-model and organisation
  terms: bonus pool, formulaic payout, discretionary bonus, deferred compensation, malus, clawback,
  vesting schedule, material risk taker, non-compete clause, garden leave, non-solicitation clause, front,
  middle and back office, pass-through fee, centre book, and the rest of `sources/desk/DEFINITIONS.md`.
- **Book 17** owns industry-landscape, employer-type, career-path, role and pay-*data* terms, for example a
  role title as a defined term, sign-on bonus and guarantee if Book 16 lacks them, LCA, prevailing wage,
  and a pay-data source's own vocabulary.
- **Book 18** owns interview-process and question-method terms: online assessment, superday or final
  round, case study, take-home, and the families of puzzles as named methods.
- Anything left is a tie, and it goes to the lower book number.
- **Watch these overlaps:**
  - B17 Part III (the roles) against B18 ch. 1 (what each interview tests). B17 defines the roles; B18
    uses them.
  - B17 ch. 13–15 (pay) and B18 ch. 7 (offers). Pay structure is B17's; reading and negotiating an offer
    is B18's; the contract clauses are B16's.
  - B17 ch. 28 (careers, non-competes in practice) against B16 ch. 11 (the law) and B18 ch. 7.
  - B17 ch. 29 (education pipelines, competitions) against B18 ch. 3 (applications, competitions).

## Lessons from the Books 14–16 batch (binding)

- **Check every figure on its own page in Phase C, and log the count.** One Book 14 pass found 22 defects in
  72 figures that no gate saw: diagrams wrong in their field, log axes not labelled, labels overlapping or
  clipped, legends over data, and `1,000` thousands separators (now fixed globally for ticks; hand-typed
  numbers must use `\,` or `\num{}`). Log "figures: N checked, K fixed (list)" in `PROGRESS.md`.
- **Scan the PDF** for comma thousands:
  `pdftotext -layout build/<entry>.pdf - | grep -nE '(^|\s{2,})[0-9]{1,3},[0-9]{3}(\s{2,}|$)'` must print
  nothing.
- **Chart-CSV labels:** no commas, `%` or `$`. `%` silently comments out the rest of a pgfplots row.
- **No measured timings in these two books** unless a chapter truly needs one. If one does, measure it last,
  on a quiet machine, and say so in the `.meta`.
- **A micro sign or any non-ASCII character in a listed code file is fatal.** Write `us`.
- **Print numbers from the test's rounding** (Python rounds 140.55 to 140.5).
- **Briefs age.** Rewrite a hook from the sources actually read, never from the brief.
- **Source access tricks that worked:**
  - EDGAR full-text search (`efts.sec.gov`) with a user agent;
  - Companies House filing PDFs, then `pdftotext`;
  - the Federal Register's `/documents/full_text/text/`;
  - legislation.gov.uk in place of EUR-Lex;
  - the Internet Archive for justice.gov.

  WebFetch cannot read PDFs directly: save the file and run `pdftotext -layout` on it.

## Resources, CI and the search budget

- **Resource limits,** as in the 14–16 file: at most ~1.5 GB RSS and one core per process, BLAS threads 1,
  `nice -n 19`, `systemd-run --user --scope -q -p MemoryHigh=2G -p MemoryMax=4G` for anything long. Book 17's
  LCA files are streamed and never loaded whole: read them in chunks, or convert once to Parquet under the
  scratchpad.
- **CI rules for new chapters,** as in the 14–16 file: a fast set under 20 s per chapter, and full-size tests
  `@pytest.mark.reference` from the start.
- **Web searches:** the session budget is 5,000 and is shared. Book 17 is the most source-heavy book of the
  series, so plan ~500 and fetch primary URLs directly wherever possible. Book 18 needs few (~50).

## Phase A report

Return the ten points of the 14–16 file's "Phase A report" section, with these adaptations:
- point 6 lists running-project components, if any. Book 17 may add a filings reader or pay-data tool;
  Book 18 probably none, since its code is answer checkers under `code/interviews/`;
- Book 18 adds its question count per chapter;
- Book 17 adds its data plan: the public datasets, their licences, their sizes and what is committed.

Then stop.

## Sync decisions

(Written by the main session after the two Phase A reports; binding for Phases B–D.)

1. **Definitions.** `sources/SERIES_DEFINITIONS.md`, "Rulings at the Books 17–18 sync", is binding. The map
   is now regenerated over Books 1–16 (3,383 terms).
   - *Return offer* is Book 17's (ch. 28), and Book 17 also defines *internship* there. Book 18 removes
     *return offer* from its `defines` and `DEFINITIONS.md` by hand (do not re-run make_briefs) and uses it.
   - Pay-structure terms (ch. 13), career-path terms and the role titles are Book 17's. Book 18 uses
     Book 17's **exact strings**: read `sources/industry/DEFINITIONS.md` and fix the `uses` owners (for
     example, there is no bare "trader" or "risk manager" term; the terms are *risk trader*, *compliance
     officer*, *control function* …).
   - Counteroffer, offer letter, exploding offer and the interview and application-process terms are
     Book 18's. Book 17 ch. 28–29 uses them with forward pointers.
   - Book 18's `DEFINITIONS.md` has combined rows ("exploding offer, offer letter"): make one term per row.
2. **Book 18 size (user: "not too many per chapter or book").** Cap every bank at 14 questions (ch. 29 keeps
   its six transcripts of three), aiming at **about 355 questions** in all, with Part II and IV banks at
   13–14. Target ~240–250 pp.
3. **Book 18 ch. 7 stays self-contained.** It may point to Book 17's `firm.payoffer` in prose, but its
   checks are its own `iv_` code: Book 17 lands `payoffer` at the same time, so do not wait for it.
4. **Components.** Book 17's 21 names are reserved in `code/firm/INTERFACES.md` §10 (all new). Book 18 has
   none; its answer checkers live under `code/interviews/`.
5. **Web access and the user's e-mail.** Do **not** put the user's e-mail address (or any personal contact)
   in a user agent or anywhere else, unless the main session later tells you the user has allowed it. For
   www.sec.gov, bls.gov and dol.gov, use the Internet Archive copies, which work, and
   `efts.sec.gov`/`data.sec.gov` with a plain research user agent. This holds until the user decides
   otherwise.
6. **Book 17 data.**
   - The plan is accepted: derived tables only, raw files streamed and deleted.
   - LCA cells with fewer than ten filings are suppressed; no named individual's pay is used anywhere
     (proxy named-executive tables and "highest-paid director" lines are dropped at extraction).
   - The ~2.85 GB of LCA downloads run once, late, one file at a time, under `nice` and the `systemd-run`
     caps. The disk has room (690 GB free).
   - For a component whose licence is still to verify (EBA reuse, HESA CC BY), verify it before committing
     derived numbers. If the licence cannot be verified, cite the figures in prose and ledger only.
7. **Already fixed by the main session:**
   - the ~20 prose comma thousands Book 17 found (a third thin-space pass);
   - the Book 16, `OUTLINE.md` and `WRITING_A_QUANT_BOOK.md` sentences that said Book 18 harvests questions;
   - `make_briefs.py` printing an empty "Defines";
   - the Book 18 gate reading `\iqroles`/`\iqfirm` only on the `\begin` line: it now reads the whole
     optional argument.
8. **Chapter numbering is frozen.** Checkpoints at ch. 10 and ch. 20 in `PROGRESS.md`, with pages and search
   counts. The Phase D report follows the 14–16 file's decision 9. It also gives **"figures: N checked, K fixed"**
   and the PDF comma scan result: `pdftotext -layout <pdf> - | grep -P '(?<![\d.,])\d{1,3}(,\d{3})+(?![\d,])'`
   must print nothing outside code listings.

## Reconciliation to-do (main session)

- **Book 18 landed and was verified by the main session (2026-09-29):**
  - 220 pp (outline ~240: capped banks, no padding), 357 questions (118/134/105);
  - `gates.sh book interviews` GREEN (3,469 definitions over 18 books);
  - `make test-code CH=interviews` GREEN: 30 directories including the originality gate (805 texts against 14,597
    in Books 1–17, 0 shared 8-word runs); C++20 ×4, Rust ×1, SQL on DuckDB and SQLite;
  - sampled solutions recomputed by hand (10.6 birthday bound, 10.8 two protocols).
- **Traps to merge:**
  - an unquoted `<<EOF` deletes `$…$` math;
  - ThreadSanitizer can SIGSEGV at start-up on this kernel (rerun under `setarch -R`);
  - writing from memory reproduces the series' own questions (two Book 2 near-duplicates caught);
  - ruff B905 (`zip(strict=)`).
- **Appended by Book 18:** a SQL listings style in `onequant.sty` and names in `tools/firm_names.txt`.

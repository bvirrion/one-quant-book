# Batch run: One Quant Books 14, 15, 16 (started 2026-09-28)

Three books are written in parallel in this one working tree, one agent per
book. User rule for Books 14–18 (2026-09-28): one subagent per book, **at most
three books at the same time**; batches {14, 15, 16} then {17, 18}. This file
is owned by the main session; book agents read it and never edit it.

| Book | Entry file | Slug | Label prefix | Teaching-module prefix | Chapters |
|---|---|---|---|---|---|
| 14 Networks, Hardware and Trading Infrastructure | `one_quant_book_14_networks.tex` | `networks` | `nw` | `nw_` | 29 |
| 15 Research, Data and Risk Platforms | `one_quant_book_15_platforms.tex` | `platforms` | `pl` | `pl_` | 30 |
| 16 The Desk and the Firm | `one_quant_book_16_desk.tex` | `desk` | `fm` | `fm_` | 30 |

Book 16's slug is **`desk`**, not `firm`: `code/firm/` is the running project,
and `code/<slug>/NN-…` must not land inside it.

Already done by the main session (Step 0):
- the three entry files, `latexmkrc`, `tools/termlink/books.py` (`--book 14..16`
  works), the `Makefile` gate list and `tools/gates.sh`'s slug map;
- part-title keys in `styles/lang/en.tex`;
- linker configs `tools/term_config/book{14,15,16}_en.py`, copied from Book 13's
  (curate yours in Phase C);
- the libraries and tools below.

Part keys (use in `tools/briefs/book<N>.py`, `PARTS`; write that file in the
shape of `tools/briefs/book13.py`, then `python3 tools/make_briefs.py --book N`):

- Book 14: `part.nw.network`, `part.nw.hardware`, `part.nw.venues`, `part.nw.cloudcrypto`, `part.nw.sectors`
- Book 15: `part.pl.data`, `part.pl.research`, `part.pl.services`, `part.pl.practice`
- Book 16: `part.fm.business`, `part.fm.desk`, `part.fm.control`, `part.fm.tech`, `part.fm.strategy`

## User rulings for this batch (2026-09-28)

1. **Book 15 ch. 4 is "A tick store on open formats"**, not "kdb+ and q" (see
   `outline/engineering-firm-interviews.md`). The ch. 4 system:
   - live capture to append-only binary or Arrow IPC files;
   - end-of-day compaction into Parquet partitioned by date and symbol and sorted by time;
   - the intraday/historical split;
   - as-of joins in DuckDB and Polars;
   - memory-mapped in-house flat formats;
   - schema evolution.

   Ch. 3 keeps the formats' internals: Arrow memory layout, Parquet row groups, encodings,
   statistics, predicate pushdown. kdb+ appears as one sourced remark in ch. 4 and a row in
   ch. 5's survey, and **no q is written anywhere**. The general rule: teach the open-source
   tools the industry actually runs, and treat proprietary products briefly, with a source.
2. **Book 14 ch. 6–7: SystemVerilog, tested in simulation.** Verilator
   (4.038 here; CI's ubuntu-24.04 has 5.x) and Icarus Verilog 11 are installed.
   - Write HDL that both versions accept.
   - Drive the Verilator build with `verilator --cc --exe --build`, not the 5.x-only
     `--binary`, from a pytest test in the chapter's `tests/` or the component's tests.
   - Such a test **fails** if the tool is missing; it never skips.
   - HDL files live under `code/networks/NN-…/hdl/` or `code/firm/<component>/hdl/`, and
     `\omcode` prints `.sv`/`.v`. Append a `listings` SystemVerilog style to
     `onequant.sty` only if needed (append-only rule).
   - A C++20 or Rust cycle model sits beside the HDL where the comparison teaches something.
3. **Libraries.** On top of Books 10–13's set (numpy, pandas, scipy, statsmodels,
   scikit-learn, LightGBM, PyTorch CPU), `.venv` now has **duckdb, polars, pyarrow and
   pybind11** (pinned in `requirements.txt`).
   - `python3-dev` is installed, so pybind11 extensions build with
     `g++ -std=c++20 -shared -fPIC $(python3-config --includes)`.
   - Rust stays free of external crates. A Python-to-Rust binding goes through a C ABI
     (`extern "C"`, `cdylib`) and `ctypes`/the buffer protocol; PyO3 is described with a
     cited source, not built.
   - Anything else needs the main session's approval, because it must go into
     `requirements.txt`.
   - No network access in tests; no GPU; no cloud account; no kdb+.
4. **Cloud and crypto connectivity (Book 14 Part IV) are not measured here.**
   - Numbers come from cited sources: provider documentation, venue docs, public talks,
     papers. They go through the ledger and dated boxes.
   - Simulations (the instance lottery, route racing) are labelled as simulations, with
     their parameters taken from cited figures.
   - Anything timed on this laptop follows Book 13's rule: the caption names the laptop
     (Intel Core Ultra 7 155H, WSL2, no isolated cores), and tests assert only
     machine-independent properties.
5. **Maps (Book 14 Part III).**
   - Site coordinates are ledger rows.
   - Distances (great-circle, WGS-84), fibre and radio light-times and route factors are
     computed by a script into `figdata/`, never typed.
   - Maps are TikZ over the computed coordinates.
   - Who is in which building goes in a dated box, and only with a public source.
6. **Case studies and incidents (Book 16 ch. 27–29, and anywhere else)** come only from
   court, regulator, official-inquiry or exchange records, and reputable press for
   context. They are stated neutrally, with the outcome. Examples: the 1998 hedge-fund
   collapse, the 2006 natural-gas fund, August 2007, the 2012 software incident, the 2021
   family-office default, the 2022 exchange failure, the 2022 nickel squeeze.

## Ownership rules (in force at all times)

1. **Write only your own files:**
   - anything under `parts/<slug>/`, `code/<slug>/`, `figdata/<slug>/`,
     `sources/<slug>/`, `images/<slug>/` and `data/<slug>/`;
   - your own `tools/briefs/book<N>.py` and `tools/term_config/book<N>_en.py`;
   - your entry file;
   - the `code/firm/<component>/` directories reserved for you at the sync (none before
     it). **Never edit an existing `code/firm/` component**: wrap or extend it in a new
     component of yours, and report defects.
2. **Never edit** files belonging to Books 1–13 or to another batch book. Put
   the defects you find there in your report, with file:line and the fix.
   Books 1–13 are committed, but this batch's work (and the shared Step 0
   edits) is not: its only copy is this working tree.
3. **Shared files are append-only**, and only when unavoidable:
   `styles/onequant.sty` (a new package, macro or `listings` language) and
   `tools/firm_names.txt`. Append at the end under a `% Book <N>:` (or
   `# Book <N>:`) comment. Never change or reorder existing lines. Re-read the
   file just before editing, because others append too. Keep appended macros
   few and prefixed or clearly scoped, and build your book right after.
4. **Do not edit** `tools/gates.sh`, `tools/termlink/`, `tools/test_code.sh`,
   `tools/figdata.sh`, the other `tools/*.py`, `Makefile`, `latexmkrc`,
   `CONTRIBUTING.md`, `OUTLINE.md`, `outline/*.md`, `WRITING_A_QUANT_BOOK.md`,
   `code/firm/INTERFACES.md`, `requirements.txt`, `.github/`, any `CLAUDE.md`,
   or this file. If a tool is buggy or a doc must change, report it (and work
   around it locally if you can). New traps and calibration go in your
   `sources/<slug>/PROGRESS.md`; the main session merges them into the shared
   docs.
5. **Git is read-only:** `git status`, `git diff` and `git log` only. Never
   run `checkout`, `stash`, `reset`, `clean`, `restore`, `add` or `commit`. A
   repo-wide checkout destroyed a whole batch of shared work once in a sister
   series.
6. **Build only your own entry file:** `latexmk <your entry file>`. Never run
   a bare `latexmk` or `make`/`make all`/`make gates`, which build or check the
   other books mid-write. Never run two `latexmk` on your entry at once and
   never wrap it in a short timeout (a killed run corrupts `.aux`/`.toc`;
   recover by deleting your entry's `.aux .toc .out .fdb_latexmk` in `build/`).
7. **Scope tests to your slug:**
   - `make test-code CH=<slug>/NN-…` per chapter, and `make test-code
     CH=<slug>` at the end; `ruff check code/firm/<component>` after every
     edit to one of your firm components (and `make test-code CH=firm/<component>`
     if that form works for it);
   - `tools/figdata.sh <slug>`;
   - `tools/gates.sh chapter|sources|firms <slug>/NN-…`;
   - `tools/gates.sh book <slug>`; `tools/gates.sh log <slug>`.

   A global check can go red because of another book's work in progress (ruff
   over `code/`, `check_module_names`, `check_figdata`, the series-wide "terms
   defined twice"). Read the failing path: if it is not yours, note it and
   carry on.
8. **Teaching modules** (Python files under `code/<slug>/`) start with your
   module prefix (`nw_`, `pl_`, `fm_`). Running-project modules are
   `firm_<component>.py`. C++, Rust and HDL files follow the same prefix rule
   where they are importable or linked by name. Module names are unique
   repo-wide (`check_module_names.py`): prefix even helper scripts.
9. **Cross-book references are prose only:** "One Quant Book 13, chapter 18",
   never a `\cref` into another book. Chapter numbers are the outline's,
   frozen at the sync.
10. **A term is defined once in the series.** Before each chapter's
    definitions, search the multi-line harvest over every written book:
    `perl -0777 -ne 'while(/\\emph\{([^}]*)\}\s*\\index\{([^}]*)\}/g){($t=$2)=~s/\s+/ /g; print "$t\n"}' parts/*/[0-9]*.tex`
    and check `sources/SERIES_DEFINITIONS.md` (the batch's rows are added at
    the sync). If another book owns the term, use it with a prose pointer and
    no `\emph{…}\index{…}` pair, in the owner's wording.
11. **Figure crops** go to your own subdirectory of the session scratchpad
    (`/tmp/claude-1000/-home-bvirrion-repositories-one-course/ae14faac-4918-4550-a552-734d3b2515f8/scratchpad/<slug>/`);
    check the running header of every crop, because another book's build may be
    rewriting a PDF.

## Resource limits (user rule, binding from the first command)

The machine is the user's laptop (22 logical cores, 19 GB RAM, WSL2), shared with
their own work and with the two other agents.
- Every process stays under about 1.5 GB RSS and one core. Set BLAS, torch and
  LightGBM threads to 1. No multiprocessing pools, no `make -j`, and one heavy job per
  agent at a time.
- Run long jobs under `nice -n 19` **and** a cgroup cap:
  `systemd-run --user --scope -q -p MemoryHigh=2G -p MemoryMax=4G <cmd>`.
- Run `latexmk` only when a chapter is ready.
- Stream large generated data (capture files, tick stores) to disk in chunks, test it
  small, and generate it full-size once, late. Keep committed data small: a tick-store
  tutorial uses a generated day of a few tens of MB at most, and the bytes are
  regenerated by a script, not committed.
- Check `free -g` before anything heavy. Leave alone any process that is not yours; the
  user runs research jobs of their own.

## CI rules for new chapters (user rulings 2026-09-26/27)

- Every chapter directory has a fast set that runs in well under 20 s. Any full-size test
  that reproduces the book's printed digits (whole simulated days, big Monte Carlo runs,
  training runs, large tick stores) is `@pytest.mark.reference` **from the start**.
- Each chapter keeps an unmarked `test_small_runs` (or other unmarked test) that calls
  the same functions at reduced size through their size parameters and asserts
  properties, never printed digits.
- A heavy result computed at import time runs even when every test is deselected. Make it
  a cached function called inside the tests.
- Digits that move with the processor's floating-point kernels are `reference` too;
  by-hand arithmetic tests stay unmarked.
- Assume CI's g++ is 13 while the local one is 11.4. Stay `-Werror`-clean on both, without
  version-specific tricks.

## Sources and the web-search budget

The session's web-search budget (5,000) is shared by the three agents and the main session.
- Guide: **about 400 searches per book**. Prefer fetching known primary URLs directly.
- Use the no-search fallbacks in `WRITING_A_QUANT_BOOK.md` §9: Crossref and arXiv APIs,
  Wikipedia `?action=raw` as a map to primary references, CourtListener, EDGAR with a
  user agent, eCFR, FRED CSVs, `pdftotext` on saved PDFs, GitHub raw docs.
- If searches start failing, say so in `PROGRESS.md` and continue with the fallbacks;
  never fill a ledger row from memory.
- Book 14 (venue locations, vendors, products) and Book 16 (case studies, regulation) are
  source-heavy. Book 15 is mostly bibliographic and documentation-based.

## Term ownership rule, and the overlaps to watch

- A term already defined in **Books 1–13 stays there.** Examples to check before
  claiming anything:
  - Book 13: kernel bypass (if defined), busy polling, core isolation, huge pages, FIX and
    session terms, SBE, line arbitration, multicast, feed handler, risk gate, sequencer,
    binary logging, replay.
  - Book 10: order-entry protocol, redundant feed lines, snapshot recovery, drop copy,
    exchange simulator.
  - Book 3: the crypto-venue API vocabulary (rate limit, request weight, API key,
    snapshot-and-delta feed, cloud region, dedicated endpoint).
  - Book 1: colocation (if defined), direct feed, sponsored access, market-data terms.
  - Book 7: backtest fidelity levels, replay parity test, canary deployment, staged
    rollout, paper trading, point-in-time data, security master.
  - Book 6: risk limit, risk hierarchy, VaR/ES, XVA terms.
  - Book 11: kill switch, pre-trade risk check, market access rule.
  - Book 9 ch. 29: surveillance and manipulation terms.
- Otherwise: **Book 14** owns network, hardware, timing, physical-access, colocation-product,
  long-haul, cloud-networking and connectivity-contract terms; **Book 15** owns data-system,
  storage-format, platform, pricing-library-architecture, post-trade-systems and
  software-engineering-practice terms; **Book 16** owns business-model, organisation,
  control-function, funding/treasury, legal-documentation, compensation-policy and
  firm-strategy terms.
- Anything left is a tie, and it goes to the lower book number.

Within the batch:
- **Buying connectivity and vendors:** B14 ch. 15 and 27 (what is bought, from whom) against
  B16 ch. 20, 22, 23 (build against buy, data budget, negotiating). B14 owns connectivity
  products and contract terms such as SLA and cross-connect; B16 owns the decision and
  negotiation terms.
- **Resilience and incidents:**
  - B14 ch. 28 (DR sites, exchange failover tests, resilience rules): the physical and
    regulatory side;
  - B15 ch. 28 (observability, incident response, blameless review): the engineering
    process;
  - B16 ch. 27 (crisis management): the firm's decisions;
  - B16 ch. 17 (regulators and licences): the regimes.
- **Backtesting:** B15 ch. 11–12 extend Book 7's backtester (levels 1–3: `firm.vecbt`,
  `firm.evbt`, `firm.lobreplay` …) and Book 7's replay-parity vocabulary. Level 4 runs on
  Book 10's `firm.exchsim` (`code/firm/INTERFACES.md` §7).
- **Positions, P&L, risk:**
  - B15 ch. 17–20 (services, real-time risk, pricing-library architecture, risk grid) sit
    on Book 5's `firm.pricing`, Book 6's `firm.riskengine`, Book 13's `firm.riskgate` and
    the existing `firm.pnl`/`firm.pnlexplain`;
  - B16 ch. 7 and 12 own the limit *framework* and the risk *function*;
  - B15 owns the systems.
- **Operations and post-trade:** B15 ch. 21–22 (trade capture, confirmation, settlement
  instructions, reconciliation systems) against B16 ch. 13 (operations as a function).
  Existing `firm.ledger` and `firm.corpactions` are there to build on (`firm.recon` is Book 1's index-*reconstitution* predictor, not reconciliation).
- **Data:** B15 ch. 6 and 23 (reference data, entitlements) against B16 ch. 22 (data
  strategy and costs) and Book 1's data-licence vocabulary.
- **Surveillance:** B15 ch. 30 (the technology) against Book 9 ch. 29 (manipulation and
  detectors) and B16 ch. 16 (compliance as a function). Existing `firm.surveil` is there
  to build on.
- **Security and IP:** B15 ch. 29 (technical security) against B16 ch. 11 (trade secrets,
  non-competes).
- **Hardware in the program:** B14 ch. 3 (network cards, kernel bypass from the network
  side) against Book 13 ch. 13 (Linux tuning, busy polling). B14 ch. 8 (servers) against
  Book 13 ch. 2–4 (microarchitecture, memory, NUMA).
- **Crypto APIs:** B14 ch. 20 (API engineering for crypto venues) against Book 13 ch. 17
  (WebSocket/REST/TLS/JSON client stack) and Book 3's API vocabulary.

## Running project

Books 14–16 add components to `code/firm/`. They are reserved at the sync in
`code/firm/INTERFACES.md` §9, and names must not collide with the ~380 existing
directories (`ls code/firm`). The expected big pieces:
- **Book 14:**
  - the network and timing models the tutorials need;
  - the HDL designs (feed decoder, book top, risk check), each with a C++ or Python
    golden model;
  - the ch. 29 **connectivity plan** (latency table, bill of materials, budget as data,
    with a report).

  Where it helps, Book 14 extends Book 13's tick-to-trade path (`firm.ticktotrade`) with
  a wire and switch model.
- **Book 15:**
  - the open-format tick store (ch. 2–4);
  - a native-extension example (ch. 9);
  - the backtest-engine architecture, with **level 4 on `firm.exchsim`** (ch. 11);
  - simulation–production parity (ch. 12);
  - the **position and P&L service** from fills and drop copies (ch. 17);
  - real-time risk aggregation (ch. 18);
  - a risk-grid fan-out on the existing pricing and risk engines (ch. 20);
  - trade capture and post-trade reconciliation (ch. 21–22).
- **Book 16:** Python firm-level models: the economics of a trading firm (P&L and cost
  model), limit allocation, drawdown rules, bonus pools, fund-launch economics and an
  entry-plan tool.

  Where the outline's anatomy asks for a "Build", Book 16's builds are these models. A
  chapter whose subject has no honest build (for example, legal documentation) says so in
  its Phase A brief and proposes a small analytical tool instead.

## Phase A report (what each agent returns before writing any chapter)

1. Paths written: `tools/briefs/book<N>.py`, `sources/<slug>/DEFINITIONS.md`,
   `sources/<slug>/PROGRESS.md`, and the skeleton. The skeleton must build
   0/0/0 with `latexmk <entry>` and `tools/gates.sh log <slug>`.
2. **Uses from other books.** For every term you use but do not define, the
   owning book and chapter: Books 1–13 (checked against the harvest) or a
   batch book (by the outline).
3. **Contested terms.** The terms you plan to define that another batch book
   might also define, and why you should own each one.
4. Any **term already in Books 1–13** that you had planned to define: remove
   it from your map before reporting and list it here.
5. The **notation** you need beyond `CONTRIBUTING.md`'s series notation.
6. **Running-project components**: `code/firm/<name>` names, one line each,
   with language(s) and the existing components they build on. Check that none
   of them exist in `code/firm/`.
7. **What you need from other books' code** (exchsim, pricing, riskengine,
   ticktotrade, pnl, recon, …), by chapter, and anything in them that blocks you.
8. **Chapter changes** you propose (split, merge, reorder), with the reason.
   Default: none. The outline's numbering is what other books point to.
9. **Source plan**: the chapters that are most source-heavy, and your
   search-budget estimate.
10. **Defects found in Books 1–13 or in the tooling.**

Then stop. The main session merges the three reports, extends
`sources/SERIES_DEFINITIONS.md`, the notation table and
`code/firm/INTERFACES.md`, and resumes each agent with its specific changes.

## Carry-over traps (read WRITING_A_QUANT_BOOK.md §9 in full; these bite most)

- A model's memory is not a source. Search for the most recent release of any rule,
  product or price a chapter leans on (fees, colocation products, cloud instance types
  and regions change often). Volatile facts go in `dated` boxes.
- Named firms (vendors, venues, data-centre operators, network providers, trading firms)
  need a ledger row per attribution; the firm-name gate checks it. Criticism comes only
  from court or regulatory records.
- Planted effects are too strong at first, every time; a single seed is not a test; a
  simulation a caption leans on gets a time-step-divided-by-four stability test and an
  ablation of every mechanism the text credits.
- Listing ranges drift: run `omcode_ends.py` after every code edit and every `ruff --fix`.
  Listings are at most 40 lines, ASCII only in listed files, and listed lines under
  ~104 characters.
- Captions are written from the rendered figure; legends go below the axis; write tick
  lists out (no `...`); brace commas in `\legend` entries; no commas in chart-CSV labels.
- Print numbers from the test's rounding. A product of rounded factors must equal the
  printed factors' product. Put the unit in the test's variable name, and convert clock
  times to UTC.

## Sync decisions

(Written by the main session after the three Phase A reports; binding for Phases B–D.)

1. **Definitions.** `sources/SERIES_DEFINITIONS.md`, "Rulings at the Books 14–16 sync", is binding.
   The three planned maps (181 + 248 + 201 terms) had one exact collision and a few synonym pairs:
   - *vendor lock-in* goes to **B16 ch. 20**; B14 ch. 27 uses it.
   - *data-transfer charge* is **B14 ch. 16**; B15 drops *egress charge* and uses B14's term.
   - *public cloud* is **B14 ch. 16**; *network segmentation* is **B15 ch. 29**.
   - *latency tier* is **B16 ch. 19**; B14 ch. 9 describes port and connectivity options without the term.
   - *time to restore* (B15) and *mean time to repair* (B14) are both kept; B15 ch. 28 says how they differ.
   - Everything else each agent claimed in its Phase A report is **granted as claimed**: B14's resilience,
     SLA and colocation terms; B15's post-trade, engineering-practice, entitlement and cloud-economics terms;
     B16's organisation, compensation, legal and strategy terms, including front/middle/back office and the
     four-eyes principle.
   - The loser of a ruling removes the `\emph{…}\index{…}` pair from its brief's `defines` and from its
     `DEFINITIONS.md` **by hand**. Do not re-run `make_briefs.py`: it regenerates `part.tex`/`DEFINITIONS.md`
     and drops hand-written sections. The loser then uses the term in the owner's wording, with a prose
     pointer (a forward pointer if the owner is a later book).
   - Before each chapter, still grep the harvest over every written book: the other two batch books are
     writing at the same time.
2. **Notation.** `CONTRIBUTING.md`, "Books 14–16 additions", holds every symbol the three reports asked for.
3. **Style file.** The main session has already appended to `onequant.sty`:
   - a `SystemVerilog` listings language, so `.sv` and `.v` files print with it through `\omcode`;
   - the units `\flop` and `\msg`.

   Do not add these again. Other appends follow ownership rule 3. `tools/firm_names.txt` appends (Book 16's
   case-study names, Book 14's vendors) are expected, under `# Book <N>:`.
4. **Components.** `code/firm/INTERFACES.md` §9 reserves the 89 names from the reports, all unique and new.
   - Wrap existing components; never edit them.
   - **Level 4 (B15 ch. 11):** B15's proposal is adopted. The reactive simulation on `exchsim` is presented
     as Book 7's fidelity level 4, with the simulator standing in for the venue. Only *reactive simulation*
     is defined; *fidelity level* stays Book 7's.
   - `firm.recon` is **not** reconciliation. B15's `posttrade` builds position and cash reconciliation.
   - **B16 `techtier` ↔ B14 `connplan`:** B16 takes tier costs as cited inputs until `connplan` lands, and
     the main session wires the two together at reconciliation.
5. **Tooling fixed by the main session:**
   - `tools/make_briefs.py` now writes the brief's `data` field (the hand-added Data lines stay);
   - the two entry-file comments are fixed;
   - CI (matrix slugs, the apt verilator/iverilog/python3-dev packages, release PDFs) is updated at
     reconciliation, not now.

   Defects reported in earlier books are logged for reconciliation, not fixed by the agents:
   - emphasis different from the index term in Books 7, 10 and 13;
   - interview role `dev` in Book 12 and `compliance` in Book 13.
6. **Chapter numbering is frozen** as in the outline; none of the three books proposed a change. Hooks that
   would repeat an earlier book's are changed, as B16 already did. Hooks with a placeholder or unsourced
   number are replaced by a ledger row or the chapter's own simulation before the chapter passes its gates.
   Example: B14 ch. 9's equal-length cross-connects, which is otherwise rewritten around RTS 10's fairness
   rule.
7. **Search budget.** The estimates are B14 ~380, B15 ~150–250 and B16 ~450, all accepted. Log a running
   count in `PROGRESS.md` at each checkpoint.
8. **Checkpoints.** At ch. 10 and ch. 20, write a page projection in `PROGRESS.md`. A projection more than
   15 % under the outline means chapters are being compressed: restore depth (~450–550 body lines, four
   figures where the subject has them) before going on.
9. **Phase D report** (end of your book). It gives:
   - pages against the outline, and the chapter count;
   - counts of figures, listings, tables, dated boxes, ledger rows, term links and tests (chapter and
     firm, plus C++/Rust/HDL builds);
   - gate results: `tools/gates.sh book <slug>`, `make test-code CH=<slug>`, and `tools/figdata.sh <slug>`
     with no diff;
   - EXCLUDED facts; defects found in other books or the tooling; new traps and calibration for the
     shared docs.
10. **Resource limits** are as in the section above, from the first command. The main session runs no
    full-repo test suite while you write.

## Reconciliation to-do (main session; collected as books land)

- **Book 16 landed and was verified by the main session (2026-09-28):**
  - 347 pp; `gates.sh book desk` GREEN;
  - `make test-code CH=desk` GREEN (30 chapter dirs), 94 firm tests pass, ruff clean;
  - `figdata.sh desk`: 87 CSVs with identical checksums.
- `techtier` reads Book 14's `firm.colobill` rather than `connplan`: check the wiring once Book 14 lands.
- `check_figdata.py` misses `%` and `$` inside chart-CSV labels (`%` comments out the rest of the row). The
  chapter gate does not enforce the 40-line listing limit. The drafty gate flags pgfplots `{1,...,7}`.
- **Book 3 ch. 8 ledger (LME nickel):**
  - F2 and F3 were cited from search excerpts. Primary texts: [2024] EWCA Civ 1168 on the LME site; FCA final
    notice `fca.org.uk/publication/final-notices/london-metal-exchange-2025.pdf`.
  - F1 mixes $2.6bn / $7.05bn margin-call figures with the FCA's $3.5bn / $5.1bn, which are different measures.
- Emphasis/index mismatches:
  - `low-latency/24:115` *idempotently*; `low-latency/09:75` *sound*;
  - `research/03:31` *bitemporal*; `research/28:15` *capacity*;
  - `microstructure/07:76` *neutral*; `microstructure/08:89` *locked*/*crossed*.
- Interview roles: `dev` in `parts/ml/13,14,15,23-29` (should be `developer`); `compliance` at
  `parts/low-latency/23:350`.
- CI: matrix slugs `networks platforms desk`; apt `verilator iverilog python3-dev`; release PDFs for 14–16.
- New traps from each book's `PROGRESS.md` go into `WRITING_A_QUANT_BOOK.md` §8–9; tables go into `CLAUDE.md`,
  `OUTLINE.md` and the root `CLAUDE.md`.
- **Book 14 landed (2026-09-28/29):**
  - 349 pp; `gates.sh book networks` GREEN; 29 chapter test dirs pass;
  - all 30 components pass: 102 tests, C++20 twins, the nicring Rust crate, and Verilator/Icarus builds in
    hdlkit and hwtrade;
  - per-figure check of ch. 1–20 sent back to the agent (they were only sampled); figdata to verify after.
  - Wire `techtier` (reads `colobill`) against `connplan/data/cost_table.csv`.
  - Ch. 26's term was renamed *transaction charge*.
  - Unsourced assumptions left flagged in `connplan`: the Mahwah–Aurora wavelength price and the Tokyo endpoint
    price.
  - Traps to merge: a micro sign in a listed file is fatal; `meta expr` fixed-point output; round from the tests.
- **Book 14 figure pass done:** 72 figures in ch. 1–20 checked, 22 fixed (2 content errors, 1 text error, log
  axes, overlaps, comma thousands).
- **Comma thousands, series-wide.**
  - Ticks: fixed globally by `\pgfplotsset{/pgf/number format/1000 sep={\,}}` in `onequant.sty` (main
    session, 2026-09-29). Rebuild every book and re-gate.
  - Hand-typed table numbers with commas remain in many books, e.g. Book 11 tables `15,783`. Fix them inside
    `tabular` bodies only, by a reviewed script, then rebuild. Detector:
    `pdftotext -layout <pdf> - | grep -cE '(^|\s{2,})[0-9]{1,3},[0-9]{3}(\s{2,}|$)'`.
- `tools/figcrop.py` hard-codes 110 dpi against the 130-dpi rule: add a `--dpi` option (default 130) and print
  the running header.
- Trap to merge: pgfplots' default thousands separator is a comma.
- **Book 3 ch. 8 (LME nickel), resolved 2026-09-29:** the book's $2.6bn and $7.05bn are correct. They are
  the intra-day and 7 March margin-call totals in [2024] EWCA Civ 1168 §46 and §48, while the FCA's $3.5bn
  and $5.1bn are total margin calls. F1's evidence now quotes §46 and §48, and F2 cites the judgment (the
  Divisional Court is [2023] EWHC 2969 (Admin)) instead of a search excerpt.
- **Book 15 landed and was verified (2026-09-28/29):**
  - 367 pp; `gates.sh book platforms` GREEN; `make test-code CH=platforms` GREEN (30 directories, 103
    ranges); 165 firm tests pass;
  - 17 measured CSVs were re-measured on the quiet machine; 110 figures were checked and 28 fixed.
  - `firm.natext` now takes Python headers from `sysconfig` (not `python3-config`, which may be another
    Python on CI).
- **Tools (2026-09-29):**
  - `check_figdata.py` flags `%` and unpaired `$` in chart CSVs;
  - `omcode_ends.py` reports out-of-range listings instead of crashing;
  - `figcrop.py` crops at 130 dpi (`OQB_DPI`) and prints the running header.
- **Thin spaces:** 1,853 hand-typed comma thousands (and math-mode `{,}`) were replaced by `\,` in 9 books by a
  script that skips TikZ and pgfplots lines. All 16 books are being rebuilt.
- **Role tags normalised:** `dev` becomes developer (B12), `quant` researcher (B14), `compliance` risk
  (B13, B16).
- **CI:** matrix `networks platforms desk`; apt `verilator iverilog python3-dev`; release notes cover Books 1–16.
- **Thin spaces, done (2026-09-29).** Three script passes plus 4 hand edits:
  1. 1,853 replacements. A bug left every other `{,}` in chains of math `{,}`, e.g. `1{,}148{,}049{,}585`.
  2. 96 replacements, with a lookbehind for `{,}`, `\euro`/`\pounds` prefixes, and a narrower TikZ skip list:
     "tick" had skipped all of Book 11's prose.
  3. 36 math `{,}` inside TikZ labels, then 17 numbers in prose parentheses or after `\textyen`.

  All 16 books rebuild at 0/0/0. The broad PDF scan (`(?<![\d.,])\d{1,3}(,\d{3})+(?![\d,])`) finds only two
  comments inside printed code listings (Book 3 ch. 7, Book 12 ch. 28), left as code.

# Batch run: One Quant Books 3, 4, 5, 6 (started 2026-09-24)

Four books are written in parallel in this one working tree, one agent per
book. This file is owned by the main session; book agents read it and never
edit it.

| Book | Entry file | Slug | Label prefix | Teaching-module prefix | Chapters |
|---|---|---|---|---|---|
| 3 Markets III: Commodities, Energy and Crypto | `one_quant_book_03_markets_3.tex` | `markets-3` | `m3` | `m3_` | 29 |
| 4 Quantitative Methods | `one_quant_book_04_methods.tex` | `methods` | `qm` | `qm_` | 29 |
| 5 Derivatives and Volatility | `one_quant_book_05_derivatives.tex` | `derivatives` | `dv` | `dv_` | 28 |
| 6 Rates, Credit, XVA and Risk | `one_quant_book_06_rates_credit_risk.tex` | `rates-credit-risk` | `rc` | `rc_` | 29 |

Already done by the main session (Step 0): the four entry files,
`latexmkrc`, `tools/termlink/books.py` (`--book 3..6` works), part-title keys
in `styles/lang/en.tex`, linker configs `tools/term_config/book{3,4,5,6}_en.py`
(copies of Book 2's; curate yours in Phase C).

Part keys (use in `tools/briefs/book<N>.py`, `PARTS`):

- Book 3: `part.m3.commodities`, `part.m3.crypto`, `part.m3.other`
- Book 4: `part.qm.stochastic`, `part.qm.statistics`, `part.qm.timeseries`, `part.qm.highdim`, `part.qm.numerics`
- Book 5: `part.dv.foundations`, `part.dv.surface`, `part.dv.exotics`, `part.dv.numerical`, `part.dv.desk`
- Book 6: `part.rc.rates`, `part.rc.credit`, `part.rc.xva`, `part.rc.risk`

## Ownership rules (in force at all times)

1. **Write only your own files:**
   - anything under `parts/<slug>/`, `code/<slug>/`, `figdata/<slug>/`,
     `sources/<slug>/`, `images/<slug>/` and `data/<slug>/`;
   - your own `tools/briefs/book<N>.py` and `tools/term_config/book<N>_en.py`;
   - your entry file;
   - the `code/firm/<component>/` directories reserved for you at the sync
     (none before it).
2. **Never edit** files belonging to Books 1–2 or to another batch book. Put
   the defects you find there in your report, with file:line and the fix.
3. **Shared files are append-only**, and only when unavoidable. These are
   `styles/onequant.sty` (a new package or macro) and `tools/firm_names.txt`.
   Append at the end under a `% Book <N>:` (or `# Book <N>:`) comment. Never
   change or reorder existing lines; another book depends on them. Re-read the
   file just before editing, because others append too.
4. **Do not edit** `tools/gates.sh`, `tools/termlink/`, `tools/test_code.sh`,
   the other `tools/*.py`, `Makefile`, `latexmkrc`, `CONTRIBUTING.md`,
   `OUTLINE.md`, `outline/*.md`, `WRITING_A_QUANT_BOOK.md`, any `CLAUDE.md`, or
   this file. If a tool is buggy or a doc must change, report it (and work
   around it locally if you can). New traps and calibration go in your
   `sources/<slug>/PROGRESS.md`; the main session merges them into the shared
   docs.
5. **Git is read-only:** `git status`, `git diff` and `git log` only. Never
   run `checkout`, `stash`, `reset`, `clean`, `restore`, `add` or `commit`.
   Everything in this tree is uncommitted. A repo-wide checkout destroyed a
   whole batch of shared work once in a sister series.
6. **Build only your own entry file:** `latexmk <your entry file>`. Never run
   a bare `latexmk` or `make`/`make all`, which would build the other books
   mid-write.
7. **Scope tests to your slug:**
   - `make test-code CH=<slug>/NN-…` per chapter, and `make test-code
     CH=<slug>` at the end;
   - `tools/figdata.sh <slug>`;
   - `tools/gates.sh chapter|sources|firms <slug>/NN-…`;
   - `tools/gates.sh book <slug>`;
   - `tools/gates.sh log <slug>`.

   A global check can go red because of another book's work in progress. The
   global checks are ruff over `code/`, `check_module_names`, `check_figdata`,
   and the series-wide "terms defined twice". Read the failing path: if it is
   not yours, note it in your report and carry on.
8. **Teaching modules** (Python files under `code/<slug>/`) start with your
   module prefix (`m3_`, `qm_`, `dv_`, `rc_`). Running-project modules are
   `firm_<component>.py`, as before.
9. **Cross-book references are prose only:** "One Quant Book 4, chapter 3",
   never a `\cref` into another book. Chapter numbers of the batch books are
   the outline's numbers, frozen at the sync.
10. **A term is defined once in the series.** Before each chapter's
    definitions, search `\index{<term>}` over `parts/*/` (multi-line aware:
    `perl -0777 -ne 'while(/\\emph\{([^}]*)\}\s*\\index\{([^}]*)\}/g){($t=$2)=~s/\s+/ /g; print "$t\n"}' parts/*/[0-9]*.tex`
    -- a line-based grep misses pairs split over two lines) and check
    `sources/SERIES_DEFINITIONS.md` (written at the sync). If another book
    owns the term, use it with a prose pointer and no `\emph{…}\index{…}`
    pair.

## Known overlaps between the four books (resolve in Phase A, confirmed at the sync)

Ownership rule:
- A term already defined in Books 1–2 stays there. Examples: *Bachelier
  model*, *barrier option*, *base correlation*, *implied volatility*,
  *volatility skew*, *put–call parity*, *swaption* if defined, *hazard rate*,
  *CDS* terms.
- Otherwise the **Markets books** own what a market or product *is*.
- **Book 4** owns mathematics, statistics, time series, optimisation and
  numerics.
- **Book 5** owns option pricing and volatility modelling.
- **Book 6** owns rates and credit *models*, XVA, and risk measures and
  processes.
- Anything left is a tie, and it goes to the lower book number.

The overlaps to watch:
- **Notation.** Book 4 ch. 1 fixes the series notation. Books 5 and 6 are
  written at the same time, so the main session writes the full table into
  `CONTRIBUTING.md` at the sync, and Book 4 ch. 1 prints it. Propose what you
  need in your Phase A report.
- **Book 4 Part I** (Brownian motion, Itô, SDEs, Girsanov, numeraires, jumps,
  Lévy) is used by Book 5 Part I–II and Book 6 Part I. Book 4 defines these
  terms; Books 5 and 6 use them.
- **Book 4 Part V** (Monte Carlo, finite differences, Fourier, AAD) against
  **Book 5 Part IV** (pricers in practice). Book 4 defines the methods; Book 5
  defines the pricing-specific terms (for example *regression-based early
  exercise* as applied, *pathwise Greek* if Book 4 does not).
- **Book 5 ch. 11 SABR** against **Book 6 ch. 5 SABR in rates**. Book 5
  defines SABR; Book 6 defines shifted SABR and the swaption matrix (the *volatility cube* itself is Book 2 ch. 13).
- **Book 5 ch. 20 FX derivatives** against **Book 2 ch. 19 FX options** (Book
  2 already defines *barrier option*, risk reversal, butterfly and similar
  terms; check).
- **Book 5 ch. 21 convertibles / equity-to-credit** against **Book 6 ch. 14
  structural credit**.
- **Book 3 ch. 10 convenience yield, storage** and **ch. 12 swing contracts,
  average-price options** against **Book 6 ch. 16 commodity derivatives**.
  Book 3 defines the products; Book 6 defines the models.
- **Book 3 ch. 5 day-ahead auction clearing** against **Book 4 ch. 29
  auctions**. Book 4 defines auction theory (formats, revenue equivalence);
  Book 3 defines the power-market auction terms.
- **Book 3 ch. 20 automated market makers** (Book 11 later covers market
  making; no conflict now).
- **Book 6 ch. 29 risk engine** runs on **Book 5 ch. 28 pricing library**.
  The interface is fixed at the sync in `code/firm/INTERFACES.md`. Book 6
  writes ch. 29 last; if Book 5's library is not there yet, Book 6 uses a stub
  adapter that conforms to the interface, and the main session wires the two
  together afterwards.
- **Book 6 ch. 21–28** (VaR, stress, capital, liquidity, margin models, model
  risk, P&L explain, operational risk) against Book 1/2 margin and clearing
  chapters. Books 1–2 define *initial margin*, *variation margin*, *central
  counterparty* and similar terms.

## Phase A report (what each agent returns before writing any chapter)

1. Paths written: `tools/briefs/book<N>.py`,
   `sources/<slug>/DEFINITIONS.md`, and the skeleton. The skeleton must build
   0/0/0 with `latexmk <entry>` and `tools/gates.sh log <slug>`.
2. **Uses from other books.** For every term you use but do not define, give
   the owning book and chapter: Books 1–2 (checked against their `\index{}`
   harvest) or a batch book (by the outline).
3. **Contested terms.** List the terms you plan to define that another batch
   book might also define, and say why you should own each one.
4. Any **term already in Books 1–2** that you had planned to define. Remove it
   from your map before reporting and list it here.
5. The **notation** you need beyond `CONTRIBUTING.md`'s interim tables.
6. **Running-project components**: `code/firm/<name>` names, one line each,
   with language(s). Check that none of them exist in `code/firm/`.
7. **Chapter changes** you propose (split, merge, reorder), with the reason.
   Default: none. The outline's numbering is what other books point to.
8. **Defects found in Books 1–2 or in the tooling.**

Then stop. The main session merges the four reports and writes
`sources/SERIES_DEFINITIONS.md`, the notation table and
`code/firm/INTERFACES.md`. It then resumes each agent with its specific
changes.

## Sync decisions (2026-09-24): binding for Phases B–D

1. **Definitions.** `sources/SERIES_DEFINITIONS.md` is the series map, with
   1,790 terms and its rulings at the top. The four collisions went to Book 4:
   - *equivalent martingale measure* and *risk-neutral measure*: B4 ch. 5.
   - *calibration*: B4 ch. 24.
   - *copula*: B4 ch. 15. Book 6 keeps *Gaussian copula* and *Student-t
     copula*.

   Each losing book removes the term from its brief `defines` (and its
   `DEFINITIONS.md`) and uses it with a prose pointer. A term you discover you
   need mid-book: check this map first. If it is unowned, define it and note
   it in your `PROGRESS.md`. If another batch book owns it, use it.
2. **Notation.** `CONTRIBUTING.md`, section "Series notation (fixed in One
   Quant Book 4, chapter 1)". Changes from the proposals:
   - Hawkes intensity is $\lambda_t$ (an intensity, like the Poisson and hazard
     rates), not $\eta_t$.
   - $\eta$ is the vol-of-vol everywhere: square-root process
     $dv=\kappa(\bar v-v)dt+\eta\sqrt v\,dW$ and OU long-run level $\bar x$
     ($\theta$ and $\xi$ are left free for $\theta_T$ and $\xi_t(u)$).
   - The money-market account is $B_t$ (not $\beta_t$), and the barrier level is
     $H$.
   - The collateral threshold is $\mathrm{Th}$. The convenience yield is $y_c$.
   - MA coefficients are $\vartheta_j$. The SLV leverage function is $L(t,S)$.
3. **Running project.** `code/firm/INTERFACES.md` freezes the pricing library,
   Book 5 → Book 6. The 113 component names in its §3 are reserved and
   unique.
4. **Term strings follow the owner's wording.** When you name another book's
   term in prose, use the owner's string: *Monte Carlo method*,
   *Euler–Maruyama scheme*, *finite-difference method*, *shrinkage
   estimator*, *Ornstein–Uhlenbeck process*, *cubic spline*, *principal
   component analysis*, *Cholesky factorisation*, *Spearman's rank
   correlation*, and so on. Book 6 writes *curve bootstrapping* for curves;
   *bootstrap* is Book 4's statistical term.
5. **Interview roles.** `risk` is added to the role list (`trader, researcher,
   developer, mle, bank, risk`).
6. **No scipy.** The `.venv` stays numpy + pandas (+ pytest, ruff), as in
   Books 1–2. Write your own optimisers and special functions; critical-value
   tables are ledger rows.
7. **`tools/gates.sh`** "defined twice" is now multi-line aware (perl
   harvest). `make_briefs.py` writes `\mbox{}` in solution stubs.
   `styles/onequant.sty` has commodity units: `\barrel`, `\mmbtu`, `\therm`,
   `\bushel`, `\troyounce` (`\tonne`, `\watt`, `\hour` are siunitx
   built-ins).
8. **Defects reported in Books 1–2** (missing `\index` on *delta*,
   *intrinsic value* and *borrow fee* in Book 1) are fixed by the main session
   at the reconciliation. Do not touch Books 1–2.
9. **No outline changes.** Chapter numbering is frozen as in the outlines.

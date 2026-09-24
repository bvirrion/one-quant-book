# Contributing to the One Quant Book series

Read `WRITING_A_QUANT_BOOK.md` first: it is the full procedure. This file is
the short reference a contributor keeps open while writing.

## Ground rules

- Packages, macros and environments live **only** in `styles/onequant.sty`.
- Code is never pasted into a chapter: write it under `code/`, test it, print
  an excerpt with `\omcode{path}{first}{last}{caption}` (≤ 40 lines).
- Every checkable external fact has a row in the chapter's source ledger
  (`sources/<slug>/NN-chapter.md`); volatile facts live in `dated` boxes.
- A firm is named only when the ledger holds a public source for the claim.
- New terms: `\emph{term}\index{term}` inside a `definition`, once in the
  series. `\omterm` links are generated, never hand-written.
- `` ``quotes'' `` never `"`; `\dots` never `...`; `\cref` never `\ref`.

## Environments

| Environment | Use | Label |
|---|---|---|
| `definition theorem proposition lemma corollary method example remark notation` | the lesson | `def: thm: prop: lem: cor: met: ex: rem: not:` |
| `strategyfile{Title}` with nine `\sfield{…}` | a strategy | `strat:` |
| `predictorcard{Title}` with `\sfield{…}` | a predictor | `pred:` |
| `dated{YYYY-MM}{Title}` | a volatile fact | `dat:` |
| `tutorial` + `tutsteps` inside `\section{Tutorial: …}` | guided code | `tut:` on the section |
| `build` with `\bfield{…}` inside `\section{Build: …}` | specification | `bld:` on the section |
| `exercise[$\star$]` | 8 per chapter, 3/3/2 | `exo:` first thing inside |
| `problem[{Weekend problem --- …}]` | one per chapter | `pb:` first thing inside |
| `interviewq[$\star$ \iqroles{trader, researcher}]` | 5–8 per chapter | `iq:` first thing inside |
| `omsources` | end of lesson | — |
| `solution{<key>}`; `\iqlookfor{…}` closes an interview solution | solutions file | — |

Roles for `\iqroles`: `trader, researcher, developer, mle, bank`.

## Ledger format

```
| id | claim | source | URL | accessed | evidence | used in |
| F1 | … | … | https://… | 2026-09-18 | quote / page | dat:m1:…:… or §2 |
```
Rows start with `F<n>`. Unverifiable facts go under a heading `## EXCLUDED`.

## Interim notation (until One Quant Book 4 fixes the series notation)

| Symbol | Meaning |
|---|---|
| $b_t, a_t$ | best bid, best ask; $m_t = \tfrac12(a_t+b_t)$ mid; $s_t = a_t - b_t$ spread |
| $q$ | signed quantity (positive = long / buy) |
| $S_t$ | spot price; $F_{t,T}$ forward or futures price for delivery at $T$ |
| $r$ | financing rate (continuously compounded unless stated); $d$ dividend yield; $\ell$ borrow (stock-loan) fee |
| $\tau = T - t$ | time to expiry in years (ACT/365 unless stated) |
| $K$ | strike; $C, P$ call and put prices; $\sigma$ volatility |
| $\pnl$ | profit and loss; $\E, \Var, \Cov, \P$ as usual |
| units | `\qty{1.5}{\bp}`, `\qty{2}{\tick}`, `\money{USD}{2400000}`, latencies in `\micro\second` |

Rates, FX and credit (added for One Quant Book 2):

| Symbol | Meaning |
|---|---|
| $P(t,T)$ | discount factor (price at $t$ of 1 paid at $T$); $P(T) = P(0,T)$ |
| $\delta$, $\delta_i$ | accrual (day-count) fraction of a period |
| $y$ | yield to maturity; $c$ coupon rate (bond coupon, or a CDS standard coupon) |
| $F(t;T_1,T_2)$ | simple forward rate for $[T_1,T_2]$ seen at $t$; $f(t,T)$ instantaneous forward |
| $D$, $D_{\mathrm{mod}}$, $\mathrm{DV01}$ | Macaulay and modified duration; value of one basis point (currency, positive for a long bond) |
| $\mathcal{C}$ | convexity |
| $r_{\mathrm{on}}$ | overnight benchmark rate; $K$ fixed rate of a swap (as a strike) |
| $S$, $F$ | FX spot and outright forward, in units of the **quote** currency per one unit of the **base** currency (pair written `EURUSD`); $r_d$, $r_f$ domestic (quote) and foreign (base) rates |
| $\lambda$ | hazard rate; $R$ recovery rate; $\mathcal{S}$ a credit spread (CDS par spread, bond Z-spread $z$) — never $s$, which is the bid–ask spread |

## Gates

`tools/gates.sh chapter <slug>/<NN-chapter>`, `make test-code CH=<slug>/<NN-chapter>`,
`latexmk && tools/gates.sh log`, then render and read every figure
(`tools/figpage.sh "<caption words>"`).

## Code naming

- Chapter modules live in `code/<slug>/NN-chapter/python/` and must have a
  name unique in the book (tests of all chapters run in one pytest session).
- Running-project modules live in `code/firm/<component>/firm_<component>.py`
  (the `firm_` prefix keeps them from colliding with a chapter's teaching
  module of the same name); their acceptance tests in `…/tests/`.
- Chart scripts are `fig_*.py`; they write only under `figdata/`.

# One Quant Book — series outline (draft for discussion)

Status: **discussion draft, 2026-09-18.** Nothing here is written yet; chapter
lists, titles and page counts are proposals.

## Premises

- **English only.** No translations planned.
- **Reader prerequisites:** programs fluently in C++, Rust and Python; has a
  master's-level mathematical culture (measure, linear algebra, analysis,
  basic probability and statistics). The series teaches only the
  quant-specific layer on top.
- **Goal:** a reader who finishes all eighteen books and does every tutorial
  and build knows what is publicly knowable about the trade — every market,
  HFT and MFT, bank side and asset-manager side, operational and strategic,
  quant and software.
- **Naming firms:** a practice is attributed to a named firm only where a
  citable public source says so (paper, regulatory or court document,
  conference talk, firm blog, patent, interview). Otherwise: "a large options
  market maker".
- **Freshness:** venue-specific and regulation-specific facts go in dated
  boxes, checked against primary documentation at writing time. Mechanisms go
  in the main text.

## Chapter anatomy

1. Hook — a concrete scene from a desk, a venue or an incident.
2. Lesson — the usual definition / theorem / proposition / method / example /
   remark boxes.
3. **Strategy files** (where relevant) — fixed template: who pays you and
   why; instruments and venues; signal construction; sizing and execution;
   costs; how it dies (with the episode); horizon, capacity, infrastructure;
   how to backtest it honestly; sources.
4. **Tutorial** — guided walk-through with code (Python for research, C++ for
   systems, Rust twins in the companion tree).
5. **Build it** — a specified piece of the running project, with acceptance
   tests in the companion tree.
6. Exercises — graded one to three stars (about 8).
7. Weekend problem — story-driven, about 20 questions, one named result.
8. **Interview questions** — 5 to 8, with full solutions.

## The running project: a miniature trading firm

Built piece by piece across the series: exchange simulator and matching
engine (Book 10), agent-based market (10), feed handler, order book, gateway
and risk gate, then the measured tick-to-trade path (13), a connectivity plan
and budget (14), backtester at four fidelity levels (7, 15), pricing library
(5) and risk engine (6), market-making and execution strategies (10, 11), an
order-book ML model served at low latency (12), position and P&L services
(15).

**Code gate (new, on top of the One Course gates):** no listing is printed
unless it is included from a file that CI compiles and tests.

## The eighteen books

Every title starts with **One Quant Book N** so the series reads as one work;
the cover's book line carries it the same way.

Page counts are all-in (chapter + its share of the solutions appendix), plus
about 20 pages of front and back matter per book.

| # | Title | Chapters | Pages | Detail |
|---|---|---|---|---|
| 1 | One Quant Book 1 — Markets I: The Ecosystem and Exchange-Traded Markets | 31 | 374 (written) | `outline/markets.md` |
| 2 | One Quant Book 2 — Markets II: Rates, FX and Credit | 31 | 363 (written) | `outline/markets.md` |
| 3 | One Quant Book 3 — Markets III: Commodities, Energy and Crypto | 29 | 332 (written) | `outline/markets.md` |
| 4 | One Quant Book 4 — Quantitative Methods | 29 | 351 (written) | `outline/methods-derivatives.md` |
| 5 | One Quant Book 5 — Derivatives and Volatility | 28 | 348 (written) | `outline/methods-derivatives.md` |
| 6 | One Quant Book 6 — Rates, Credit, XVA and Risk | 29 | 314 (written) | `outline/methods-derivatives.md` |
| 7 | One Quant Book 7 — Research Craft: Predictors, Backtests, Measurement, Portfolios | 29 | 345 (written) | `outline/research-strategies.md` |
| 8 | One Quant Book 8 — Strategies I: Equities and Futures | 29 | 330 (written) | `outline/research-strategies.md` |
| 9 | One Quant Book 9 — Strategies II: Volatility, Relative Value, Macro and the Bank Desks | 29 | 333 (written) | `outline/research-strategies.md` |
| 10 | One Quant Book 10 — Microstructure and Execution | 28 | 303 (written) | `outline/microstructure-hft-ml.md` |
| 11 | One Quant Book 11 — Market Making and High-Frequency Trading | 29 | 330 (written) | `outline/microstructure-hft-ml.md` |
| 12 | One Quant Book 12 — Machine Learning for Markets | 29 | 348 (written) | `outline/microstructure-hft-ml.md` |
| 13 | One Quant Book 13 — Low-Latency Software | 26 | 314 (written) | `outline/engineering-firm-interviews.md` |
| 14 | One Quant Book 14 — Networks, Hardware and Trading Infrastructure | 29 | 349 (written) | `outline/engineering-firm-interviews.md` |
| 15 | One Quant Book 15 — Research, Data and Risk Platforms | 30 | 367 (written) | `outline/engineering-firm-interviews.md` |
| 16 | One Quant Book 16 — The Desk and the Firm | 30 | 347 (written) | `outline/engineering-firm-interviews.md` |
| 17 | One Quant Book 17 — The Industry: Firms, Roles and Careers | 30 | 339 (written) | `outline/engineering-firm-interviews.md` |
| 18 | One Quant Book 18 — The Interview Book | 29 | 220 (written; new-questions-only shape) | `outline/engineering-firm-interviews.md` |

Total: 524 chapters, about 7,070 pages, and about 300 strategy files
(231 in Books 8–9, 75 in Book 11). Books 6 and 13 have the most headroom;
Books 1, 2 and 18 run slightly over 400.

Measured (2026-09-26): Books 1–13 are written, 4,385 pages against the
outline's 5,088 for them (−14 %; Books 10–13, written in one parallel batch, 1,295 against 1,530,
−15 %). Books 1–9 alone: 3,090 pages against the outline's 3,558 for them (−13 %), with 236 strategy files in Books 8–9 (outline
231). Written books run 10.8–12.4 pages a chapter all-in; the per-chapter
figures above overstate by 1–3 pages wherever they exceed 12, so the series
total will land nearer 6,200 than 7,070.

Measured (2026-09-29): Books 14–16, written in one parallel batch of three, 1,063 pages against the
outline's 1,182 for them (−10 %). Books 17–18: 559 pages against 632 (−12 %). **The series is complete: 18
books, 524 chapters, 6,007 pages.**

## Reading paths

| Role | Books |
|---|---|
| Quant researcher, HFT | 1, (2 or 3 by asset class), 4, 7, 10, 11, 12 |
| Quant researcher, MFT | 1, 4, 7, 8, 10, 12 |
| Bank quant (pricing / risk) | 1, 2, 4, 5, 6, 15 |
| Options market maker / vol trader | 1, 4, 5, 9, 11 |
| Macro / rates / credit trader | 2, 6, 9 |
| Commodities / power trader | 3, 6 (ch. 16), 9 |
| Crypto trader | 3, 10, 11, 14 (Part IV) |
| Quant dev / software engineer | 1, 10, 13, 14, 15 |
| Network / infrastructure engineer | 1, 13, 14 |
| ML engineer | 1, 4, 7, 12, 15 |
| Portfolio manager / head of desk | 1, 7, 8 or 9, 16 |
| CEO / CTO | 1, 16, then skim 11, 13, 14, 15 |
| Everyone | 17 (first or last — it needs no prerequisites), 18 |

## Proposed writing order

1 → 2 → 3 → 4 → 10 → 5 → 7 → 11 → 13 → 14 → 8 → 6 → 9 → 12 → 15 → 16 → 17 → 18.
The three Markets books fix the vocabulary; Book 10 comes early because
it builds the exchange simulator every later tutorial runs on; Book 18 is
last because its interview banks sit on top of every other book (it writes new
questions only and does not harvest the per-chapter ones: user ruling, 2026-09-28).

## The access layer (added 2026-09-18)

Every market is covered at three levels, never only the first:

1. **Mechanism** — how the market works (Books 1–3, 10).
2. **Commercial access** — a "Getting access" chapter closing each market part
   of Books 1–3: entity and membership, clearing or prime broker, fee
   schedules and tier negotiation, market-maker programmes and their
   obligations, data licences, what the top tiers unlock (raised rate limits,
   private or dedicated gateways). The negotiator's side is Book 16 ch. 23.
3. **Physical access** — Book 14: data centres, colocation products,
   long-haul fibre and wireless, how connectivity is bought and from whom,
   public-cloud trading, six chapters of crypto connectivity, one chapter per
   other sector, the vendor map.

## Open points

- Book 11 is the likeliest to overflow (crypto and options strategy files);
  decide on a split when writing it.
- Label prefixes per book (proposal): `m1 m2 m3 qm dv rc rs s1 s2 mx hf ml
  ll nw pl fm in iv`.
- A quant addendum to `book_style.md` (new environments, code gate, visuals
  policy: schematics and pgfplots charts first, licensed photographs where a
  real thing is shown, few AI illustrations) must be written before chapter 1.

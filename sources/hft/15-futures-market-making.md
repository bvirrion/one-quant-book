# 15. Futures Market Making — brief and source ledger

## Brief

- **Hook.** In a short-rate futures contract the queue at the best price holds tens of thousands of lots and fills are shared pro rata; a market maker who wants a hundred lots shows thousands, and every other maker knows it.
- **Sections.** Pro-rata books and size; Calendar spreads and implied prices; Arbitrage between spread and outright books; Rates futures strips; Inter-commodity spreads.
- **Defines.** over-quoting, implied-price arbitrage.
- **Uses (defined earlier).** pro-rata allocation (B1.19), top-order allocation (B1.19), implied-in (B1.19), implied-out (B1.19), calendar spread (B1.19), pack (B2.8), bundle (B2.8), futures strip (B2.8), overnight-rate future (B2.8), lead market maker (B1.19), inter-commodity spread credit (B1.20), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** pro-rata outright quoting; calendar-spread quoting with implied legs; implied-price arbitrage between spread and outright books; short-rate futures strip making; inter-commodity spread trading.
- **Tutorial.** Match a pro-rata book with firm.match, show the over-quoting equilibrium when every maker scales its size to its share, then quote a strip of short-rate futures and its calendar spreads with implied prices and find the arbitrage when an implied price lags.
- **Build.** `firm.futmm`: pro-rata fill model with top-order and minimum-allocation rules, over-quoting best response, implied-price computation across a strip, spread-outright arbitrage scanner; Python, on firm.match.
- **Weekend problem.** Showing ten times what you want — named result: the equilibrium over-quoting factor in a pro-rata book, and the inventory risk it creates when an unexpectedly large order fills everyone at once.
- **Facts to verify.** CME Globex matching algorithms (pro-rata, allocation, split FIFO) (dated); CME implied functionality description (dated); Field and Large 2008 Pro-rata matching and one-tick futures markets (working paper); Eurex or ICE pro-rata products (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Field and Large (2008): four one-tick pro-rata futures markets; offered depth at the quotes exceeds mean market order size by two orders of magnitude; cancellation rates over 96%; model of strategic complementarities in limit order size causing over-sized orders expected mostly to be cancelled | J. Field, J. Large, "Pro-rata matching and one-tick futures markets", CFS Working Paper 2008/40 | https://econpapers.repec.org/RePEc:zbw:cfswop:200840 | 2026-09-25 | abstract: "offered depths at the quotes on average exceed mean market order size by two orders of magnitude, and their order cancellation rates ... are significantly over 96 per cent"; "strategic complementarities in the choice of limit order size cause traders to risk overtrading by submitting over-sized limit orders, most of which they expect to cancel" | §1; strategy file |
| F2 | CME pro-rata allocation as described in a vendor guide (Aug 2025): matched by each resting order's pro-rated percentage, rounded down to integer incl. 0, excess FIFO; top order (first to improve the market) matched first, then LMM; pro rata listed for some calendar-spread books; configurable algorithm for outrights incl. ZT | Databento blog, "CME matching algorithms explained", 1 August 2025 | https://databento.com/blog/cme-matching-algorithms-explained | 2026-09-25 | "An incoming aggressor order quantity is matched based on each resting order's pro-rated percentage. Allocations are rounded down to the nearest integer, including 0. Excess lots are allocated FIFO."; "First order that improves the market is matched (top order), followed by LMM allocation and FIFO" | dat:hf:futures-market-making:cme |

## EXCLUDED

- CME Client Systems Wiki pages: content not returned by the fetcher; the vendor guide is cited instead, as a description.
- Eurex/ICE pro-rata product lists: not fetched.

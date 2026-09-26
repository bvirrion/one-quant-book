# 21. FX Market Making — brief and source ledger

## Brief

- **Hook.** A non-bank liquidity provider streams euro-dollar prices to a hundred banks, brokers and platforms at once, each with its own price; a trade on one of them is hedged, or not, within microseconds on another.
- **Sections.** Principal electronic liquidity provision; Pricing from many venues; Streams, tiers and last look; Internalise or hedge; Crosses and emerging markets.
- **Defines.** liquidity aggregator, firm liquidity, synthetic cross.
- **Uses (defined earlier).** last look (B2.15), hold time (B2.15), reject rate (B2.15), quote skewing (B2.15), streaming quote (B2.15), liquidity tier (B2.15), primary venue (B2.14), electronic communication network (B2.14), internalisation (B1.10), client tiering (B9.24), cross rate (B2.14), non-deliverable forward (B2.18), FX Global Code (B2.15), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** primary-venue FX market making; disclosed streaming to aggregators with last look; cross-rate synthesis quoting; non-deliverable forward electronic making.
- **Tutorial.** Build a consolidated fair price from three simulated FX venues, stream tiered prices to simulated aggregators with and without last look, and choose between internalising and hedging each trade; measure capture, rejects and hedging cost.
- **Build.** `firm.fxlp`: multi-venue FX fair price, per-stream pricing with skew and tier, last-look check, internalise-or-hedge policy, synthetic crosses; Python, on firm.lastlook and firm.flowmm.
- **Weekend problem.** A hundred prices at once — named result: the liquidity provider's capture and reject rate with and without last look, and the hedge share at which internalising stops paying.
- **Facts to verify.** BIS Triennial Central Bank Survey 2025 FX turnover by counterparty and execution method (dated); Chaboud, Chiquoine, Hjalmarsson, Vega 2014 Rise of the machines (JF); Oomen 2017 Last look (QF); FX Global Code principle 17 on last look (dated); Euromoney FX survey or a firm's published market share (dated; only with a citable source).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | BIS Triennial Survey preliminary results (30 Sep 2025): FX trading $9.6 trillion per day in April 2025; FX swaps $4 trillion (+5% vs 2022); spot +42%, outright forwards +60%, shares 31% and 19%; USD on one side of 89% of trades; UK, US, Singapore, Hong Kong sales desks 75% | BIS press release p250930 | https://www.bis.org/press/p250930.htm | 2026-09-25 | "Global FX trading hits $9.6 trillion per day in April 2025"; "FX swaps remained the most traded instrument, with average daily turnover rising to $4 trillion"; "Turnover of FX spot increased by 42% and outright forwards rose 60%. Their shares in global turnover increased to 31% and 19%"; "being on one side of 89% of all FX trades"; "accounted for 75% of total FX trading" | dat:hf:fx-market-making:bis |
| F2 | Chaboud, Chiquoine, Hjalmarsson and Vega (2014): algorithmic trading improves price efficiency (triangular arbitrage frequency, return autocorrelation); fewer arbitrage opportunities mainly from computers taking liquidity (possibly higher adverse selection on slower traders); lower autocorrelation more from algorithmic liquidity provision | Journal of Finance 69(5), 2014, 2045-2084 | https://api.crossref.org/works/10.1111/jofi.12186 | 2026-09-25 | Crossref abstract: "the reduction in arbitrage opportunities is associated primarily with computers taking liquidity"; "the reduction in the autocorrelation of returns owes more to the algorithmic provision of liquidity" | §1; strategy file |

## EXCLUDED

- Oomen (2017) Last look (QF 17, 1057-1070): no abstract available through Crossref; last look's economics are left to Book 2 ch. 15 by pointer.
- FX Global Code principle 17: covered in Book 2 ch. 15; not restated.
- Market shares of named non-bank providers: no citable primary source fetched; no firm named.

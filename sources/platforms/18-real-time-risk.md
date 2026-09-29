# 18. Real-Time Risk — brief and source ledger

## Brief

- **Hook.** Each of two desks was inside its limit all afternoon. Together they were short twice the firm's appetite in the same index, and nobody saw it until the end-of-day batch, because nothing added the desks up while they traded.
- **Sections.** What real-time means for risk; Aggregation along the hierarchy; Incremental updates; Sensitivities, full revaluation and the gap; Limits in the loop.
- **Defines.** real-time risk system, exposure aggregation, incremental aggregation, risk snapshot, sensitivity cache, what-if check.
- **Uses (defined earlier).** risk engine (B6.29), risk factor (B6.21), risk hierarchy (B6.29), risk limit (B6.29), pricing engine (B5.28), market-data snapshot (B5.28), bump-and-reprice (B5.4), Greeks (B5.4), risk data aggregation (B6.29), full revaluation (B6.29), delta--gamma approximation (B6.21), risk-based attribution (B6.27), pre-trade risk check (B11.27), kill switch (B11.27), risk gate (B13.22), limit utilisation (B16.7), position service (ch17), stream processing (ch1).
- **Tutorial.** Stream fills from two desks' strategies (firm.posservice) and market moves into a risk aggregator: sensitivities per trade from Book 5's pricing library, cached and refreshed on market moves above a threshold, aggregated incrementally along Book 6's hierarchy; compare the sensitivity-based P\&L with full revaluation over the day's moves; check desk and firm limits (Book 11's policy) on every update, and ask the aggregator what a proposed trade would do before sending it. End state: desk and firm exposure through the afternoon with the firm-level breach the desks could not see, and the sensitivity approximation's error against move size.
- **Build.** `firm.rtrisk`: `Aggregator` over a risk hierarchy with incremental updates on fills and market ticks, a sensitivity cache on firm.pricing with invalidation rules, risk snapshots with timestamps and staleness, a what-if check for proposed trades, limit evaluation against firm.riskctl limits with alerts; Python.
- **Weekend problem.** Two desks, one index -- named result: the time at which the firm-level limit was breached while each desk stayed inside its own, the exposure at the close, and the size of the market move beyond which the sensitivity cache's P\&L error exceeds one percent of the full revaluation.
- **Facts to verify.** BCBS 239 principle on timeliness of risk data aggregation in stress; SEC Rule 15c3-5 pre-trade and post-trade controls (pointer B11.27); a public account of intraday risk aggregation architecture at a bank (paper or talk, dated).
- **Data.** Two desks on firm.exchsim and synthetic option books priced with firm.pricing.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|

## EXCLUDED

- BCBS 239 timeliness: pointer to Book 6 chapter 29 (its ledger row lists timeliness among the principles) and this book's chapter 1; the BIS PDF was not retrievable as text here.
- A public account of a bank's intraday risk aggregation architecture (brief): not searched.
- SEC Rule 15c3-5: pointer to Book 11 chapter 27.


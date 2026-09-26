# 2. Fair Value — brief and source ledger

## Brief

- **Hook.** The same stock quotes on a dozen venues, its future trades in Chicago and its ETF in New Jersey; the market maker's price is none of these quotes but its own estimate, updated on every message from any of them.
- **Sections.** Mid, weighted mid and microprice as estimators; Fair price across venues; Fair price across instruments; Filtering: the fair price as a state; Evaluating a fair price.
- **Defines.** fair price, consolidated fair price, cross-instrument fair price, fair-price filter.
- **Uses (defined earlier).** microprice (B7.8), weighted mid price (B7.8), queue imbalance (B7.8), Kalman filter (B4.19), microstructure noise (B4.21), national best bid and offer (B1.9), fair value (B1.21), lead--lag relationship (B7.10), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Tutorial.** On firm_tape's paired instruments (simulate_pair) and a synthetic multi-venue book, build weighted-mid, microprice, venue-weighted and Kalman fair prices and score each as a forecast of the efficient price and of the mid a few seconds later.
- **Build.** `firm.fairprice`: streaming fair-price estimators (weighted mid, microprice table, consolidated across venues with staleness weights, cross-instrument Kalman filter) with a common `update(event) -> price` interface; Python, streaming core in C++20 and Rust checked on one fixture.
- **Weekend problem.** Whose price is it — named result: the forecast error of each estimator against the efficient price, and the share of the improvement that comes from the second instrument.
- **Facts to verify.** Stoikov 2018 The micro-price (QF); Cartea, Jaimungal, Penalva 2015 Algorithmic and High-Frequency Trading (CUP); Gatheral and Oomen 2010 zero-intelligence realized variance estimation (F&S) or equivalent on noise.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Stoikov (2018): the micro-price, estimated from high-frequency data, is empirically a better predictor of short-term prices than the mid-price or the weighted mid-price | S. Stoikov, "The micro-price: a high-frequency estimator of future prices", Quantitative Finance 18(12), 2018, 1959-1966 | https://doi.org/10.1080/14697688.2018.1489139 | 2026-09-25 | Crossref metadata; OpenAlex abstract: "The micro-price estimated using high-frequency data is empirically a better predictor of short-term prices than the mid-price or the weighted mid-price" | §1 |

## EXCLUDED

- Real multi-venue or futures-ETF data: none licensed for redistribution; the chapter's markets are synthetic (firm.tape, a leader and a follower on two venues, lead 0.1 to 2 seconds planted).
- Cartea, Jaimungal and Penalva (2015) and Gatheral and Oomen (2010): not needed for any claim in this chapter; Cartea et al. cited in chapter 3.


# 18. Order-Book Replay Simulation — brief and source ledger

## Brief

- **Hook.** A market-making backtest earns money every day; the live strategy loses. The backtest had assumed that its quotes stood first in every queue they joined.
- **Sections.** Replaying a market-by-order feed; Where am I in the queue?; Latency; Fill logic; The missing market impact and how to bound it; The fourth level.
- **Defines.** order-book replay, queue position, queue-position model, latency model, order-entry latency, market-data latency, passive fill probability, market impact, counterfactual impact.
- **Uses (defined earlier).** market-by-order (B1.19), market-by-price (B1.19), price-time priority (B1.19), pro-rata allocation (B1.19), sequence number (B1.28), exchange timestamp (B1.28), adverse selection (B1.1), birth--death process (B4.8), queue imbalance (ch8), fill model (ch17), fidelity level (ch16), tape (ch2).
- **Tutorial.** Replay a firm.tape session through firm.lobreplay with a passive quoting strategy under three queue-position models and three latencies, and draw the P&L of each.
- **Build.** `firm.lobreplay`: level-3 replay engine (book reconstruction from MBO messages, our orders' queue positions under pluggable models, latency queues for entry and data, fill logic, an impact bound) in Python for research with a C++20 core and a Rust twin that reproduce the Python fills on a shared fixture.
- **Weekend problem.** Where did the queue go? — named result: the daily P&L of a passive strategy under each queue model and latency, and the latency at which its edge vanishes.
- **Facts to verify.** Moallemi and Yuan 2017 queue position valuation (working paper); Lehalle and Mounjid 2017 limit order placement, adverse selection and latency (Market Microstructure and Liquidity); Cont and de Larrard 2013 (SIAM J. Financial Math.); hftbacktest queue models (open-source documentation); exchange MBO feeds (CME MDP 3.0 MBO, Nasdaq ITCH) as sources of queue order.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | hftbacktest (open-source backtester) documentation, Order fill: a market-data replay-based tool in which your order cannot change the simulated market and no market impact is considered, so the order must be small enough not to make any impact; queue models for market-by-price data: RiskAverseQueueModel (decreases by cancellation happen only at the tail, the position advances only on trades) and ProbQueueModel (decreases happen before and after the position according to a probability function of it) | docs/order_fill.rst in the project repository | https://github.com/nkaz001/hftbacktest/blob/master/docs/order_fill.rst | 2026-09-25 | "your order cannot make any changes to the simulated market, no market impact is considered"; "The order queue position will be advanced only if a trade happens at the price"; "the decrease in quantity happens at both before and after the queue position" | sections 2, 5; iq 2; omsources |
| F2 | C.-A. Lehalle, O. Mounjid, "Limit order strategic placement with adverse selection risk and the role of latency", Market Microstructure and Liquidity 3(1) (2017) 1750009: the added value of exploiting a knowledge of liquidity imbalance is eroded by latency, when there is not enough time to cancel and reinsert limit orders | arXiv abstract 1610.00261; Crossref record | http://arxiv.org/abs/1610.00261 | 2026-09-25 | "the added value of exploiting a knowledge on liquidity imbalance is eroded by latency: being able to predict future liquidity consuming flows is of less use if you have not enough time to cancel and reinsert your limit orders" | section 3; pb 11; omsources |
| F3 | R. Cont, A. de Larrard, "Price dynamics in a Markovian limit order market", SIAM J. Financial Mathematics 4(1) (2013) 1-25: arrivals of market orders, limit orders and cancellations as a Markovian queueing system; the probability of an upward price move conditional on the state of the book | arXiv abstract 1104.4596; Crossref record | http://arxiv.org/abs/1104.4596 | 2026-09-25 | "arrivals of market order, limit orders and order cancellations are described in terms of a Markovian queueing system"; "the probability of an upward move in the price, conditional on the state of the order book" | omsources |

## EXCLUDED

- Moallemi and Yuan (2017), queue position valuation: SSRN record only, no abstract retrievable; not cited.
- CME MDP 3.0 MBO and Nasdaq ITCH as sources of queue order: covered in Book 1 (chapter 19) and chapter 2's ITCH dated box; not restated.
- All fills, P&L, mark-outs, shares of volume and impact bounds are computed on firm.tape and tested; the C++20 and Rust cores are checked on the shared fixture.

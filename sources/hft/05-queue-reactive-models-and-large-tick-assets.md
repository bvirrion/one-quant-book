# 5. Queue-Reactive Models and Large-Tick Assets — brief and source ledger

## Brief

- **Hook.** On a stock whose spread is one tick nearly all day, every market maker quotes the same prices; what separates them is where they stand in the queue, and an order at the front of a long queue is worth money before it trades.
- **Sections.** The large-tick regime; Queue-reactive intensities; The value of a place in the queue; When to join and when to leave; Queue-reactive simulation.
- **Defines.** queue-reactive model, queue value, queue-exit rule.
- **Uses (defined earlier).** large-tick asset (B10.6, by outline), small-tick asset (B10.6, by outline), queue imbalance (B7.8), queue depletion rate (B7.8), queue-position model (B7.18), birth--death process (B4.8), price-time priority (B1.19), queue position (B7.18), latency model (B7.18), order-book replay (B7.18), exchange simulator (B10.26, by outline).
- **Tutorial.** Estimate state-dependent add, cancel and trade intensities on firm_tape (large-tick configuration), simulate the queue-reactive model, and value a queue slot by its expected spread capture less adverse selection as a function of position and queue sizes.
- **Build.** `firm.qreactive`: queue-reactive intensity estimation and simulation (Huang--Lehalle--Rosenbaum), queue value by position, a join/leave rule tested in firm.mmharness; Python.
- **Weekend problem.** Front of the line — named result: the value of the first place in a queue against the tenth, in ticks, and the imbalance at which leaving beats staying.
- **Facts to verify.** Huang, Lehalle, Rosenbaum 2015 Simulating and analyzing order book data: the queue-reactive model (JASA); Moallemi and Yuan 2017 A model for queue position valuation in a limit order book (working paper / MS); Cont, Stoikov, Talreja 2010 A stochastic model for order book dynamics (OR); Dayri and Rosenbaum 2015 Large tick assets: implicit spread and optimal tick size (MMF).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Huang, Lehalle and Rosenbaum (2015): within periods of constant reference price the order book is a Markov queuing system whose order-flow intensities depend only on the current state of the book; parameters estimated from market data; a stochastic mechanism switches reference-price periods; useful as a market simulator and for transaction cost analysis | W. Huang, C.-A. Lehalle and M. Rosenbaum, "Simulating and analyzing order book data: the queue-reactive model", Journal of the American Statistical Association 110(509), 2015, 107-122 | https://doi.org/10.1080/01621459.2014.982278 | 2026-09-25 | OpenAlex abstract: "we assume that the intensities of the order flows only depend on the current state of the order book" | §2 |
| F2 | Moallemi and Yuan: a model valuing orders by relative queue position with a static component (spread earned against adverse selection costs, which increase with queue position) and a dynamic component (the optionality of future value); for some large-tick stocks queue value is of the same order of magnitude as the bid-ask spread | C. C. Moallemi and K. Yuan, "A model for queue position valuation in a limit order book", working paper, December 2016 (SSRN 2996221) | https://moallemi.com/ciamac/papers/queue-value-2016.pdf | 2026-09-25 | SSRN and Columbia abstract, via search: "queue value can be of the same order of magnitude as the bid-ask spread" | §3 |
| F3 | Cont, Stoikov and Talreja (2010), "A stochastic model for order book dynamics", Operations Research 58(3), 549-563: the book as a continuous-time Markov chain of queues | Crossref metadata | https://doi.org/10.1287/opre.1090.0780 | 2026-09-25 | Crossref: journal, volume, issue, pages | §2 |
| F4 | Dayri and Rosenbaum (2015), "Large tick assets: implicit spread and optimal tick size", Market Microstructure and Liquidity 1(1), 1550003 | Crossref metadata | https://doi.org/10.1142/S2382626615500033 | 2026-09-25 | Crossref: journal, volume, article number | §1 |

## EXCLUDED

- Real queue data (ITCH or exchange MBO): not licensed for redistribution; estimation on firm.tape only.
- The printed queue values are the fitted queue-reactive model's, not Moallemi and Yuan's (their model has an information component this chapter's fitted model lacks; the chapter says so).


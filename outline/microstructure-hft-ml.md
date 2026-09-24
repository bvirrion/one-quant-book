# Books 10–12 — Microstructure, HFT, Machine Learning

Pages are all-in (chapter + its share of solutions). Each book adds ~20 pages
of front and back matter. Bracketed numbers are planned strategy files.

---

## One Quant Book 10 — Microstructure and Execution (~378 pp)

**Part I — The order book**

1. **The limit order book** (14 pp) — State, events, priority; the book as a data structure and as a queueing system.
2. **Order types and their uses** (12 pp) — Limit, market, stop, pegged, hidden, iceberg, post-only, immediate-or-cancel, intermarket sweep; who uses which and why.
3. **Empirical facts of order books** (14 pp) — Depth profiles, arrival and cancellation rates, spread distributions, intraday shapes.
4. **Why there is a spread** (14 pp) — Order-processing, inventory and information theories; the sequential-trade and strategic-trader models.
5. **Decomposing the spread** (12 pp) — Effective and realised spreads, price impact of a trade, estimating the adverse-selection share.
6. **Tick size, queues and priority** (14 pp) — Large-tick and small-tick regimes, the value of queue position, tick-size experiments.
7. **Fees, rebates and venue economics** (12 pp) — Maker-taker, inverted and flat pricing, tiers, how fees move the effective tick.
8. **Fragmentation and routing** (12 pp) — Many venues, one stock: consolidated books, protected quotes, latency between venues.
9. **Dark pools and blocks** (12 pp) — Midpoint and conditional orders, minimum quantities, information leakage, block venues.
10. **Auction mechanics and theory** (12 pp) — Uncrossing rules, indicative prices, strategic behaviour near the uncross.

**Part II — Market impact**

11. **The empirics of price impact** (14 pp) — Impact of single trades and of whole orders, the square-root law, measurement pitfalls.
12. **Transient impact and propagator models** (14 pp) — Decaying impact kernels, the long memory of order flow, no-manipulation conditions.
13. **Metaorders, latent liquidity and cross-impact** (12 pp) — Why impact is concave; impact across correlated instruments.

**Part III — Optimal execution**

14. **The Almgren–Chriss framework** (14 pp) — Risk against impact, the efficient frontier of execution, closed forms.
15. **Beyond Almgren–Chriss** (14 pp) — Execution with signals, stochastic liquidity, transient impact, control formulations.
16. **Benchmark algorithms** (14 pp) — Volume-weighted, time-weighted, participation, implementation-shortfall and close algorithms: schedules and their volume forecasts.
17. **Child-order placement** (14 pp) — Passive against aggressive, queue management, repricing logic, reinforcement-learning placement.
18. **Smart order routing** (12 pp) — Venue ranking, fill-probability models, fee-aware routing, anti-gaming.
19. **Transaction-cost analysis** (14 pp) — Benchmarks, slippage attribution, peer comparison, feeding the loop back to the algorithm.
20. **The buy-side trading desk and its brokers** (10 pp) — Algo wheels, broker evaluation, high-touch against low-touch.
21. **Execution beyond equities** (14 pp) — Futures, FX, bonds and crypto: what changes when the market is request-for-quote, last-look or round-the-clock.
22. **Portfolio trades and risk bids** (12 pp) — Pricing a basket for a client, principal bids, transition management.

**Part IV — Dealer markets and market quality**

23. **Request-for-quote and dealer markets in theory** (12 pp) — Search, bargaining, winner's curse among dealers, how many dealers to ask.
24. **Market quality and regulation** (12 pp) — Measuring liquidity, the high-frequency-trading debate in the evidence, the flash-crash literature.
25. **Circuit breakers and halts** (8 pp) — Designs, magnet effects, reopening.

**Part V — Builds**

26. **Build: a matching engine and exchange simulator** (16 pp) — Price-time and pro-rata matching, order types, a market-data feed and an order-entry protocol: the venue every later tutorial trades on.
27. **Build: an agent-based market** (12 pp) — Populating the simulator with noise, informed and market-making agents; reproducing the stylised facts.
28. **Build: an execution algorithm** (12 pp) — A complete shortfall algorithm, measured with the chapter 19 toolkit.

---

## One Quant Book 11 — Market Making and High-Frequency Trading (~396 pp)

**Part I — Core theory and components**

1. **The business of market making** (12 pp) — Revenue per trade, volume, inventory cost, technology cost; what the public financial statements of listed market makers reveal.
2. **Fair value** (14 pp) — Mid, weighted mid, microprice, multi-venue and multi-instrument fair values, filtering.
3. **Inventory models** (14 pp) — The Avellaneda–Stoikov framework: reservation price, optimal spread, closed forms and their limits.
4. **Extensions of the inventory framework** (12 pp) — Asymptotic solutions, multi-asset quoting, signals and adverse selection inside the control problem.
5. **Queue-reactive models and large-tick assets** (14 pp) — State-dependent intensities, the value of a queue slot, when to join and when to leave.
6. **Adverse selection and toxicity** (14 pp) — Markouts by counterparty, venue and order type; detecting informed flow; widening, fading and skewing.
7. **Short-horizon alpha** (16 pp) — Building the seconds-and-below forecast from book, flow and cross-asset predictors; coupling it to quoting. [5]
8. **Lead-lag and cross-venue trading** (14 pp) — Futures to cash, ETF to constituents, venue to venue; estimating lag at asynchronous ticks. [5]
9. **Latency arbitrage and its defence** (14 pp) — Stale-quote sniping, the arms race in the evidence, speed bumps and asymmetric delays, last look. [4]
10. **The quoting engine** (14 pp) — Cancel-replace logic, throttles and message limits, self-match prevention, layering quotes without crossing the line.
11. **Hedging and inventory in practice** (12 pp) — Hedge instrument choice, partial hedging, end-of-day and overnight inventory.

**Part II — Strategy files by market**

12. **ETF market making** (16 pp) — Pricing from the basket, create-redeem arbitrage, fixed-income and international ETFs when the underlying is closed. [5]
13. **Index and basket arbitrage** (12 pp) — Futures against cash baskets, financing, dividend and execution risk. [3]
14. **Depositary receipts and dual listings** (10 pp) — Conversion, currency leg, non-overlapping hours. [3]
15. **Futures market making** (14 pp) — Pro-rata products, calendar-spread and implied-price strategies, rates futures stacks. [5]
16. **Auctions and the close** (10 pp) — Imbalance-feed strategies, providing liquidity into the uncross. [3]
17. **Rebates, inverted venues and tiers** (10 pp) — Fee-driven strategies and volume-tier economics. [3]
18. **News and event trading** (12 pp) — Scheduled numbers, machine-readable headlines, social-media events; the race and its risk controls. [4]
19. **Automated options market making** (16 pp) — Live surface fitting, mass quoting and quote protection, delta hedging, per-strike and per-expiry risk limits, the documented approaches of the major firms. [5]
20. **Options: cross-venue and volatility arbitrage at speed** (12 pp) — Parity and box violations, dividend and exercise plays, surface arbitrage across listings. [4]
21. **FX market making** (14 pp) — Principal electronic liquidity provision: pricing from many venues, client tiering, skew, internalisation against external hedging. [4]
22. **Bond and ETF request-for-quote market making** (14 pp) — Pricing illiquid bonds, hit-rate models, winner's curse, portfolio trades. [4]
23. **Retail wholesaling** (12 pp) — Pricing and internalising retail flow, price-improvement economics, inventory from one-sided flow. [3]
24. **Crypto high-frequency trading on centralised venues** (14 pp) — Cross-exchange making and taking, funding and basis at speed, liquidation flows, rate-limit-aware quoting. [6]
25. **On-chain trading** (14 pp) — Exchange-to-chain arbitrage, liquidations, just-in-time liquidity, searching and bundle bidding; sandwiching described and legally situated. [6]
26. **Prediction and sports market making** (10 pp) — Pricing models, in-play latency, limits and counterparty selection. [3]

**Part III — Running it**

27. **Risk controls** (12 pp) — Pre-trade limits, position and loss limits, price collars, kill switches, the regulatory requirements for algorithmic firms.
28. **P&L analytics and the strategy lifecycle** (12 pp) — Daily attribution, parameter changes as experiments, when to retire a strategy.
29. **A venue playbook** (12 pp) — One page per major venue type: matching rule, fees, feed, quirks, the strategies that live there.

---

## One Quant Book 12 — Machine Learning for Markets (~392 pp)

**Part I — Foundations for noisy, non-stationary data**

1. **Why financial machine learning is different** (12 pp) — Signal-to-noise near zero, non-stationarity, adversarial feedback, small effective sample.
2. **Targets, labels and sample weights** (12 pp) — Horizon returns, barrier labels, overlapping samples, uniqueness weighting.
3. **Validation** (14 pp) — Walk-forward, purged and embargoed folds, combinatorial splits, leakage hunting.
4. **Linear and regularised baselines** (12 pp) — The model to beat, and why it often wins.
5. **Trees and boosting** (16 pp) — Gradient boosting as the workhorse: losses, regularisation, monotonic constraints, tuning under noise.
6. **Feature engineering, selection and importance** (14 pp) — Transformations, stability selection, permutation and additive-attribution importances, their failure modes.

**Part II — Deep learning**

7. **Neural networks for noisy tabular data** (14 pp) — Architectures, normalisation, regularisation, ensembling, seeds as a source of variance.
8. **Sequence models on order books** (16 pp) — Convolutional, recurrent, temporal-convolutional and attention models on book and trade streams; what the literature replicates.
9. **Cross-sectional deep models** (12 pp) — Panels of assets, embeddings, learned factor models.
10. **Representation learning** (12 pp) — Autoencoders, contrastive objectives, pre-training on unlabelled market data.
11. **Probabilistic models and uncertainty** (12 pp) — Predictive distributions, quantile and distributional losses, using uncertainty in sizing.
12. **Online learning and drift** (14 pp) — Recursive estimators, forgetting, drift detection, retraining schedules.

**Part III — Text, alternative data, generative models**

13. **Text: from bag of words to embeddings** (12 pp) — Sentiment, topic, event extraction, entity linking to tickers.
14. **Large language models in finance** (16 pp) — Filings, calls and news at scale; retrieval; evaluation without leakage from the model's own training cut-off; agents in research workflows.
15. **Alternative-data pipelines** (12 pp) — Ingestion, panel bias, mapping to securities, backfill detection.
16. **Generative models and synthetic data** (12 pp) — Synthetic order flow and price paths: uses, and the ways they mislead.

**Part IV — Decisions**

17. **Reinforcement learning foundations** (14 pp) — Value and policy methods, off-policy evaluation, the simulator problem.
18. **Reinforcement learning for execution and market making** (14 pp) — State, action and reward design; what works in the published evidence.
19. **Deep hedging and machine learning in pricing** (14 pp) — Hedging under frictions, surrogate pricers, calibration networks.
20. **Clustering, regimes and anomaly detection** (12 pp) — Regime models, correlation clustering, trade-surveillance detectors.
21. **Interpretability and model governance** (10 pp) — Explaining a model to a risk committee; validation of learned models.
22. **From prediction to portfolio** (12 pp) — Loss functions aligned with P&L, end-to-end learning through the optimiser.

**Part V — Machine-learning engineering**

23. **Training infrastructure** (14 pp) — Accelerators, distributed training, mixed precision, data loaders for tick data.
24. **Data and feature stores** (12 pp) — Point-in-time feature serving, the same features offline and online.
25. **Experiment tracking and reproducibility** (10 pp) — Versioning data, code and models; the audit trail.
26. **Low-latency inference** (16 pp) — Compiling trees and small networks, quantisation, batching against latency, inference in C++ and on programmable hardware.
27. **Monitoring and retraining** (10 pp) — Feature and prediction drift, performance alarms, safe rollouts.
28. **The machine-learning team** (8 pp) — Researcher, engineer and platform roles; how work moves between them.
29. **Build: an order-book model, end to end** (14 pp) — Train on simulator data, validate properly, serve within a latency budget, trade it in the simulator.

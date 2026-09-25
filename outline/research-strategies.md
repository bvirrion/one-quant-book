# Books 7–9 — Research Craft and the Strategy Catalogue

Pages are all-in (chapter + its share of solutions). Each book adds ~20 pages
of front and back matter. Chapters in Books 8 and 9 are built around
**strategy files** (fixed template, see `OUTLINE.md`); the number in brackets
after a summary is the planned count of strategy files.

---

## One Quant Book 7 — Research Craft: Predictors, Backtests, Measurement, Portfolios (written: 345 pp; outline estimate was ~398)

**Part I — Process and data**

1. **The research process** (12 pp) — Hypothesis first, the research log, what counts as evidence, how a research idea moves to production.
2. **Market data for research** (14 pp) — Ticks, quotes, bars by time, volume and value; adjustments; what each representation destroys.
3. **Point-in-time data and the biases** (14 pp) — Survivorship, look-ahead, restatements, timestamp semantics, as-of joins.
4. **Universe, symbology and corporate actions** (12 pp) — Defining a tradable universe through time; identifiers that change; adjusting without leaking.
5. **Stylised facts of returns** (12 pp) — Heavy tails, volatility clustering, leverage effect, intraday seasonality, cross-sectional structure.

**Part II — The predictor catalogue**

6. **Anatomy of a predictor** (12 pp) — Target definition, horizon, normalisation, neutralisation, information coefficient, the predictor card used in the rest of the part.
7. **Price and volume features** (14 pp) — Returns at many scales, volatility, range, volume surprise, the standard bar-level families.
8. **Order-book features** (16 pp) — The imbalance family at one and many levels, order-flow imbalance, microprice, depth shape, queue depletion, cancellation rates.
9. **Trade-flow features** (14 pp) — Trade signing, sign autocorrelation, flow-toxicity measures, fitted excitation intensities, large-trade detection.
10. **Cross-sectional and cross-asset features** (12 pp) — Peer and sector residuals, lead-lag networks, futures-to-cash, rates-to-equities, cross-venue returns.
11. **Fundamental, analyst and event features** (12 pp) — Accounting ratios done point-in-time, revisions, surprises, event calendars.
12. **Alternative and text data** (14 pp) — Transactions, web, geolocation, satellite, filings, news; vendor evaluation and the buy decision.
13. **Half-life, decay and stability** (10 pp) — Measuring how fast a predictor dies across horizon and across years.

**Part III — From predictors to forecasts**

14. **Signal combination** (14 pp) — Linear blends, regularised regression, information-coefficient weighting, stacking, orthogonalisation.
15. **From signal to forecast** (12 pp) — Calibration, scaling a score into expected return, the fundamental law and its limits.

**Part IV — Backtesting at four levels**

16. **Vectorised backtests** (12 pp) — Fast and approximate; where they are right and the lies they tell.
17. **Event-driven backtests** (14 pp) — Orders, fills and a clock; bar-level fill assumptions.
18. **Order-book replay simulation** (16 pp) — Queue-position models, latency models, fill logic, the missing market impact and how to bound it.
19. **Simulation versus live** (12 pp) — Reconciling fills and P&L, locating the divergence, keeping the simulator honest.
20. **Overfitting** (14 pp) — Selection bias under multiple trials, deflated performance, probability of backtest overfitting, purged and embargoed validation.
21. **Live experiments** (10 pp) — Paper trading, canaries, randomised A/B tests on live flow, sizing the experiment.

**Part V — Measurement, risk and portfolios**

22. **Performance measurement** (14 pp) — The Sharpe ratio and its standard error, drawdown statistics, turnover, hit rate, skew of outcomes.
23. **Measuring market making and execution** (14 pp) — Markout curves, fill rates, hit ratios, P&L split into spread capture, adverse selection and inventory.
24. **Risk models** (16 pp) — Fundamental, statistical and hybrid factor models, specific risk, building one from scratch. Build: an equity risk model.
25. **Portfolio construction I** (14 pp) — Mean-variance with realistic constraints, neutrality, turnover control.
26. **Portfolio construction II** (14 pp) — Robust optimisation, views blended with equilibrium, risk parity, multi-period optimisation with costs.
27. **Transaction costs in research** (12 pp) — Cost models inside the optimiser, netting across strategies, cost-aware signals.
28. **Capacity, decay and crowding** (12 pp) — Capacity curves, alpha decay in production, detecting crowding, August 2007 as the case.
29. **Build: a research workflow** (10 pp) — From raw data to a reviewed, reproducible result.

---

## One Quant Book 8 — Strategies I: Equities and Futures (written: 330 pp, 118 strategy files; outline estimate was ~388)

**Part I — Equity statistical arbitrage**

1. **Anatomy of a stat-arb book** (12 pp) — Thousands of small bets, neutrality, financing, how the public descriptions of such books fit together.
2. **Short-term reversal** (12 pp) — Liquidity provision at daily and intraday horizons. [4]
3. **Residual and principal-component stat arb** (14 pp) — Trading mean reversion of factor residuals. [4]
4. **Pairs and baskets** (12 pp) — Distance, cointegration and copula selection; why pairs died and what replaced them. [4]
5. **Momentum** (12 pp) — Cross-sectional, residual, industry and intraday momentum; crashes. [5]
6. **Value, quality and low risk** (14 pp) — The factor-investing canon and its implementation details. [6]
7. **Earnings** (14 pp) — Post-announcement drift, revisions, guidance, the announcement-day options angle. [5]
8. **Short interest, borrow and crowding** (12 pp) — Lending data as signal and as risk. [4]
9. **Flows** (12 pp) — ETF, index-fund, mutual-fund and quarterly-holdings flows. [4]
10. **Index rebalancing** (14 pp) — Predicting additions and deletions, trading the event, how the trade has decayed. [4]
11. **Merger arbitrage** (14 pp) — Deal spreads, break risk, collars, regulatory risk. [4]
12. **Share classes, holding companies, closed-end funds, blank-cheque companies** (12 pp) — Structural relative value. [5]
13. **Intraday patterns** (14 pp) — Overnight versus intraday returns, the volume smile, end-of-day hedging flows, close imbalances. [5]
14. **Intraday machine-learned alphas** (16 pp) — The minutes-to-hours horizon built on order-book features: targets, models, execution coupling. [4]
15. **Options-implied signals for stocks** (12 pp) — Skew, volatility spreads, option volume. [4]
16. **Alternative-data strategies** (12 pp) — From dataset to position; what has been documented to work. [4]
17. **News and events** (12 pp) — Machine-readable news, scheduled events, halts. [4]
18. **Asia-specific equity strategies** (10 pp) — Price limits, retail dominance, connect flows. [3]

**Part II — Futures and systematic macro**

19. **Trend following** (16 pp) — Signal families, portfolio of trends, volatility scaling, the long record. [6]
20. **Carry across asset classes** (14 pp) — Defining carry everywhere; carry crashes. [5]
21. **Calendar spreads and curve trades** (12 pp) — Trading the shape of a futures curve. [4]
22. **Cross-asset lead-lag** (12 pp) — Intermarket signals at daily and intraday horizons. [4]
23. **Seasonality and calendar effects** (10 pp) — What survives out of sample. [4]
24. **Positioning and sentiment** (10 pp) — Positioning reports, surveys, options positioning. [3]
25. **Short-term futures strategies** (12 pp) — Intraday mean reversion and momentum, opening ranges, the announcement drift. [5]
26. **Volatility targeting and risk-managed portfolios** (10 pp) — The mechanics and the footprint of the whole industry doing it. [3]
27. **Crypto medium-frequency strategies** (14 pp) — Funding and basis carry, cross-sectional momentum, on-chain data signals. [6]

**Part III — Running it**

28. **Running a multi-strategy book** (14 pp) — Allocation across strategies, netting, shared risk, turning strategies off.
29. **The asset manager's strategies** (14 pp) — Indexing, factor products, benchmark-relative management, transition management.

---

## One Quant Book 9 — Strategies II: Volatility, Relative Value, Macro and the Bank Desks (written: 333 pp, 118 strategy files; outline estimate was ~382)

**Part I — Volatility and convertibles**

1. **Harvesting the variance risk premium** (14 pp) — Short-volatility implementations and their blow-ups. [5]
2. **Dispersion and correlation** (14 pp) — Index against constituents; implied-correlation trading. [4]
3. **Skew and term-structure relative value** (12 pp) — Across strikes, expiries and related underlyings. [4]
4. **Gamma scalping and event volatility** (12 pp) — Trading realised against implied around events. [4]
5. **The volatility-index complex** (12 pp) — Roll-down, futures-versus-options, exchange-traded volatility products. [4]
6. **Zero-day options and dealer-gamma flows** (10 pp) — Estimating dealer positioning and trading its hedging. [3]
7. **Tail hedging and long volatility** (10 pp) — Convex programmes, their cost, how they are funded. [3]
8. **Convertible arbitrage** (14 pp) — Delta, gamma, credit and borrow in one trade; 2005 and 2008. [4]
9. **Capital-structure arbitrage** (10 pp) — Equity against credit of one issuer. [3]

**Part II — Rates and FX**

10. **Government-bond relative value** (14 pp) — Butterflies, curve trades, fitted-curve rich-cheap. [5]
11. **The bond-futures basis trade** (12 pp) — Mechanics, leverage, March 2020. [3]
12. **Swap-spread and asset-swap trades** (12 pp) — Balance-sheet-driven dislocations. [4]
13. **Supply trades** (10 pp) — Auction concessions, new-issue and on-the-run premia. [4]
14. **Cross-currency basis and FX carry** (14 pp) — Carry construction, crash risk, funding-driven basis trades. [5]
15. **FX flow strategies** (10 pp) — Fixing and month-end flows, central-bank behaviour. [4]
16. **Systematic macro** (14 pp) — Value, momentum, carry and macro-data signals across countries. [5]
17. **Discretionary macro** (12 pp) — How a portfolio manager expresses a view: instrument choice, convexity, stop discipline.

**Part III — Credit and mortgages**

18. **Credit relative value** (14 pp) — Bond-versus-default-swap basis, index arbitrage, curve trades. [5]
19. **Systematic credit and bond-ETF arbitrage** (12 pp) — Factor credit, ETF create-redeem, portfolio-trade pricing. [4]
20. **Mortgage and structured-credit strategies** (10 pp) — Prepayment views, tranche relative value. [3]

**Part IV — Commodities and energy**

21. **Commodity spreads** (14 pp) — Calendar, quality, location, crack, spark and crush spreads. [6]
22. **Storage, transport and physical optionality** (12 pp) — What an asset-backed trader owns and how it is monetised. [4]
23. **Power and gas trading** (14 pp) — Day-ahead versus intraday, weather-driven positions, battery and flexible-asset optimisation. [5]

**Part V — The bank desks**

24. **Flow market making at a bank** (14 pp) — Axes, client tiering, skewing, internalisation, the franchise P&L. [4]
25. **The central risk book** (12 pp) — Pooling and netting desk risk, internal crossing, optimised hedging. [3]
26. **Delta-one and dividends** (12 pp) — Index arbitrage at a bank, financing trades, dividend risk from structured issuance. [4]
27. **Quantitative investment strategies** (14 pp) — Rules-based indices sold as products: design, wrappers, fees, hedging. [4]
28. **Hedging a structured-products book** (14 pp) — The autocallable book's vega, dividend, correlation and skew exposures and the recycling trades they create. [4]

**Part VI — What you must not do**

29. **Manipulative strategies and how they are caught** (14 pp) — Spoofing, layering, momentum ignition, wash trades, marking the close, benchmark manipulation, sandwiching and its legal status; each with its enforcement case and the surveillance detector. [8]

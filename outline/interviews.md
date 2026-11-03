# The interview books: chapters

`tools/check_interview_book.py` reads these tables. The file name carries the number here; a printed chapter number
follows `part.tex`. A count of 0 is a chapter of text with no questions. A book may stop short of its pages rather than
pad, but counts here are targets the gate enforces at closing: to change one, ask the main session.

## interviews-1

One Quant Book 18, Interviews I: Maths, Probability and Speed. About 400 pp. Parts: Speed (1-6), Probability and Riddles
(7-16), Statistics and Mathematics (17-23), Timed Tests (24-33).

| No. | Slug | Questions | Brief |
|---|---|---|---|
| 1 | how-to-train | 0 | Text, about 6 pp: what interviews test by role and type of firm, the stages and formats reported (online tests, phone screens, final rounds), how to train with these three books. Facts through the ledger, no firm named |
| 2 | mental-technique | 40 | Questions on technique, not drills: multiplying near round numbers, fractions and percentages, compounding, logs by hand, square roots, rule of 72, checking by last digit, estimating products |
| 3 | speed-drills | 12 | CALIBRATE. 12 generated sheets, from easy to hard. PILOT holds sheet 1 |
| 4 | sequences-patterns-and-aptitude | 30 | Next number in a sequence, interleaved rules, matrix and pattern logic stated in words, verbal logic, quick numerical reasoning, as in first-round tests |
| 5 | estimation | 25 | Fermi estimates with intervals, sanity checks, market sizing, estimates about markets and systems |
| 6 | number-riddles | 25 | Clock hands, trailing zeros, remainders, last digits, divisibility, coins and Frobenius, digit puzzles |
| 7 | counting-and-symmetry | 40 | Arrangements, multisets, inclusion-exclusion, reflection and ballot, symmetry arguments that avoid counting |
| 8 | conditional-probability-and-bayes | 40 | Conditioning traps, Bayes by odds, protocols of information, sequential updates, posterior betting |
| 9 | expectation-and-indicators | 25 | PILOT, written |
| 10 | waiting-times-and-markov-chains | 25 | PILOT, written |
| 11 | random-walks-and-martingales | 25 | Gambler's ruin with and without drift, optional stopping, reflection, ballot, Wald's identity, last and maximum visits |
| 12 | continuous-and-geometric-probability | 25 | Regions on the square and cube, broken sticks, Buffon, uniform spacings, normal variables and their angles, densities |
| 13 | order-statistics | 15 | Maximum and median of samples, spacings, German tank, second-highest values, records |
| 14 | optimal-stopping | 20 | Secretary, dice with re-rolls, card stopping games, thresholds on uniform draws, value of information |
| 15 | games | 20 | Nim and Grundy values, backward induction, pirates, mixed strategies, poker toy games, auctions |
| 16 | logic-riddles | 35 | Weighings, hats, poison and binary coding, burning ropes, pills, parity and invariants, chessboards |
| 17 | statistics | 40 | Tests, intervals and power, estimators (MLE, method of moments), multiple testing, bootstrap, Sharpe inference, normality |
| 18 | regression | 30 | PILOT, written |
| 19 | linear-algebra | 25 | Rank, eigenvalues of structured matrices, equicorrelation, PSD, PCA and SVD, conditioning, sample covariance |
| 20 | calculus-and-optimisation | 20 | Integrals by symmetry, Lagrange, convexity, gradient steps, Newton, Stirling, floating-point numerics |
| 21 | machine-learning | 45 | Bias and variance, trees and boosting, cross-validation on time series, leakage, regularisation, neural nets, metrics, financial data |
| 22 | stochastic-calculus | 30 | Brownian motion, Ito, martingales, Girsanov, hitting times, integrated Brownian motion, Feynman-Kac |
| 23 | time-series | 20 | Stationarity, AR and MA, GARCH, volatility estimators, cointegration, forecasting evaluation |
| 24 | timed-test-1 | 12 | PILOT, written. Section A: 6 questions, 40 minutes. Section B: 6 questions, 60 minutes. Mixed, numeric answers |
| 25 | timed-test-2 | 12 | As timed test 1: new questions, about 3 in 4 probability, the rest quant |
| 26 | timed-test-3 | 12 | As timed test 2 |
| 27 | timed-test-4 | 12 | As timed test 2 |
| 28 | timed-test-5 | 12 | As timed test 2 |
| 29 | timed-test-6 | 12 | As timed test 2 |
| 30 | timed-test-7 | 12 | As timed test 2 |
| 31 | timed-test-8 | 12 | As timed test 2 |
| 32 | timed-test-9 | 12 | As timed test 2 |
| 33 | timed-test-10 | 12 | As timed test 2 |

## interviews-2

One Quant Book 19, Interviews II: Markets, Trading Games and the Final Round. About 400 pp. Parts: Trading Games (1-4),
Markets (5-18), The Final Round (19-21).

| No. | Slug | Questions | Brief |
|---|---|---|---|
| 1 | betting-and-kelly | 35 | Pricing a bet, Kelly and fractions of it, ruin under Kelly, sizing with an edge you estimate, bets with limits, target-based betting |
| 2 | making-a-market | 35 | Making a market on dice, cards and unknown quantities, widths and skews, updating quotes after a trade, adverse selection, position limits |
| 3 | played-games | 12 | 12 played games. PILOT holds 2 |
| 4 | options-and-bond-arithmetic-at-speed | 25 | Quick estimates: at-the-money option value and Greeks without a calculator, parity by hand, DV01, yield and price moves, carry, ETF fair value and spread arithmetic |
| 5 | markets-and-microstructure | 50 | Order books, spreads, impact, execution including TWAP, VWAP and optimal liquidation, adverse selection, short selling, market structure |
| 6 | etfs-futures-and-index-arbitrage | 35 | Creation and redemption, basket fair value, leveraged ETFs, cash and carry, dividends, index rebalances, roll |
| 7 | options-parity-and-greeks | 50 | Payoffs, parity, no-arbitrage bounds, spreads, Greeks and their signs, delta hedging, gamma and theta, early exercise |
| 8 | pricing-and-numerics | 50 | Black-Scholes derivations, digitals, barriers, Asians, baskets, Monte Carlo, trees, PDEs, American pricing |
| 9 | vol-surface-and-vol-trading | 40 | Implied and realised, smile dynamics, local and stochastic vol, variance swaps, dispersion, event vol |
| 10 | rates-and-fx | 50 | Curves, duration and convexity, DV01 hedging, swaps, futures, short-rate models, swaptions, FX forwards, FX options |
| 11 | credit-and-xva | 20 | Hazard rates, CDS, default correlation, CVA, FVA, wrong-way risk |
| 12 | commodities-and-energy | 20 | Contango and backwardation, storage and convenience yield, spreads such as crack and calendar, seasonality, power, physical against financial |
| 13 | risk-validation-and-regulation | 40 | VaR, expected shortfall, backtests, stress tests, factor risk, model validation, capital rules |
| 14 | crypto-for-traders-and-researchers | 30 | Perpetuals and funding, basis, inverse contracts, liquidation, AMM mathematics, arbitrage across venues, stablecoins |
| 15 | portfolio-construction | 25 | Minimum variance and mean-variance by hand, constraints, risk parity, factor models, fundamental law, shrinkage, turnover |
| 16 | macro-market-knowledge-and-pitches | 25 | How rates, inflation and growth move assets, what an event does to prices, how to keep up with levels, a stock or trade pitch. Levels and volatile facts in `dated` boxes |
| 17 | valuation-and-financial-statements | 25 | CALIBRATE. For fundamental analysts: three statements and how they link, DCF, WACC, multiples, earnings quality, a quick model, a position under questioning |
| 18 | research-and-strategy-cases | 40 | Signal design, backtest critique, costs, capacity, sizing, ramp-up, live against simulated, take-home data cases, business cases such as sizing a venture or a desk |
| 19 | behavioural-and-fit | 30 | CALIBRATE. Motivation, mistakes, conflict, pressure, risk appetite, questions to ask |
| 20 | your-strategy-and-your-project | 20 | Walking through your own work, market views, ideas under questioning, defending results |
| 21 | mock-interviews | 10 | CALIBRATE one. One written mock interview per role and one more, with commentary |

## interviews-3

One Quant Book 20, Interviews III: Code. About 400 pp. One part per family if it reads better, or one part.

| No. | Slug | Questions | Brief |
|---|---|---|---|
| 1 | algorithms | 80 | CALIBRATE the first 20. The recurring families, with order-book and streaming variants, in Python or C++ as fits; complexity stated |
| 2 | python-and-pandas | 40 | Language traps, performance, data handling, pandas, numpy, testing |
| 3 | cpp | 60 | Lifetime, move semantics, templates, undefined behaviour, the standard library, implementing vector, smart pointers, allocators |
| 4 | low-latency | 35 | PILOT, written |
| 5 | operating-systems-concurrency-and-networks | 40 | Threads, scheduling, virtual memory, locks, TCP and UDP, multicast, the socket path |
| 6 | system-design | 40 | Matching engine, feed handler, risk checks, tick store, market-data service, order router, research platform |
| 7 | sql-and-data | 25 | CALIBRATE. Joins, windows, as-of joins, data quality; run on SQLite or DuckDB |
| 8 | smart-contracts-and-crypto-engineering | 30 | What a trading engineer at a crypto firm should know: EVM basics, reentrancy, oracles, MEV, exchange design. Solidity printed from tested files where possible, or stated in the answer's prose with a ledger |
| 9 | reading-debugging-and-software-design | 40 | CALIBRATE. What does this code do, find the bug, memory leaks, races, object-oriented design, interfaces, testing, Java and C# as banks use them only where a stem asks |

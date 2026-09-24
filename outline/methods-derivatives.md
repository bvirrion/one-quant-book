# Books 4–6 — Methods, Derivatives, Risk

Pages are all-in (chapter + its share of solutions). Each book adds ~20 pages
of front and back matter.

---

## One Quant Book 4 — Quantitative Methods (written: 351 pp; outline estimate was ~406)

Assumes a master's-level mathematical culture: fast, rigorous, and aimed at use.

**Part I — Stochastic calculus**

1. **Probability at speed** (12 pp) — Conditional expectation, filtrations, martingales, stopping times, change of measure; fixes the notation of the whole series.
2. **Brownian motion** (12 pp) — Construction, path properties, reflection principle, hitting times, quadratic variation.
3. **Itô calculus** (14 pp) — The integral, Itô's formula in one and several dimensions, local martingales, the representation theorem.
4. **Stochastic differential equations** (14 pp) — Existence and uniqueness, the workhorse diffusions (geometric, mean-reverting, square-root), generators, Kolmogorov equations, Feynman–Kac.
5. **Girsanov and changes of numeraire** (12 pp) — Measure changes as a computational tool; forward and annuity measures.
6. **Jump processes** (14 pp) — Poisson and compound Poisson processes, Itô's formula with jumps, Lévy processes and the Lévy–Khintchine formula.
7. **Point processes and Hawkes processes** (14 pp) — Intensities and compensators, self- and mutual excitation, branching ratio, likelihood estimation, simulation by thinning.
8. **Markov chains and queues** (12 pp) — Continuous-time chains, birth-death processes, queueing models sized for order books, hitting probabilities.
9. **Stochastic control** (14 pp) — Dynamic programming, the Hamilton–Jacobi–Bellman equation, verification, Merton's problem, a sketch of viscosity solutions.
10. **Optimal stopping and impulse control** (12 pp) — Free boundaries, variational inequalities, when to act and when to wait.

**Part II — Statistics**

11. **Estimation** (14 pp) — Maximum likelihood, M-estimators, method of moments, asymptotics, the delta method, sandwich variances.
12. **Testing and multiple testing** (14 pp) — Power, the garden of forking paths, family-wise error and false-discovery control, reality-check tests for strategy search.
13. **Resampling** (12 pp) — Bootstrap, block bootstrap for dependent data, permutation tests, jackknife.
14. **Bayesian methods** (14 pp) — Conjugacy, shrinkage, hierarchical models, empirical Bayes, Markov-chain Monte Carlo.
15. **Robust statistics and heavy tails** (14 pp) — Robust losses, winsorising, rank methods, extreme-value theory, tail-index estimation.
16. **Linear models under stress** (14 pp) — Geometry of least squares, collinearity, ridge, lasso, elastic net, weighted and errors-in-variables regression, cross-sectional regressions over time, panels.

**Part III — Time series**

17. **Linear time series** (14 pp) — Autoregressive and moving-average models, spectral view, stationarity, unit roots, long memory.
18. **Volatility models** (14 pp) — The conditional-heteroskedasticity family, realised volatility, heterogeneous autoregressive models, forecasting and evaluation.
19. **State-space models and the Kalman filter** (14 pp) — Filter, smoother, expectation-maximisation, particle filters; a time-varying hedge ratio as the running example.
20. **Multivariate series and cointegration** (12 pp) — Vector autoregressions, error-correction form, rank tests, causality in the predictive sense.
21. **High-frequency econometrics** (12 pp) — Microstructure noise, asynchronous observation, the vanishing of correlation at short scales, robust covariance estimators, signature plots.

**Part IV — High dimension and optimisation**

22. **Covariance estimation and random matrices** (14 pp) — The eigenvalue law of pure noise, linear and nonlinear shrinkage, eigenvalue clipping, factor-structured covariances.
23. **Convex optimisation** (14 pp) — Duality, optimality conditions, quadratic and second-order cone programmes, what solvers actually do.
24. **Numerical optimisation in practice** (12 pp) — First- and second-order methods, operator splitting, stochastic gradients, non-convex calibration problems and their traps.

**Part V — Numerical methods**

25. **Floating point and numerical linear algebra** (14 pp) — Representation, cancellation, conditioning, factorizations, iterative solvers; the bugs that cost money.
26. **Monte Carlo** (14 pp) — Generators, variance reduction, importance sampling, low-discrepancy sequences, multilevel methods, discretisation schemes.
27. **Finite-difference methods** (14 pp) — Explicit, implicit and theta schemes, alternating directions, boundaries, stability and oscillations.
28. **Transforms, interpolation and algorithmic differentiation** (14 pp) — Fast Fourier and cosine-series methods, splines, root finding, forward and adjoint differentiation.
29. **Games, auctions and information** (12 pp) — Equilibrium, Bayesian games, auction formats and revenue, entropy and its link to optimal betting.

---

## One Quant Book 5 — Derivatives and Volatility (written: 348 pp; outline estimate was ~386)

**Part I — Foundations**

1. **No arbitrage and the fundamental theorems** (12 pp) — Replication, state prices, equivalent martingale measures, completeness.
2. **The binomial model** (10 pp) — Replication in discrete time, convergence, a first pricer.
3. **Black–Scholes three ways** (14 pp) — Replication and the pricing equation, the martingale route, the binomial limit; what each derivation teaches.
4. **Greeks and the hedging P&L** (14 pp) — The gamma-theta identity, discrete hedging error, break-even volatility, which volatility to hedge at.
5. **Dividends, borrow and forwards** (12 pp) — Discrete dividends, repo rates, implying forwards and borrow from put-call parity.
6. **American options and early exercise** (12 pp) — Exercise boundaries, dividends and rates as triggers, the practical exercise decision.

**Part II — The volatility surface**

7. **Implied volatility and its surface** (14 pp) — Smile phenomenology by asset class, sticky-strike and sticky-delta regimes, static no-arbitrage conditions.
8. **Parametrising the surface** (14 pp) — Stochastic-volatility-inspired parametrisations, spline approaches, fitting to bid and ask, event volatility, business time versus calendar time.
9. **Local volatility** (14 pp) — Dupire's formula, calibration in practice, the forward-smile problem.
10. **Stochastic volatility** (14 pp) — The Heston model, characteristic functions, calibration, what the parameters mean to a trader.
11. **SABR and smile dynamics** (12 pp) — The asymptotic formula, backbone, hedging under a smile model.
12. **Rough volatility and forward-variance models** (12 pp) — Forward-variance curves, rough fractional models, path-dependent volatility, joint calibration to index and volatility-index options.
13. **Jumps and Lévy models** (10 pp) — Jump-diffusions, short-dated smiles, when jumps matter.
14. **Variance swaps and volatility derivatives** (14 pp) — Replication by a strip of options, the volatility-index formula, its futures and options, convexity.

**Part III — Exotics and products**

15. **Barriers and digitals** (14 pp) — Reflection, static hedging, barrier shifts, gap risk at the barrier.
16. **Asians, lookbacks, cliquets and forward-starts** (12 pp) — Path dependence and forward-smile sensitivity.
17. **Multi-asset options** (14 pp) — Correlation, baskets, worst-of payoffs, local correlation, correlation skew, quanto and composite adjustments.
18. **Autocallables** (16 pp) — Payoff anatomy, pricing, the risk profile (vega, dividends, correlation, skew), issuer hedging flows and their documented market impact.
19. **The structured-products business** (12 pp) — Wrappers, distribution, margins, issuer funding, product lifecycle; systematic-strategy indices and options on them.
20. **FX derivatives** (14 pp) — The pricing conventions, the vanna-volga method, barriers and target-redemption forwards, stochastic-local volatility.
21. **Convertibles and the credit-equity link** (12 pp) — Convertible bonds, equity-to-credit models, what a convertible desk hedges.

**Part IV — Numerical pricing**

22. **Trees and finite-difference pricers in practice** (12 pp) — Grids, discrete dividends, barriers, Americans; accuracy against speed.
23. **Monte Carlo pricers in practice** (14 pp) — Regression-based early exercise, pathwise, likelihood-ratio and adjoint Greeks, bridges.
24. **Fourier pricing and calibration engineering** (12 pp) — Transform pricers, calibration as an optimisation pipeline, stability day to day.

**Part V — On the desk**

25. **Trading volatility** (14 pp) — Gamma scalping, carry, skew and term trades, attribution of a volatility book's P&L.
26. **Options market making in practice** (16 pp) — Fitting a live surface, quote widths, delta-hedging policies, pin risk, dividend and early-exercise plays, bucketed limits.
27. **Managing an exotic book** (12 pp) — Reserves, parameter bid-offer, model risk, stress, day-one P&L.
28. **Build: a pricing library** (14 pp) — Instruments, models and engines as separate concepts; market-data objects; testing a pricer.

---

## One Quant Book 6 — Rates, Credit, XVA and Risk (written: 314 pp; outline estimate was ~372)

**Part I — Rates modelling**

1. **Curve construction** (14 pp) — Instrument selection, bootstrapping, interpolation choices and their hedging consequences.
2. **Multi-curve and collateral discounting** (14 pp) — Discounting at the collateral rate, the collateral agreement, cheapest-to-deliver collateral, life after interbank rates.
3. **Rates risk** (12 pp) — Bucketed sensitivities, principal components of the curve, hedging a swap book.
4. **Vanilla rates options** (12 pp) — Lognormal and normal models, caps, floors and swaptions, normal volatilities.
5. **SABR in rates and the volatility cube** (12 pp) — Building and interpolating the cube; negative rates and shifted models.
6. **Convexity adjustments and constant-maturity products** (12 pp) — Replication by swaptions, timing and quanto adjustments.
7. **Short-rate models** (14 pp) — One- and two-factor Gaussian models, calibration, trees.
8. **Forward-rate and market models** (14 pp) — The forward-rate framework, the market model, drift, calibration to swaptions.
9. **Bermudans and callables** (12 pp) — Exercise strategies, regression methods, the callable-bond issuance business.
10. **Modelling overnight-rate products** (10 pp) — Backward-looking compounding, low-dimensional Markov models.
11. **Inflation derivatives** (10 pp) — Foreign-currency analogy, year-on-year versus zero-coupon, seasonality.
12. **Mortgage modelling** (10 pp) — Prepayment models, option-adjusted spread, hedging negative convexity.

**Part II — Credit and commodities modelling**

13. **Reduced-form credit** (14 pp) — Hazard rates, default-swap pricing, curve bootstrapping, the standard model.
14. **Structural credit models** (10 pp) — Equity as an option on the firm, distance to default, capital-structure signals.
15. **Portfolio credit** (14 pp) — Copulas, base correlation, tranches; the 2005 correlation dislocation and 2008.
16. **Commodity and energy derivatives** (14 pp) — Factor models of the curve, spread options, swing contracts, storage valuation.

**Part III — Valuation adjustments**

17. **Counterparty exposure** (14 pp) — Expected and potential future exposure, netting, collateral, simulation engines, wrong-way risk.
18. **Credit and debit valuation adjustments** (12 pp) — Definitions, computation, sensitivities, accounting.
19. **Funding, margin and capital adjustments** (12 pp) — The funding debate, initial-margin cost, capital cost.
20. **The valuation-adjustment desk** (10 pp) — What it hedges, how it charges, how it is organised.

**Part IV — Risk**

21. **Market-risk measures** (14 pp) — Value at risk three ways, expected shortfall, backtesting the measure.
22. **Stress testing and scenarios** (10 pp) — Historical, hypothetical and reverse stress tests.
23. **Regulatory capital for trading books** (14 pp) — Standardised and internal-model approaches, the P&L-attribution test, non-modellable risk factors.
24. **Liquidity and funding risk; bank treasury** (12 pp) — Liquidity ratios, funds-transfer pricing, asset-liability management, rate risk in the banking book, the 2023 regional-bank failures.
25. **Margin models** (10 pp) — The standard bilateral initial-margin model, clearing-house models, procyclicality.
26. **Model risk and validation** (12 pp) — Supervisory expectations, the validation report, model inventories, benchmarking.
27. **P&L explain and independent price verification** (12 pp) — Attribution, unexplained P&L, valuation control, reserves, prudent valuation.
28. **Operational risk and rogue trading** (10 pp) — The documented rogue-trader cases and the control failures behind each.
29. **Build: a risk engine** (12 pp) — Scenario generation, revaluation, aggregation; run on the Book 5 pricing library.

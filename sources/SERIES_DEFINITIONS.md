# Series definition map (One Quant Books 1–13)

Regenerated 2026-09-26 after the Books 10–13 batch, from the `\index{}` harvest of
all thirteen written books (first written 2026-09-24 for Books 1–6) (multi-line aware; the same harvest as `tools/gates.sh book`). **A term
is defined once in the series**: the book and chapter below own it; every other
book uses it with a prose pointer ("One Quant Book 4, chapter 5"). Named results are not terms and are not listed.

## Rulings at the sync (2026-09-24)

| term | owner | not | reason |
|---|---|---|---|
| equivalent martingale measure | B4 ch. 5 | B5 ch. 1 | mathematics, read first; B5 keeps arbitrage, FTAP, self-financing strategy, complete market, replicating portfolio, state price |
| risk-neutral measure | B4 ch. 5 | B5 ch. 1 | same |
| calibration | B4 ch. 24 | B5 ch. 8 | optimisation; tie to the lower book; B5 keeps its surface-specific terms, B6 keeps *curve calibration* |
| copula | B4 ch. 15 | B6 ch. 15 | the general notion (with Sklar's theorem); B6 keeps *Gaussian copula*, *Student-t copula*, *default correlation* |
| trinomial tree | B5 ch. 22 | B6 ch. 7 | settled in Phase A |
| valuation reserve | B5 ch. 27 | B6 ch. 27 | settled in Phase A |
| Samuelson effect | B3 ch. 10 | B6 | settled in Phase A |
| fractional Brownian motion, Hurst exponent | B4 ch. 17 | B5 ch. 12 | B5 uses them |
| Sharpe ratio | B4 ch. 11 | — | not defined in Books 1–2 (B2 ch. 29 uses it inline) |
| volatility cube | B2 ch. 13 | B6 | B6 defines *swaption matrix*, *shifted SABR*, *normal SABR* |
| Asian option / average-price option | B5 ch. 16 / B3 ch. 12 | — | two index terms, prose cross-reference both ways |

## Rulings at the Books 10–13 sync (2026-09-25)

Ownership rule: Books 1–9 keep their terms; otherwise Book 10 owns microstructure, impact, execution, TCA,
venue and protocol mechanisms as the market sees them (and the exchange simulator); Book 11 market-making
and HFT strategy terms and the risk-control policy; Book 12 machine-learning terms not in Books 4 or 7;
Book 13 software, systems and protocol engineering (Book 14, later, uses Book 13's hardware-facing terms).
Ties go to the lower book number. The losing book removes the `\emph{…}\index{…}` pair and uses the term,
in the owner's wording, with a prose pointer.

| term | owner | not | reason |
|---|---|---|---|
| limit order, market order, limit order book, price level, tick size, matching engine, order types (stop, IOC, FOK, GTC, hidden, iceberg, pegged, midpoint peg, time in force) | B10 ch. 1–2 | — | not defined in Books 1–9 (only ISO, MOC/LOC and post-only are); Books 11–13 use them |
| queue value, large-tick asset, small-tick asset, uncertainty-zone model | B10 ch. 6 | B11 ch. 5 | venue mechanics, lower book; B11 keeps the queue-reactive model and its join/leave terms |
| information share, component share | B10 ch. 8 | B11 ch. 8 | fragmentation measures, lower book; B10 defines both |
| frequent batch auction | B10 ch. 10 | B11 ch. 9 | auction design; B11 keeps latency arbitrage, latency race, stale-quote sniping, speed bump, asymmetric speed bump |
| parent order, child order | B10 ch. 14 | — | not in Books 1–9 |
| order management system, execution management system | B10 ch. 20 | B13 ch. 21 | buy-side desk tools; B13 keeps order gateway, order state machine, drop copy |
| firm liquidity, liquidity aggregator | B10 ch. 21 | B11 ch. 21 | lower book |
| high-frequency trading, algorithmic trading, order-to-trade ratio | B10 ch. 24 | B11 ch. 1, 10 | legal definitions in the market-quality chapter, read first; B11 ch. 1 describes the business with a pointer |
| order-entry protocol, order-entry session, execution report, redundant feed lines, snapshot recovery, retransmission request, cancel on disconnect, self-trade prevention | B10 ch. 26 (or earlier in B10) | B13 ch. 15–21, B11 ch. 10 | the venue side; *self-match prevention* (B11) is the same concept: one string, *self-trade prevention*; B13 drops *binary order-entry protocol* |
| cancel-replace, message throttle | B11 ch. 10 | — | quoting-engine policy; B13 keeps *token bucket* (the algorithm) |
| mass quote | B11 ch. 19 | B10 ch. 26, B13 ch. 16 | options quoting mechanism; B10's protocol message uses it with a pointer |
| kill switch, pre-trade risk check, price collar, loss limit, market access rule | B11 ch. 27 | B13 ch. 22 | policy and regulation; B13 keeps mass cancel, risk gate, worst-case exposure, fail-closed design |
| win-probability model, cover price, auto-quoting | B11 ch. 22 | B10 ch. 23 | dealer pricing inputs; B10 keeps search, bargaining, how many dealers to ask |
| reinforcement-learning terms (MDP, policy, reward, Q-learning, policy gradient, actor–critic, bandits, off-policy evaluation, …) | B12 ch. 17–18 | B10 ch. 17–18, B11 | the batch file's assignment |
| recursive least squares, forgetting factor, hidden Markov model, regime-switching model, audit trail, shadow deployment | B12 | — | claimed by no other book |
| latency, tick-to-trade latency, wire-to-wire latency, latency budget, tail latency, jitter | B13 ch. 1 | — | systems terms; B7 keeps latency model and the two latencies |
| FIX protocol and session terms, line arbitration, message gap, incremental and snapshot channels, simple binary encoding, flyweight codec, multicast, hardware timestamp, kernel bypass, busy polling | B13 | Book 14 (later) | protocol and systems engineering, lower book |

## Map (2753 terms)

| term | book | chapter |
|---|---|---|
| 130/30 portfolio | 7 | 25-portfolio-construction-i |
| 13F holdings | 8 | 09-flows |
| 3-2-1 crack spread | 3 | 03-refined-products-and-cracks |
| A/B test | 7 | 21-live-experiments |
| ABA problem | 13 | 11-lock-free-programming |
| absorbing state | 4 | 08-markov-chains-and-queues |
| accelerator | 12 | 23-training-infrastructure |
| access fee cap | 1 | 09-us-equity-market-structure |
| accountability level | 3 | 13-getting-access-commodities-and-power |
| accounting ratio | 7 | 11-fundamental-analyst-and-event-features |
| accrued interest | 2 | 03-government-bonds |
| accumulated local effects | 12 | 21-interpretability-and-model-governance |
| accumulator | 5 | 20-fx-derivatives |
| acquire--release ordering | 13 | 11-lock-free-programming |
| action masking | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| action-value function | 12 | 17-reinforcement-learning-foundations |
| activation function | 12 | 07-neural-networks-for-noisy-tabular-data |
| active management | 1 | 03-the-buy-side |
| actor--critic method | 12 | 17-reinforcement-learning-foundations |
| Adam | 12 | 07-neural-networks-for-noisy-tabular-data |
| adapted process | 4 | 01-probability-at-speed |
| adaptive execution | 10 | 15-beyond-almgren-chriss |
| adaptive windowing | 12 | 12-online-learning-and-drift |
| additional tier 1 | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| additional valuation adjustment | 6 | 27-pnl-explain-and-independent-price-verification |
| adjoint mode | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| adjustment factor | 1 | 08-shares-corporate-actions-indices |
| admissible control | 4 | 09-stochastic-control |
| adversarial validation | 12 | 03-validation |
| adverse selection | 1 | 01-what-a-trading-firm-does |
| adverse-selection component | 10 | 05-decomposing-the-spread |
| adverse-selection cost | 7 | 23-measuring-market-making-and-execution |
| affine term-structure model | 6 | 07-short-rate-models |
| agency mortgage-backed security | 2 | 12-mortgages-and-agencies |
| agency portfolio trade | 10 | 22-portfolio-trades-and-risk-bids |
| agent | 1 | 01-what-a-trading-firm-does |
| agent-based model | 10 | 27-build-an-agent-based-market |
| aggregate impact | 10 | 11-the-empirics-of-price-impact |
| aggregational Gaussianity | 7 | 05-stylised-facts-of-returns |
| aggressive-in-the-money strategy | 10 | 15-beyond-almgren-chriss |
| aim portfolio | 7 | 26-portfolio-construction-ii |
| aleatoric uncertainty | 12 | 11-probabilistic-models-and-uncertainty |
| algo wheel | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| algorithmic differentiation | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| algorithmic stablecoin | 3 | 23-defi-credit-and-leverage |
| algorithmic trading | 10 | 24-market-quality-and-regulation |
| all-reduce | 12 | 23-training-infrastructure |
| all-to-all trading | 2 | 22-how-bonds-trade |
| allowance surrender | 3 | 07-emissions-and-environmental-markets |
| Almgren--Chriss model | 10 | 14-the-almgren-chriss-framework |
| alpha | 1 | 01-what-a-trading-firm-does |
| alpha contamination | 10 | 11-the-empirics-of-price-impact |
| alpha scaling rule | 7 | 15-from-signal-to-forecast |
| alternating direction implicit method | 4 | 27-finite-difference-methods |
| alternating direction method of multipliers | 4 | 24-numerical-optimisation-in-practice |
| alternative data | 7 | 12-alternative-and-text-data |
| alternative trading system | 1 | 04-exchanges-brokers-venues |
| alternative-data strategy | 8 | 16-alternative-data-strategies |
| American exercise | 1 | 23-option-contracts-and-exchanges |
| Amihud illiquidity | 7 | 07-price-and-volume-features |
| analyst revision | 7 | 11-fundamental-analyst-and-event-features |
| ancillary activity exemption | 3 | 13-getting-access-commodities-and-power |
| ancillary service | 3 | 05-power-markets-design |
| announcement premium | 8 | 07-earnings |
| announcement window | 7 | 11-fundamental-analyst-and-event-features |
| annualisation | 7 | 22-performance-measurement |
| annuity | 2 | 09-interest-rate-swaps |
| annuity measure | 4 | 05-girsanov-and-changes-of-numeraire |
| anomaly detection | 12 | 20-clustering-regimes-and-anomaly-detection |
| anonymisation test | 12 | 14-large-language-models-in-finance |
| anti-gaming logic | 10 | 18-smart-order-routing |
| anti-procyclicality tool | 6 | 25-margin-models |
| antithetic variates | 4 | 26-monte-carlo |
| API gravity | 3 | 02-crude-oil |
| API key | 3 | 15-centralised-exchanges |
| app-chain | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| arbitrage | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| arbitrage window | 3 | 03-refined-products-and-cracks |
| ARCH model | 4 | 18-volatility-models |
| archive node | 3 | 26-crypto-data-and-infrastructure |
| arena allocator | 13 | 06-cpp-for-latency-i-memory |
| ARMA process | 4 | 17-linear-time-series |
| arrival price | 7 | 19-simulation-versus-live |
| Arrow--Debreu security | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| as-of join | 7 | 03-point-in-time-data-and-the-biases |
| Asian option | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| assessment window | 3 | 01-physical-commodity-markets |
| asset manager | 1 | 01-what-a-trading-firm-does |
| asset--liability management | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| asset-backed trading | 9 | 22-storage-transport-and-physical-optionality |
| asset-swap spread | 2 | 21-corporate-bonds |
| assets under management | 1 | 01-what-a-trading-firm-does |
| assignment | 1 | 23-option-contracts-and-exchanges |
| asymmetric speed bump | 11 | 09-latency-arbitrage-and-its-defence |
| async runtime | 13 | 09-rust-for-low-latency |
| at-the-money | 1 | 25-volatility-first-contact |
| atomic arbitrage | 11 | 25-on-chain-trading |
| atomic operation | 13 | 11-lock-free-programming |
| attachment point | 2 | 24-credit-indices-and-tranches |
| attention mechanism | 12 | 08-sequence-models-on-order-books |
| attenuation bias | 4 | 16-linear-models-under-stress |
| auction collar | 10 | 10-auction-mechanics-and-theory |
| auction concession | 9 | 13-supply-trades |
| auction cut-off time | 10 | 10-auction-mechanics-and-theory |
| auction final price | 2 | 23-credit-default-swaps |
| auction impact curve | 11 | 16-auctions-and-the-close |
| auction tail | 2 | 04-the-treasury-market |
| audit trail | 12 | 25-experiment-tracking-and-reproducibility |
| authorised participant | 1 | 14-exchange-traded-funds |
| auto-deleveraging | 3 | 18-margin-liquidation-and-loss-allocation |
| auto-quoting | 11 | 22-bond-and-etf-request-for-quote-market-making |
| auto-vectorisation | 13 | 14-vector-instructions-and-data-parallel-code |
| autocall trigger | 5 | 18-autocallables |
| autocallable | 5 | 18-autocallables |
| autocorrelation function | 4 | 17-linear-time-series |
| autocorrelation-adjusted Sharpe ratio | 7 | 22-performance-measurement |
| autocovariance function | 4 | 17-linear-time-series |
| autoencoder | 12 | 09-cross-sectional-deep-models |
| automated market maker | 3 | 20-automated-market-makers |
| autoregressive process | 4 | 17-linear-time-series |
| Avellaneda--Stoikov model | 11 | 03-inventory-models |
| average cost | 1 | 07-pnl-and-positions |
| average uniqueness | 12 | 02-targets-labels-and-sample-weights |
| average-price option | 3 | 12-commodity-options-and-structured-hedges |
| axe | 2 | 22-how-bonds-trade |
| axe-driven skew | 9 | 24-flow-market-making-at-a-bank |
| Bachelier model | 2 | 13-the-rates-options-market |
| back bet | 3 | 27-prediction-and-betting-markets |
| back-adjustment | 7 | 02-market-data-for-research |
| back-pressure | 13 | 12-queues-ring-buffers-and-shared-memory |
| back-running | 3 | 22-maximal-extractable-value |
| backbone | 5 | 11-sabr-and-smile-dynamics |
| backfill bias | 7 | 03-point-in-time-data-and-the-biases |
| backpropagation | 12 | 07-neural-networks-for-noisy-tabular-data |
| backtest | 7 | 16-vectorised-backtests |
| backtest overfitting | 7 | 20-overfitting |
| backward error | 4 | 25-floating-point-and-numerical-linear-algebra |
| backward stability | 4 | 25-floating-point-and-numerical-linear-algebra |
| backward-looking caplet | 6 | 10-modelling-overnight-rate-products |
| backward-looking rate | 6 | 10-modelling-overnight-rate-products |
| backwardation | 1 | 21-basis-roll-and-delivery |
| bag of words | 12 | 13-text-from-bag-of-words-to-embeddings |
| bagging | 12 | 05-trees-and-boosting |
| bail-in | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| balance-sheet cost | 9 | 12-swap-spread-and-asset-swap-trades |
| balancing group | 3 | 13-getting-access-commodities-and-power |
| balancing responsible party | 3 | 06-power-markets-trading |
| banging the close | 2 | 17-fixings-and-flows |
| bank run | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| banking book | 6 | 23-regulatory-capital-for-trading-books |
| bankruptcy price | 3 | 18-margin-liquidation-and-loss-allocation |
| bar | 7 | 02-market-data-for-research |
| bargaining power | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| barrier option | 2 | 19-the-fx-options-market |
| barrier rebate | 5 | 15-barriers-and-digitals |
| barrier shift | 5 | 15-barriers-and-digitals |
| base correlation | 2 | 24-credit-indices-and-tranches |
| base currency | 2 | 14-the-fx-market |
| base fee | 3 | 14-blockchains-for-traders |
| baseline model | 12 | 04-linear-and-regularised-baselines |
| basis | 1 | 21-basis-roll-and-delivery |
| basis carry | 8 | 27-crypto-medium-frequency-strategies |
| basis expansion | 12 | 04-linear-and-regularised-baselines |
| basis funding trade | 9 | 14-cross-currency-basis-and-fx-carry |
| basis risk | 3 | 01-physical-commodity-markets |
| basis trade | 2 | 06-bond-futures |
| basis trade at index close | 1 | 21-basis-roll-and-delivery |
| basis-trade leverage | 9 | 11-the-bond-futures-basis-trade |
| basket liquidity profile | 10 | 22-portfolio-trades-and-risk-bids |
| basket option | 5 | 17-multi-asset-options |
| batch normalisation | 12 | 07-neural-networks-for-noisy-tabular-data |
| Bates model | 5 | 13-jumps-and-levy-models |
| battery arbitrage | 9 | 23-power-and-gas-trading |
| Bayes--Nash equilibrium | 4 | 29-games-auctions-and-information |
| Bayesian game | 4 | 29-games-auctions-and-information |
| Bayesian update | 2 | 30-market-making-games |
| bear flattening | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| Bellman equation | 12 | 17-reinforcement-learning-foundations |
| benchmark | 1 | 03-the-buy-side |
| benchmark crude | 3 | 02-crude-oil |
| benchmark fix | 2 | 17-fixings-and-flows |
| benchmark manipulation | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| benchmark model | 6 | 26-model-risk-and-validation |
| Benjamini--Hochberg procedure | 4 | 12-testing-and-multiple-testing |
| Bergomi model | 5 | 12-rough-volatility-and-forward-variance-models |
| Bermudan exercise | 5 | 06-american-options-and-early-exercise |
| Bermudan swaption | 6 | 09-bermudans-and-callables |
| best execution | 1 | 11-european-equity-market-structure |
| best-of option | 5 | 17-multi-asset-options |
| bet delay | 11 | 26-prediction-and-sports-market-making |
| beta neutrality | 7 | 25-portfolio-construction-i |
| betting against beta | 8 | 06-value-quality-and-low-risk |
| betting exchange | 3 | 27-prediction-and-betting-markets |
| BFGS method | 4 | 24-numerical-optimisation-in-practice |
| bfloat16 | 12 | 23-training-infrastructure |
| bias statistic | 7 | 24-risk-models |
| bias--variance decomposition | 12 | 01-why-financial-machine-learning-is-different |
| bid shading | 4 | 29-games-auctions-and-information |
| bid--ask bounce | 4 | 21-high-frequency-econometrics |
| bid--ask spread | 1 | 01-what-a-trading-firm-does |
| bid--offer reserve | 5 | 27-managing-an-exotic-book |
| bid-to-cover ratio | 2 | 04-the-treasury-market |
| bidding zone | 3 | 05-power-markets-design |
| bilateral CVA | 6 | 18-credit-and-debit-valuation-adjustments |
| bilateral repo | 2 | 05-repo-and-specials |
| bill of lading | 3 | 01-physical-commodity-markets |
| binary log | 13 | 23-logging-capture-and-replay |
| binomial model | 5 | 02-the-binomial-model |
| bipower variation | 4 | 21-high-frequency-econometrics |
| birth--death process | 4 | 08-markov-chains-and-queues |
| bisection method | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| bitemporal data | 7 | 03-point-in-time-data-and-the-biases |
| bitwise reproducibility | 4 | 25-floating-point-and-numerical-linear-algebra |
| Black model | 5 | 03-black-scholes-three-ways |
| Black--Karasinski model | 6 | 07-short-rate-models |
| Black--Litterman model | 7 | 26-portfolio-construction-ii |
| Black--Scholes equation | 5 | 03-black-scholes-three-ways |
| Black--Scholes formula | 5 | 03-black-scholes-three-ways |
| Black--Scholes model | 5 | 03-black-scholes-three-ways |
| blackout period | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| blind risk bid | 10 | 22-portfolio-trades-and-risk-bids |
| block builder | 3 | 22-maximal-extractable-value |
| block leave | 6 | 28-operational-risk-and-rogue-trading |
| block order | 3 | 05-power-markets-design |
| block trade | 1 | 02-the-sell-side |
| blockchain | 3 | 14-blockchains-for-traders |
| BM25 | 12 | 14-large-language-models-in-finance |
| board lot | 1 | 12-asian-and-emerging-equity-markets |
| bond floor | 5 | 21-convertibles-and-the-credit-equity-link |
| bond-equivalent yield | 2 | 02-money-markets |
| Bonferroni correction | 4 | 12-testing-and-multiple-testing |
| book builder | 13 | 19-the-order-book-builder |
| book checksum | 3 | 26-crypto-data-and-infrastructure |
| book resilience | 10 | 03-empirical-facts-of-order-books |
| book-to-price ratio | 8 | 06-value-quality-and-low-risk |
| bookmaker | 3 | 27-prediction-and-betting-markets |
| bootstrap | 4 | 13-resampling |
| bootstrap percentile interval | 4 | 13-resampling |
| borrow fee | 1 | 06-financing |
| borrow-fee signal | 8 | 08-short-interest-borrow-and-crowding |
| bounds-check elimination | 13 | 09-rust-for-low-latency |
| box spread | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| branch misprediction | 13 | 02-cpu-microarchitecture |
| branch prediction | 13 | 02-cpu-microarchitecture |
| branching ratio | 4 | 07-point-processes-and-hawkes-processes |
| breadth | 7 | 15-from-signal-to-forecast |
| break price | 8 | 11-merger-arbitrage |
| break-even cost | 7 | 27-transaction-costs-in-research |
| break-even volatility | 5 | 04-greeks-and-the-hedging-pnl |
| breakdown point | 4 | 15-robust-statistics-and-heavy-tails |
| breakeven inflation rate | 2 | 11-inflation-markets |
| breakout rule | 8 | 19-trend-following |
| Breeden--Litzenberger formula | 5 | 07-implied-volatility-and-its-surface |
| Brennan--Schwartz algorithm | 5 | 22-trees-and-finite-difference-pricers-in-practice |
| Brent CFD | 3 | 02-crude-oil |
| Brent's method | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| bridge | 3 | 14-blockchains-for-traders |
| broker | 1 | 04-exchanges-brokers-venues |
| broker scorecard | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| broker-dealer | 1 | 02-the-sell-side |
| Brownian bridge | 4 | 02-brownian-motion |
| Brownian bridge construction | 4 | 26-monte-carlo |
| Brownian motion | 4 | 02-brownian-motion |
| Brownian motion with drift | 4 | 02-brownian-motion |
| bucket-shaped trajectory | 10 | 15-beyond-almgren-chriss |
| bucketed sensitivity | 6 | 03-rates-risk |
| buffer rule | 1 | 15-index-construction-and-rebalancing |
| bulk volume classification | 7 | 09-trade-flow-features |
| bull steepening | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| bump-and-reprice | 5 | 04-greeks-and-the-hedging-pnl |
| Bund | 2 | 07-european-and-japanese-government-bonds |
| bundle | 2 | 08-short-term-interest-rate-futures |
| bundle bid | 11 | 25-on-chain-trading |
| burn analysis | 3 | 11-freight-weather-and-other-corners |
| burn-in | 4 | 14-bayesian-methods |
| burnout | 6 | 12-mortgage-modelling |
| business time | 5 | 08-parametrising-the-surface |
| busted convertible | 9 | 08-convertible-arbitrage |
| busy polling | 13 | 13-linux-tuning |
| butterfly | 2 | 19-the-fx-options-market |
| butterfly arbitrage | 5 | 07-implied-volatility-and-its-surface |
| buy side | 1 | 03-the-buy-side |
| buy-in | 1 | 16-stock-loan-and-short-selling |
| cache coherence | 13 | 03-memory-hierarchy-and-caches |
| cache line | 13 | 03-memory-hierarchy-and-caches |
| cache miss | 13 | 03-memory-hierarchy-and-caches |
| calendar arbitrage | 5 | 07-implied-volatility-and-its-surface |
| calendar effect | 8 | 23-seasonality-and-calendar-effects |
| calendar month average | 3 | 02-crude-oil |
| calendar spread | 1 | 19-matching-algorithms-and-implied-spreads |
| calendar-spread option | 3 | 12-commodity-options-and-structured-hedges |
| calibration | 4 | 24-numerical-optimisation-in-practice |
| calibration curve | 7 | 15-from-signal-to-forecast |
| call auction | 1 | 13-auctions |
| call option | 1 | 23-option-contracts-and-exchanges |
| call-spread overhedge | 5 | 15-barriers-and-digitals |
| callable bond | 2 | 13-the-rates-options-market |
| callable range accrual | 6 | 09-bermudans-and-callables |
| Calmar ratio | 7 | 22-performance-measurement |
| canary deployment | 7 | 21-live-experiments |
| cancel on disconnect | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| cancel--fill race | 13 | 21-order-gateway-and-order-management |
| cancel-replace | 11 | 10-the-quoting-engine |
| cancellation rate | 7 | 08-order-book-features |
| cancelled warrant | 3 | 08-metals |
| cap | 2 | 13-the-rates-options-market |
| cap-and-trade | 3 | 07-emissions-and-environmental-markets |
| capacity curve | 7 | 28-capacity-decay-and-crowding |
| capacity market | 3 | 05-power-markets-design |
| capital control | 2 | 18-emerging-market-fx-and-ndfs |
| capital valuation adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| capital-protected note | 5 | 19-the-structured-products-business |
| capital-structure arbitrage | 6 | 14-structural-credit-models |
| caplet | 2 | 13-the-rates-options-market |
| caplet stripping | 6 | 04-vanilla-rates-options |
| caplet volatility | 6 | 04-vanilla-rates-options |
| capture decay | 11 | 28-pnl-analytics-and-the-strategy-lifecycle |
| capture price | 3 | 06-power-markets-trading |
| carbon border adjustment mechanism | 3 | 07-emissions-and-environmental-markets |
| carbon credit | 3 | 07-emissions-and-environmental-markets |
| Carr--Madan formula | 5 | 24-fourier-pricing-and-calibration-engineering |
| carry | 1 | 07-pnl-and-positions |
| carry crash | 8 | 20-carry-across-asset-classes |
| carry strategy | 8 | 20-carry-across-asset-classes |
| cash annuity | 6 | 04-vanilla-rates-options |
| cash creation | 3 | 19-dated-futures-options-and-etfs |
| cash gamma | 5 | 04-greeks-and-the-hedging-pnl |
| cash settlement | 1 | 21-basis-roll-and-delivery |
| cash-and-carry trade | 3 | 10-forward-curves-storage-and-convenience-yield |
| cash-settled swaption | 6 | 04-vanilla-rates-options |
| catastrophic cancellation | 4 | 25-floating-point-and-numerical-linear-algebra |
| causal convolution | 12 | 08-sequence-models-on-order-books |
| CCP basis | 2 | 10-swap-clearing-and-the-ccp-basis |
| central counterparty | 1 | 05-clearing-and-settlement |
| central risk book | 9 | 25-the-central-risk-book |
| central securities depository | 1 | 05-clearing-and-settlement |
| central-bank backstop | 2 | 07-european-and-japanese-government-bonds |
| central-bank reaction trade | 9 | 15-fx-flow-strategies |
| centralised exchange | 3 | 15-centralised-exchanges |
| certainty equivalent | 4 | 09-stochastic-control |
| certificate of deposit | 2 | 02-money-markets |
| CEX--DEX arbitrage | 3 | 22-maximal-extractable-value |
| CFL condition | 4 | 27-finite-difference-methods |
| champion--challenger | 12 | 27-monitoring-and-retraining |
| change of measure | 4 | 01-probability-at-speed |
| change of numeraire | 4 | 05-girsanov-and-changes-of-numeraire |
| characteristic exponent | 4 | 06-jump-processes |
| characteristic function | 4 | 01-probability-at-speed |
| chartist agent | 10 | 27-build-an-agent-based-market |
| cheapest-to-deliver | 2 | 06-bond-futures |
| checkpointing | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| Cheyette model | 6 | 10-modelling-overnight-rate-products |
| child order | 10 | 14-the-almgren-chriss-framework |
| Cholesky factorisation | 4 | 25-floating-point-and-numerical-linear-algebra |
| Christoffersen test | 6 | 21-market-risk-measures |
| classifier two-sample test | 12 | 16-generative-models-and-synthetic-data |
| clean dark spread | 3 | 07-emissions-and-environmental-markets |
| clean price | 2 | 03-government-bonds |
| clean spark spread | 3 | 07-emissions-and-environmental-markets |
| clean-up trade | 10 | 17-child-order-placement |
| clearing | 1 | 05-clearing-and-settlement |
| clearing broker | 1 | 29-getting-access-equities |
| clearing broker (swaps) | 2 | 28-getting-access-rates-credit |
| clearing mandate | 2 | 10-swap-clearing-and-the-ccp-basis |
| clearing member | 1 | 30-getting-access-futures-options |
| clearly erroneous trade | 1 | 31-stress-case-studies |
| client clearing | 2 | 10-swap-clearing-and-the-ccp-basis |
| client tiering | 9 | 24-flow-market-making-at-a-bank |
| cliquet | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| close-out amount | 6 | 18-credit-and-debit-valuation-adjustments |
| close-out netting | 6 | 17-counterparty-exposure |
| closed-end fund discount | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| closing price | 1 | 13-auctions |
| cloud region | 3 | 26-crypto-data-and-infrastructure |
| clustered feature importance | 12 | 06-feature-engineering-selection-and-importance |
| clustered standard errors | 4 | 16-linear-models-under-stress |
| clustering | 12 | 20-clustering-regimes-and-anomaly-detection |
| CMS convexity adjustment | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| CMS spread option | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| co-terminal swaption | 6 | 09-bermudans-and-callables |
| coherent risk measure | 6 | 21-market-risk-measures |
| coin-margined contract | 3 | 19-dated-futures-options-and-etfs |
| cointegrating vector | 4 | 20-multivariate-series-and-cointegration |
| cointegration | 4 | 20-multivariate-series-and-cointegration |
| cointegration rank | 4 | 20-multivariate-series-and-cointegration |
| cold path | 13 | 07-cpp-for-latency-ii-compile-time |
| cold wallet | 3 | 24-the-crypto-trading-business |
| collar | 3 | 12-commodity-options-and-structured-hedges |
| collateral choice option | 6 | 02-multi-curve-and-collateral-discounting |
| collateral mirroring | 3 | 25-getting-access-crypto-venues |
| collateral rate | 6 | 02-multi-curve-and-collateral-discounting |
| collateral return | 3 | 10-forward-curves-storage-and-convenience-yield |
| collateral threshold | 6 | 17-counterparty-exposure |
| collateralised loan obligation | 2 | 25-loans-clos-and-securitisation |
| collective action clause | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| combinatorial purged cross-validation | 7 | 20-overfitting |
| combinatorially symmetric cross-validation | 7 | 20-overfitting |
| commercial paper | 2 | 02-money-markets |
| commission sharing agreement | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| Commitments of Traders report | 3 | 09-agriculturals-and-softs |
| commodity index | 3 | 10-forward-curves-storage-and-convenience-yield |
| commodity swap | 3 | 01-physical-commodity-markets |
| commodity trading advisor | 1 | 03-the-buy-side |
| commodity trading house | 3 | 01-physical-commodity-markets |
| common-value auction | 4 | 29-games-auctions-and-information |
| comomentum | 7 | 28-capacity-decay-and-crowding |
| compare-and-swap | 13 | 11-lock-free-programming |
| compensated Poisson process | 4 | 06-jump-processes |
| compensated summation | 4 | 25-floating-point-and-numerical-linear-algebra |
| compensator | 4 | 07-point-processes-and-hawkes-processes |
| compile-time evaluation | 13 | 07-cpp-for-latency-ii-compile-time |
| compiler barrier | 13 | 02-cpu-microarchitecture |
| compiler intrinsic | 13 | 14-vector-instructions-and-data-parallel-code |
| complete market | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| complex order book | 1 | 24-options-market-structure |
| component share | 10 | 08-fragmentation-and-routing |
| composite option | 5 | 17-multi-asset-options |
| composite price | 2 | 22-how-bonds-trade |
| composite signal | 7 | 14-signal-combination |
| compound correlation | 6 | 15-portfolio-credit |
| compound Poisson process | 4 | 06-jump-processes |
| compounding in arrears | 2 | 01-central-banks-and-the-short-rate |
| concentrated liquidity | 3 | 20-automated-market-makers |
| concentration add-on | 6 | 25-margin-models |
| concept drift | 12 | 12-online-learning-and-drift |
| condition number | 4 | 25-floating-point-and-numerical-linear-algebra |
| conditional autoencoder | 12 | 09-cross-sectional-deep-models |
| conditional expectation | 4 | 01-probability-at-speed |
| conditional heteroskedasticity | 4 | 18-volatility-models |
| conditional intensity | 4 | 07-point-processes-and-hawkes-processes |
| conditional order | 10 | 09-dark-pools-and-blocks |
| conditional prepayment rate | 2 | 12-mortgages-and-agencies |
| conflation | 13 | 12-queues-ring-buffers-and-shared-memory |
| conformal prediction | 12 | 11-probabilistic-models-and-uncertainty |
| congestion rent | 3 | 05-power-markets-design |
| conjugate gradient method | 4 | 25-floating-point-and-numerical-linear-algebra |
| conjugate prior | 4 | 14-bayesian-methods |
| connection pool | 13 | 17-websocket-rest-tls-and-json-at-speed |
| consensus forecast | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| consensus protocol | 3 | 14-blockchains-for-traders |
| consistent estimator | 4 | 11-estimation |
| consistent scheme | 4 | 27-finite-difference-methods |
| consolidated fair price | 11 | 02-fair-value |
| consolidated tape provider | 1 | 11-european-equity-market-structure |
| constant-maturity swap | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| constant-product market maker | 3 | 20-automated-market-makers |
| contango | 1 | 21-basis-roll-and-delivery |
| content-addressed storage | 7 | 29-build-a-research-workflow |
| context switch | 13 | 13-linux-tuning |
| context window | 12 | 14-large-language-models-in-finance |
| contextual bandit | 12 | 17-reinforcement-learning-foundations |
| contingent claim | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| contingent convertible bond | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| contingent credit default swap | 6 | 20-the-valuation-adjustment-desk |
| continuation region | 4 | 10-optimal-stopping-and-impulse-control |
| continuous futures series | 7 | 02-market-data-for-research |
| continuous ranked probability score | 12 | 11-probabilistic-models-and-uncertainty |
| continuous-time Markov chain | 4 | 08-markov-chains-and-queues |
| contract for difference | 1 | 17-delta-one-instruments |
| contract multiplier | 1 | 18-futures-contracts-and-exchanges |
| contrastive learning | 12 | 10-representation-learning |
| control variate | 4 | 26-monte-carlo |
| convenience yield | 3 | 10-forward-curves-storage-and-convenience-yield |
| conversion arbitrage | 11 | 20-options-cross-venue-and-volatility-arbitrage-at-speed |
| conversion factor | 2 | 06-bond-futures |
| conversion premium | 5 | 21-convertibles-and-the-credit-equity-link |
| conversion price | 5 | 21-convertibles-and-the-credit-equity-link |
| conversion ratio | 5 | 21-convertibles-and-the-credit-equity-link |
| conversion value | 5 | 21-convertibles-and-the-credit-equity-link |
| convertibility | 2 | 18-emerging-market-fx-and-ndfs |
| convertible arbitrage | 5 | 21-convertibles-and-the-credit-equity-link |
| convertible bond | 5 | 21-convertibles-and-the-credit-equity-link |
| convertible delta hedge | 9 | 08-convertible-arbitrage |
| convex function | 4 | 23-convex-optimisation |
| convex optimisation problem | 4 | 23-convex-optimisation |
| convex risk measure | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| convex set | 4 | 23-convex-optimisation |
| convexity | 2 | 03-government-bonds |
| convexity adjustment | 2 | 08-short-term-interest-rate-futures |
| convexity budget | 9 | 17-discretionary-macro |
| convolutional neural network | 12 | 08-sequence-models-on-order-books |
| cooling degree day | 3 | 11-freight-weather-and-other-corners |
| coordinated omission | 13 | 05-measuring-latency |
| copula | 4 | 15-robust-statistics-and-heavy-tails |
| core isolation | 13 | 13-linux-tuning |
| core--periphery network | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| correlation asymmetry | 7 | 05-stylised-facts-of-returns |
| correlation breakdown | 3 | 28-when-markets-break-together |
| correlation risk premium | 9 | 02-dispersion-and-correlation |
| correlation skew | 5 | 17-multi-asset-options |
| correlation swap | 5 | 17-multi-asset-options |
| corridor system | 2 | 01-central-banks-and-the-short-rate |
| corridor variance swap | 5 | 14-variance-swaps-and-volatility-derivatives |
| COS method | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| cost insurance and freight | 3 | 01-physical-commodity-markets |
| cost of carry | 1 | 21-basis-roll-and-delivery |
| cost-aware optimisation | 7 | 27-transaction-costs-in-research |
| counter-based generator | 4 | 26-monte-carlo |
| counterfactual explanation | 12 | 21-interpretability-and-model-governance |
| counterfactual impact | 7 | 18-order-book-replay-simulation |
| counterparty credit risk | 6 | 17-counterparty-exposure |
| counterparty exposure | 6 | 17-counterparty-exposure |
| counting process | 4 | 07-point-processes-and-hawkes-processes |
| coupon | 2 | 03-government-bonds |
| coupon barrier | 5 | 18-autocallables |
| courtsiding | 11 | 26-prediction-and-sports-market-making |
| covariance matrix | 4 | 22-covariance-estimation-and-random-matrices |
| covariate shift | 12 | 12-online-learning-and-drift |
| covenant | 2 | 21-corporate-bonds |
| covenant-lite | 2 | 25-loans-clos-and-securitisation |
| cover price | 11 | 22-bond-and-etf-request-for-quote-market-making |
| coverage probability | 4 | 13-resampling |
| covered interest parity | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| Cox process | 4 | 07-point-processes-and-hawkes-processes |
| Cox--Ross--Rubinstein tree | 5 | 02-the-binomial-model |
| CPU affinity | 13 | 13-linux-tuning |
| CPU feature dispatch | 13 | 14-vector-instructions-and-data-parallel-code |
| crack spread | 3 | 03-refined-products-and-cracks |
| Crank--Nicolson scheme | 4 | 27-finite-difference-methods |
| crash-hedged carry | 9 | 14-cross-currency-basis-and-fx-carry |
| creation basket | 1 | 14-exchange-traded-funds |
| creation fee | 11 | 12-etf-market-making |
| creation unit | 1 | 14-exchange-traded-funds |
| credible interval | 4 | 14-bayesian-methods |
| credit curve trade | 9 | 18-credit-relative-value |
| credit default swap | 2 | 23-credit-default-swaps |
| credit event | 2 | 23-credit-default-swaps |
| credit factor | 9 | 19-systematic-credit-and-bond-etf-arbitrage |
| credit index | 2 | 24-credit-indices-and-tranches |
| credit index arbitrage | 9 | 18-credit-relative-value |
| credit index option | 2 | 24-credit-indices-and-tranches |
| credit rating | 2 | 21-corporate-bonds |
| credit spread | 2 | 21-corporate-bonds |
| credit support annex | 2 | 10-swap-clearing-and-the-ccp-basis |
| credit triangle | 6 | 13-reduced-form-credit |
| credit valuation adjustment | 6 | 18-credit-and-debit-valuation-adjustments |
| credit-hedged convertible | 9 | 08-convertible-arbitrage |
| crisis alpha | 8 | 19-trend-following |
| crop year | 3 | 09-agriculturals-and-softs |
| cross margin | 3 | 18-margin-liquidation-and-loss-allocation |
| cross rate | 2 | 14-the-fx-market |
| cross-asset feature | 7 | 10-cross-sectional-and-cross-asset-features |
| cross-asset hedge ratio | 9 | 09-capital-structure-arbitrage |
| cross-currency basis | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| cross-currency basis swap | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| cross-exchange market making | 11 | 24-crypto-high-frequency-trading-on-centralised-venues |
| cross-gamma | 6 | 03-rates-risk |
| cross-impact | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| cross-impact matrix | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| cross-instrument fair price | 11 | 02-fair-value |
| cross-listed futures | 11 | 13-index-and-basket-arbitrage |
| cross-sectional momentum | 8 | 05-momentum |
| cross-sectional z-score | 7 | 06-anatomy-of-a-predictor |
| cross-underlying volatility spread | 9 | 03-skew-and-term-structure-relative-value |
| cross-validation | 4 | 16-linear-models-under-stress |
| cross-venue arbitrage | 3 | 16-spot-markets |
| cross-venue lead | 11 | 08-lead-lag-and-cross-venue-trading |
| crossed market | 10 | 08-fragmentation-and-routing |
| crossing network | 10 | 09-dark-pools-and-blocks |
| crowded trade | 7 | 28-capacity-decay-and-crowding |
| crowding | 7 | 28-capacity-decay-and-crowding |
| CRRA utility | 4 | 09-stochastic-control |
| crush spread | 3 | 09-agriculturals-and-softs |
| crypto reference rate | 3 | 19-dated-futures-options-and-etfs |
| crypto-asset service provider | 3 | 24-the-crypto-trading-business |
| CS01 | 6 | 13-reduced-form-credit |
| CSA discounting | 6 | 02-multi-curve-and-collateral-discounting |
| cubic spline | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| cumulant | 4 | 06-jump-processes |
| cumulative reward | 12 | 17-reinforcement-learning-foundations |
| CUPED | 7 | 21-live-experiments |
| curiously recurring template pattern | 13 | 07-cpp-for-latency-ii-compile-time |
| currency band | 2 | 18-emerging-market-fx-and-ndfs |
| currency pair | 2 | 14-the-fx-market |
| currency peg | 2 | 18-emerging-market-fx-and-ndfs |
| current coupon | 6 | 12-mortgage-modelling |
| curvature factor | 6 | 03-rates-risk |
| curvature risk charge | 6 | 23-regulatory-capital-for-trading-books |
| curve calibration | 6 | 01-curve-construction |
| curve fly | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| curve Jacobian | 6 | 03-rates-risk |
| curve trade | 8 | 21-calendar-spreads-and-curve-trades |
| custom basket | 11 | 12-etf-market-making |
| customer asset segregation | 3 | 15-centralised-exchanges |
| customer priority | 1 | 24-options-market-structure |
| CUSUM test | 7 | 13-half-life-decay-and-stability |
| CVA risk capital | 6 | 19-funding-margin-and-capital-adjustments |
| daily P\&L attribution | 8 | 01-anatomy-of-a-stat-arb-book |
| daily settlement price | 1 | 18-futures-contracts-and-exchanges |
| dark pool | 1 | 09-us-equity-market-structure |
| dark spread | 3 | 05-power-markets-design |
| dash for cash | 2 | 04-the-treasury-market |
| data augmentation | 12 | 10-representation-learning |
| data decay | 8 | 16-alternative-data-strategies |
| data loader | 12 | 23-training-infrastructure |
| data parallelism | 12 | 23-training-infrastructure |
| data race | 13 | 09-rust-for-low-latency |
| data snapshot | 7 | 29-build-a-research-workflow |
| data snooping | 4 | 12-testing-and-multiple-testing |
| data surprise | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| data trial | 7 | 12-alternative-and-text-data |
| data versioning | 12 | 25-experiment-tracking-and-reproducibility |
| data vintage | 7 | 03-point-in-time-data-and-the-biases |
| Dated Brent | 3 | 02-crude-oil |
| dated future | 3 | 19-dated-futures-options-and-etfs |
| day-ahead market | 3 | 05-power-markets-design |
| day-ahead-intraday spread | 9 | 23-power-and-gas-trading |
| day-count convention | 2 | 03-government-bonds |
| day-one P\&L | 5 | 27-managing-an-exotic-book |
| days to cover | 1 | 16-stock-loan-and-short-selling |
| deal spread | 8 | 11-merger-arbitrage |
| dealer gamma | 1 | 26-zero-day-options-and-retail-flow |
| dealer-to-client platform | 2 | 04-the-treasury-market |
| debit valuation adjustment | 6 | 18-credit-and-debit-valuation-adjustments |
| decay kernel | 10 | 12-transient-impact-and-propagator-models |
| decentralised exchange | 3 | 20-automated-market-makers |
| decision staleness | 12 | 29-build-an-order-book-model-end-to-end |
| decision time | 7 | 16-vectorised-backtests |
| decision tree | 12 | 05-trees-and-boosting |
| decision-focused learning | 12 | 22-from-prediction-to-portfolio |
| decrement index | 5 | 19-the-structured-products-business |
| dedicated endpoint | 3 | 25-getting-access-crypto-venues |
| deep calibration | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| deep ensemble | 12 | 07-neural-networks-for-noisy-tabular-data |
| deep hedging | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| deep Q-network | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| default barrier | 6 | 14-structural-credit-models |
| default correlation | 6 | 15-portfolio-credit |
| default fund | 1 | 05-clearing-and-settlement |
| default risk charge | 6 | 23-regulatory-capital-for-trading-books |
| default risk premium | 6 | 13-reduced-form-credit |
| default waterfall | 1 | 05-clearing-and-settlement |
| defensive widening | 11 | 06-adverse-selection-and-toxicity |
| deferred formatting | 13 | 23-logging-capture-and-replay |
| deflated Sharpe ratio | 4 | 12-testing-and-multiple-testing |
| deflation floor | 2 | 11-inflation-markets |
| delay cost | 7 | 23-measuring-market-making-and-execution |
| delisting return | 7 | 04-universe-symbology-and-corporate-actions |
| deliverable basket | 2 | 06-bond-futures |
| delivery versus payment | 1 | 05-clearing-and-settlement |
| delta | 1 | 26-zero-day-options-and-retail-flow |
| delta hedging | 1 | 26-zero-day-options-and-retail-flow |
| delta method | 4 | 11-estimation |
| delta--gamma approximation | 6 | 21-market-risk-measures |
| delta-equivalent inventory | 11 | 11-hedging-and-inventory-in-practice |
| delta-hedged option return | 9 | 01-harvesting-the-variance-risk-premium |
| delta-neutral straddle | 2 | 19-the-fx-options-market |
| delta-one | 1 | 17-delta-one-instruments |
| demand shock | 1 | 15-index-construction-and-rebalancing |
| denoising autoencoder | 12 | 10-representation-learning |
| density process | 4 | 01-probability-at-speed |
| deoptimisation | 13 | 10-managed-and-functional-languages-on-the-desk |
| depeg | 3 | 14-blockchains-for-traders |
| deposit beta | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| depositary receipt | 1 | 17-delta-one-instruments |
| depositary receipt issuance | 11 | 14-depositary-receipts-and-dual-listings |
| depositary receipt ratio | 11 | 14-depositary-receipts-and-dual-listings |
| depth imbalance | 7 | 08-order-book-features |
| depth profile | 7 | 08-order-book-features |
| designated contract market | 3 | 13-getting-access-commodities-and-power |
| designated market maker | 1 | 29-getting-access-equities |
| designation notice | 2 | 27-getting-access-fx |
| destination flexibility | 3 | 04-natural-gas-and-lng |
| detachment point | 2 | 24-credit-indices-and-tranches |
| detailed balance | 4 | 08-markov-chains-and-queues |
| determinations committee | 2 | 23-credit-default-swaps |
| deterministic replay | 13 | 23-logging-capture-and-replay |
| device locality | 13 | 04-multi-socket-machines-and-interconnects |
| devirtualisation | 13 | 07-cpp-for-latency-ii-compile-time |
| DEX aggregator | 3 | 20-automated-market-makers |
| Dickey--Fuller test | 4 | 17-linear-time-series |
| dictionary method | 7 | 12-alternative-and-text-data |
| Diebold--Mariano test | 4 | 18-volatility-models |
| difference-in-differences | 10 | 06-tick-size-queues-and-priority |
| differentiable optimisation layer | 12 | 22-from-prediction-to-portfolio |
| differential machine learning | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| differential test | 13 | 25-testing-and-deploying-low-latency-systems |
| diffusion model | 12 | 16-generative-models-and-synthetic-data |
| digital option | 5 | 15-barriers-and-digitals |
| direct cache access | 13 | 04-multi-socket-machines-and-interconnects |
| direct feed | 1 | 09-us-equity-market-structure |
| direct market access | 1 | 04-exchanges-brokers-venues |
| direct memory access | 13 | 04-multi-socket-machines-and-interconnects |
| dirty price | 2 | 03-government-bonds |
| discount curve | 6 | 02-multi-curve-and-collateral-discounting |
| discount yield | 2 | 02-money-markets |
| discounting switch | 6 | 02-multi-curve-and-collateral-discounting |
| discrete Fourier transform | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| discrete hedging error | 5 | 04-greeks-and-the-hedging-pnl |
| discriminatory auction | 4 | 29-games-auctions-and-information |
| dispersion trade | 5 | 17-multi-asset-options |
| dispersion weighting | 9 | 02-dispersion-and-correlation |
| disruptor pattern | 13 | 12-queues-ring-buffers-and-shared-memory |
| dissemination cap | 2 | 22-how-bonds-trade |
| distance method | 8 | 04-pairs-and-baskets |
| distance to default | 6 | 14-structural-credit-models |
| distressed debt | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| divergence decomposition | 7 | 19-simulation-versus-live |
| diversified carry | 8 | 20-carry-across-asset-classes |
| dividend | 1 | 08-shares-corporate-actions-indices |
| dividend enhancement | 1 | 17-delta-one-instruments |
| dividend future | 1 | 22-index-and-single-stock-futures-worldwide |
| dividend play | 5 | 26-options-market-making-in-practice |
| dividend risk | 5 | 05-dividends-borrow-and-forwards |
| dividend supply pressure | 9 | 26-delta-one-and-dividends |
| dividend swap | 5 | 05-dividends-borrow-and-forwards |
| document embedding | 7 | 12-alternative-and-text-data |
| dollar bar | 7 | 02-market-data-for-research |
| dollar neutrality | 7 | 25-portfolio-construction-i |
| dollar roll | 2 | 12-mortgages-and-agencies |
| domain randomisation | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| Doob martingale | 4 | 01-probability-at-speed |
| double volume cap | 1 | 11-european-equity-market-structure |
| double-barrier option | 5 | 15-barriers-and-digitals |
| doubly robust estimator | 12 | 17-reinforcement-learning-foundations |
| drawdown | 2 | 29-thinking-in-expected-value |
| drawdown duration | 7 | 22-performance-measurement |
| drawdown limit | 8 | 28-running-a-multi-strategy-book |
| drift detector | 12 | 12-online-learning-and-drift |
| drift-adjusted quoting | 11 | 04-extensions-of-the-inventory-framework |
| drop copy | 13 | 21-order-gateway-and-order-management |
| dropout | 12 | 07-neural-networks-for-noisy-tabular-data |
| dual listing | 1 | 17-delta-one-instruments |
| dual number | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| dual problem | 4 | 23-convex-optimisation |
| dual upper bound | 5 | 23-monte-carlo-pricers-in-practice |
| dual-class share | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| Dupire formula | 5 | 09-local-volatility |
| duration-neutral butterfly | 9 | 10-government-bond-relative-value |
| Dutch auction | 4 | 29-games-auctions-and-information |
| DV01 | 2 | 03-government-bonds |
| dynamic batching | 12 | 26-low-latency-inference |
| dynamic dispatch | 13 | 07-cpp-for-latency-ii-compile-time |
| dynamic frequency scaling | 13 | 02-cpu-microarchitecture |
| dynamic price band | 10 | 25-circuit-breakers-and-halts |
| dynamic programming | 4 | 09-stochastic-control |
| dynamic VWAP | 10 | 16-benchmark-algorithms |
| early stopping | 12 | 05-trees-and-boosting |
| early-exercise premium | 5 | 06-american-options-and-early-exercise |
| earnings surprise | 7 | 11-fundamental-analyst-and-event-features |
| earnings-revision strategy | 8 | 07-earnings |
| economic link | 7 | 10-cross-sectional-and-cross-asset-features |
| economic rationale | 7 | 01-the-research-process |
| economic release | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| economic value of equity | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| economic-surprise signal | 9 | 16-systematic-macro |
| edge | 2 | 29-thinking-in-expected-value |
| effective breadth | 7 | 15-from-signal-to-forecast |
| effective challenge | 6 | 26-model-risk-and-validation |
| effective duration | 2 | 12-mortgages-and-agencies |
| effective lower bound | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| effective sample size | 4 | 14-bayesian-methods |
| effective spread | 1 | 10-retail-flow-and-wholesaling |
| effective tick size | 10 | 07-fees-rebates-and-venue-economics |
| efficient frontier | 7 | 25-portfolio-construction-i |
| efficient trading frontier | 10 | 14-the-almgren-chriss-framework |
| eigenportfolio | 8 | 03-residual-and-principal-component-stat-arb |
| eigenvalue clipping | 4 | 22-covariance-estimation-and-random-matrices |
| elastic net | 4 | 16-linear-models-under-stress |
| electronic communication network | 2 | 14-the-fx-market |
| electronic market maker | 11 | 01-the-business-of-market-making |
| embargo | 7 | 20-overfitting |
| emission allowance | 3 | 07-emissions-and-environmental-markets |
| empirical Bayes | 4 | 14-bayesian-methods |
| empirical distribution function | 4 | 13-resampling |
| end-of-day flattening | 11 | 11-hedging-and-inventory-in-practice |
| end-of-day hedging flow | 8 | 13-intraday-patterns |
| Engle--Granger test | 4 | 20-multivariate-series-and-cointegration |
| English auction | 4 | 29-games-auctions-and-information |
| entity embedding | 12 | 09-cross-sectional-deep-models |
| entity linking | 12 | 13-text-from-bag-of-words-to-embeddings |
| entity resolution | 12 | 15-alternative-data-pipelines |
| entropic risk measure | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| entropy | 4 | 29-games-auctions-and-information |
| environment lock | 7 | 29-build-a-research-workflow |
| epistemic uncertainty | 12 | 11-probabilistic-models-and-uncertainty |
| epoch | 12 | 07-neural-networks-for-noisy-tabular-data |
| epoch-based reclamation | 13 | 11-lock-free-programming |
| Epps effect | 4 | 21-high-frequency-econometrics |
| equal risk contribution portfolio | 7 | 26-portfolio-construction-ii |
| equal-weight blend | 7 | 14-signal-combination |
| equity swap | 1 | 17-delta-one-instruments |
| equity tranche | 2 | 25-loans-clos-and-securitisation |
| equity-implied spread | 9 | 09-capital-structure-arbitrage |
| equity-to-credit model | 5 | 21-convertibles-and-the-credit-equity-link |
| equivalent martingale measure | 4 | 05-girsanov-and-changes-of-numeraire |
| equivalent measures | 4 | 01-probability-at-speed |
| error maximisation | 7 | 25-portfolio-construction-i |
| errors-in-variables | 4 | 16-linear-models-under-stress |
| escrowed dividend model | 5 | 05-dividends-borrow-and-forwards |
| estimator | 4 | 11-estimation |
| ETF create-redeem arbitrage | 9 | 19-systematic-credit-and-bond-etf-arbitrage |
| ETF discount | 9 | 19-systematic-credit-and-bond-etf-arbitrage |
| ETP rebalancing flow | 9 | 05-the-volatility-index-complex |
| Euler allocation | 6 | 20-the-valuation-adjustment-desk |
| Euler--Maruyama scheme | 4 | 04-stochastic-differential-equations |
| European exercise | 1 | 23-option-contracts-and-exchanges |
| event calendar | 7 | 11-fundamental-analyst-and-event-features |
| event contract | 3 | 27-prediction-and-betting-markets |
| event extraction | 12 | 13-text-from-bag-of-words-to-embeddings |
| event log | 3 | 26-crypto-data-and-infrastructure |
| event loop | 13 | 20-the-strategy-engine |
| event protocol | 11 | 18-news-and-event-trading |
| event straddle | 9 | 04-gamma-scalping-and-event-volatility |
| event study | 8 | 07-earnings |
| event variance | 5 | 08-parametrising-the-surface |
| event window | 8 | 07-earnings |
| event-driven backtest | 7 | 17-event-driven-backtests |
| EWMA volatility | 4 | 18-volatility-models |
| ex-dividend date | 1 | 08-shares-corporate-actions-indices |
| exceedance correlation | 7 | 05-stylised-facts-of-returns |
| exchange | 1 | 04-exchanges-brokers-venues |
| exchange certification | 13 | 25-testing-and-deploying-low-latency-systems |
| exchange for physical | 1 | 21-basis-roll-and-delivery |
| exchange member | 1 | 04-exchanges-brokers-venues |
| exchange membership | 1 | 30-getting-access-futures-options |
| exchange offer | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| exchange simulator | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| exchange timestamp | 1 | 28-reading-market-data |
| exchange-traded fund | 1 | 14-exchange-traded-funds |
| exchange-traded product | 3 | 19-dated-futures-options-and-etfs |
| exchange-traded volatility product | 9 | 05-the-volatility-index-complex |
| exchangeability | 4 | 13-resampling |
| excitation kernel | 4 | 07-point-processes-and-hawkes-processes |
| executing broker | 1 | 29-getting-access-equities |
| execution algorithm | 10 | 16-benchmark-algorithms |
| execution benchmark | 10 | 19-transaction-cost-analysis |
| execution coupling | 8 | 14-intraday-machine-learned-alphas |
| execution lag | 7 | 16-vectorised-backtests |
| execution management system | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| execution report | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| execution risk | 10 | 14-the-almgren-chriss-framework |
| exercise boundary | 5 | 06-american-options-and-early-exercise |
| exotic book exposure | 9 | 28-hedging-a-structured-products-book |
| expanded limit | 3 | 09-agriculturals-and-softs |
| expectation--maximisation algorithm | 4 | 19-state-space-models-and-the-kalman-filter |
| expected exposure | 6 | 17-counterparty-exposure |
| expected negative exposure | 6 | 17-counterparty-exposure |
| expected positive exposure | 6 | 17-counterparty-exposure |
| expected shortfall | 6 | 21-market-risk-measures |
| experience replay | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| experiment tracker | 12 | 25-experiment-tracking-and-reproducibility |
| expiry | 1 | 23-option-contracts-and-exchanges |
| expiry month code | 1 | 18-futures-contracts-and-exchanges |
| explicit scheme | 4 | 27-finite-difference-methods |
| exploration--exploitation trade-off | 12 | 17-reinforcement-learning-foundations |
| exposure at default | 6 | 19-funding-margin-and-capital-adjustments |
| extreme-value theory | 4 | 15-robust-statistics-and-heavy-tails |
| extrinsic value | 6 | 16-commodity-and-energy-derivatives |
| factor exposure | 7 | 24-risk-models |
| factor model | 4 | 22-covariance-estimation-and-random-matrices |
| factor product | 8 | 29-the-asset-managers-strategies |
| factor return | 7 | 24-risk-models |
| factor timing | 8 | 06-value-quality-and-low-risk |
| factor-neutrality constraint | 7 | 25-portfolio-construction-i |
| fail-closed design | 13 | 22-pre-trade-risk-and-kill-switches |
| failover | 13 | 24-resilience |
| fails charge | 2 | 05-repo-and-specials |
| fair price | 11 | 02-fair-value |
| fair pricing condition | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| fair value | 1 | 21-basis-roll-and-delivery |
| fair-price filter | 11 | 02-fair-value |
| fair-value hierarchy | 6 | 27-pnl-explain-and-independent-price-verification |
| fallback spread | 2 | 01-central-banks-and-the-short-rate |
| fallen angel | 2 | 21-corporate-bonds |
| false discovery rate | 4 | 12-testing-and-multiple-testing |
| false sharing | 13 | 03-memory-hierarchy-and-caches |
| Fama--MacBeth regression | 4 | 16-linear-models-under-stress |
| family-wise error rate | 4 | 12-testing-and-multiple-testing |
| fast Fourier transform | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| favourite--longshot bias | 3 | 27-prediction-and-betting-markets |
| feature definition | 12 | 24-data-and-feature-stores |
| feature engineering | 12 | 06-feature-engineering-selection-and-importance |
| feature freshness | 12 | 24-data-and-feature-stores |
| feature selection | 12 | 06-feature-engineering-selection-and-importance |
| feature store | 12 | 24-data-and-feature-stores |
| fee neutrality | 10 | 07-fees-rebates-and-venue-economics |
| fee-adjusted price | 10 | 07-fees-rebates-and-venue-economics |
| feed handler | 13 | 18-the-feed-handler |
| feedback control | 4 | 09-stochastic-control |
| Feller condition | 4 | 04-stochastic-differential-equations |
| fictitious trade | 6 | 28-operational-risk-and-rogue-trading |
| fidelity level | 7 | 16-vectorised-backtests |
| filing lag | 7 | 11-fundamental-analyst-and-event-features |
| fill intensity | 11 | 03-inventory-models |
| fill model | 7 | 17-event-driven-backtests |
| fill rate | 7 | 23-measuring-market-making-and-execution |
| fill-or-kill order | 10 | 02-order-types-and-their-uses |
| filtered historical simulation | 6 | 21-market-risk-measures |
| filtration | 4 | 01-probability-at-speed |
| finality | 3 | 14-blockchains-for-traders |
| financial transmission right | 3 | 06-power-markets-trading |
| financing trade | 9 | 26-delta-one-and-dividends |
| fine-tuning | 12 | 10-representation-learning |
| finite-difference method | 4 | 27-finite-difference-methods |
| fire sale | 3 | 28-when-markets-break-together |
| firm liquidity | 10 | 21-execution-beyond-equities |
| firm-up rate | 10 | 09-dark-pools-and-blocks |
| first-passage model | 6 | 14-structural-credit-models |
| first-passage time | 4 | 02-brownian-motion |
| first-price auction | 4 | 29-games-auctions-and-information |
| first-seen timestamp | 12 | 15-alternative-data-pipelines |
| first-step analysis | 4 | 08-markov-chains-and-queues |
| first-touch allocation | 13 | 04-multi-socket-machines-and-interconnects |
| fiscal period | 7 | 11-fundamental-analyst-and-event-features |
| Fisher information | 4 | 11-estimation |
| fitted-curve residual | 9 | 10-government-bond-relative-value |
| FIX engine | 13 | 15-protocols-i-fix |
| fix flow | 9 | 15-fx-flow-strategies |
| FIX protocol | 13 | 15-protocols-i-fix |
| FIX session | 13 | 15-protocols-i-fix |
| fixed effects | 4 | 16-linear-models-under-stress |
| fixed leg | 2 | 09-interest-rate-swaps |
| fixed-capacity container | 13 | 06-cpp-for-latency-i-memory |
| fixed-horizon label | 12 | 02-targets-labels-and-sample-weights |
| fixing order | 2 | 17-fixings-and-flows |
| fixing source | 2 | 18-emerging-market-fx-and-ndfs |
| fixing window | 2 | 17-fixings-and-flows |
| flash crash | 1 | 31-stress-case-studies |
| flash loan | 3 | 23-defi-credit-and-leverage |
| flash rally | 2 | 04-the-treasury-market |
| flat pricing | 10 | 07-fees-rebates-and-venue-economics |
| flat volatility | 6 | 04-vanilla-rates-options |
| flat-forward interpolation | 6 | 01-curve-construction |
| flattener | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| fleeting order | 10 | 03-empirical-facts-of-order-books |
| flight to quality | 3 | 28-when-markets-break-together |
| float adjustment | 1 | 15-index-construction-and-rebalancing |
| floating leg | 2 | 09-interest-rate-swaps |
| floating storage | 3 | 10-forward-curves-storage-and-convenience-yield |
| floating-point number | 4 | 25-floating-point-and-numerical-linear-algebra |
| floor | 2 | 13-the-rates-options-market |
| floor system | 2 | 01-central-banks-and-the-short-rate |
| flow segmentation | 11 | 23-retail-wholesaling |
| flow toxicity | 7 | 09-trade-flow-features |
| flow trading | 1 | 02-the-sell-side |
| flow-induced trading | 8 | 09-flows |
| flyweight codec | 13 | 16-protocols-ii-binary-exchange-protocols |
| Fokker--Planck equation | 4 | 04-stochastic-differential-equations |
| follow-the-sun trading | 3 | 29-a-map-of-all-markets |
| forecast calibration | 7 | 15-from-signal-to-forecast |
| forecast combination puzzle | 7 | 14-signal-combination |
| forecast dispersion | 7 | 11-fundamental-analyst-and-event-features |
| forecast horizon | 7 | 06-anatomy-of-a-predictor |
| forecast skew | 11 | 07-short-horizon-alpha |
| forecast-error variance decomposition | 4 | 20-multivariate-series-and-cointegration |
| foreign ownership limit | 1 | 12-asian-and-emerging-equity-markets |
| forgetting factor | 12 | 12-online-learning-and-drift |
| formation period | 8 | 04-pairs-and-baskets |
| Formosa bond | 6 | 09-bermudans-and-callables |
| forward Brent | 3 | 02-crude-oil |
| forward curve | 3 | 10-forward-curves-storage-and-convenience-yield |
| forward delta | 2 | 19-the-fx-options-market |
| forward freight agreement | 3 | 11-freight-weather-and-other-corners |
| forward measure | 4 | 05-girsanov-and-changes-of-numeraire |
| forward mode | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| forward points | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| forward smile | 5 | 09-local-volatility |
| forward variance | 5 | 12-rough-volatility-and-forward-variance-models |
| forward-looking term rate | 6 | 10-modelling-overnight-rate-products |
| forward-rate correlation | 6 | 08-forward-rate-and-market-models |
| forward-start option | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| forward-variance model | 5 | 12-rough-volatility-and-forward-variance-models |
| fractional Brownian motion | 4 | 17-linear-time-series |
| fractional differencing | 4 | 17-linear-time-series |
| fractional Kelly | 2 | 29-thinking-in-expected-value |
| franchise | 1 | 02-the-sell-side |
| franchise P\&L | 9 | 24-flow-market-making-at-a-bank |
| free allocation | 3 | 07-emissions-and-environmental-markets |
| free float | 1 | 08-shares-corporate-actions-indices |
| free list | 13 | 06-cpp-for-latency-i-memory |
| free on board | 3 | 01-physical-commodity-markets |
| free option of a limit order | 10 | 02-order-types-and-their-uses |
| free-boundary problem | 4 | 10-optimal-stopping-and-impulse-control |
| frequent batch auction | 10 | 10-auction-mechanics-and-theory |
| front month | 1 | 18-futures-contracts-and-exchanges |
| front-running | 3 | 22-maximal-extractable-value |
| full carry | 3 | 10-forward-curves-storage-and-convenience-yield |
| full node | 3 | 26-crypto-data-and-infrastructure |
| full replication | 8 | 29-the-asset-managers-strategies |
| full revaluation | 6 | 29-build-a-risk-engine |
| function multiversioning | 13 | 08-cpp-for-latency-iii-the-compiler |
| fundamental factor model | 7 | 24-risk-models |
| fundamental law of active management | 7 | 15-from-signal-to-forecast |
| Fundamental Review of the Trading Book | 6 | 23-regulatory-capital-for-trading-books |
| fundamental theorem of asset pricing | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| fundamentalist agent | 10 | 27-build-an-agent-based-market |
| funding arbitrage | 3 | 17-perpetual-futures |
| funding benefit adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| funding carry | 8 | 27-crypto-medium-frequency-strategies |
| funding cost adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| funding interval | 3 | 17-perpetual-futures |
| funding rate | 3 | 17-perpetual-futures |
| funding spread | 1 | 17-delta-one-instruments |
| funding valuation adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| funds-transfer pricing | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| fused multiply-add | 4 | 25-floating-point-and-numerical-linear-algebra |
| futures commission merchant | 1 | 30-getting-access-futures-options |
| futures contract | 1 | 18-futures-contracts-and-exchanges |
| futures option | 3 | 12-commodity-options-and-structured-hedges |
| futures strip | 2 | 08-short-term-interest-rate-futures |
| futures-to-cash lead | 7 | 10-cross-sectional-and-cross-asset-features |
| fuzz testing | 13 | 25-testing-and-deploying-low-latency-systems |
| FX carry basket | 9 | 14-cross-currency-basis-and-fx-carry |
| FX Global Code | 2 | 15-fx-spot-microstructure |
| FX intervention | 2 | 18-emerging-market-fx-and-ndfs |
| FX prime brokerage | 2 | 14-the-fx-market |
| FX swap | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| G-spread | 2 | 21-corporate-bonds |
| gain--loss asymmetry | 7 | 05-stylised-facts-of-returns |
| gamma | 1 | 26-zero-day-options-and-retail-flow |
| gamma exposure estimate | 9 | 06-zero-day-options-and-dealer-gamma-flows |
| gamma flip level | 9 | 06-zero-day-options-and-dealer-gamma-flows |
| gamma scalping | 5 | 25-trading-volatility |
| gamma swap | 5 | 14-variance-swaps-and-volatility-derivatives |
| gap fill | 13 | 15-protocols-i-fix |
| gap risk | 5 | 15-barriers-and-digitals |
| garbage collector | 13 | 10-managed-and-functional-languages-on-the-desk |
| GARCH model | 4 | 18-volatility-models |
| garden of forking paths | 4 | 12-testing-and-multiple-testing |
| Garman--Klass estimator | 7 | 07-price-and-volume-features |
| Garman--Kohlhagen model | 5 | 20-fx-derivatives |
| gas | 3 | 14-blockchains-for-traders |
| gas day | 3 | 04-natural-gas-and-lng |
| gate closure | 3 | 06-power-markets-trading |
| Gauss--Newton method | 4 | 24-numerical-optimisation-in-practice |
| Gaussian copula | 6 | 15-portfolio-credit |
| Gaussian process | 4 | 02-brownian-motion |
| general collateral | 1 | 16-stock-loan-and-short-selling |
| generalisation error | 12 | 01-why-financial-machine-learning-is-different |
| generalised extreme value distribution | 4 | 15-robust-statistics-and-heavy-tails |
| generalised forward market model | 6 | 10-modelling-overnight-rate-products |
| generalised least squares | 4 | 16-linear-models-under-stress |
| generalised method of moments | 4 | 11-estimation |
| generalised Pareto distribution | 4 | 15-robust-statistics-and-heavy-tails |
| generative adversarial network | 12 | 16-generative-models-and-synthetic-data |
| generative model | 12 | 16-generative-models-and-synthetic-data |
| generator matrix | 4 | 08-markov-chains-and-queues |
| geometric Brownian motion | 4 | 04-stochastic-differential-equations |
| Gibbs sampler | 4 | 14-bayesian-methods |
| gilt | 2 | 07-european-and-japanese-government-bonds |
| give-up | 1 | 30-getting-access-futures-options |
| give-up (equities) | 1 | 29-getting-access-equities |
| give-up line | 2 | 27-getting-access-fx |
| GJR-GARCH model | 4 | 18-volatility-models |
| global allocator | 13 | 09-rust-for-low-latency |
| Global Master Repurchase Agreement | 2 | 28-getting-access-rates-credit |
| global surrogate | 12 | 21-interpretability-and-model-governance |
| Glosten--Milgrom model | 10 | 04-why-there-is-a-spread |
| good-till-cancelled order | 10 | 02-order-types-and-their-uses |
| gradient accumulation | 12 | 23-training-infrastructure |
| gradient boosting | 12 | 05-trees-and-boosting |
| gradient descent | 4 | 24-numerical-optimisation-in-practice |
| Granger causality | 4 | 20-multivariate-series-and-cointegration |
| grantor trust | 3 | 19-dated-futures-options-and-etfs |
| Greeks | 5 | 04-greeks-and-the-hedging-pnl |
| gross basis | 2 | 06-bond-futures |
| gross exposure | 1 | 07-pnl-and-positions |
| gross refining margin | 3 | 03-refined-products-and-cracks |
| growth rate | 2 | 29-thinking-in-expected-value |
| guarantee of origin | 3 | 07-emissions-and-environmental-markets |
| HAC estimator | 4 | 11-estimation |
| Hagan formula | 5 | 11-sabr-and-smile-dynamics |
| haircut | 1 | 06-financing |
| half-life | 4 | 04-stochastic-differential-equations |
| hallucination | 12 | 14-large-language-models-in-finance |
| Hamilton--Jacobi--Bellman equation | 4 | 09-stochastic-control |
| handoff specification | 12 | 28-the-machine-learning-team |
| HAR model | 4 | 18-volatility-models |
| hard-to-borrow list | 8 | 01-anatomy-of-a-stat-arb-book |
| hardware performance counter | 13 | 05-measuring-latency |
| hardware prefetching | 13 | 03-memory-hierarchy-and-caches |
| hardware timestamp | 13 | 05-measuring-latency |
| hat matrix | 4 | 16-linear-models-under-stress |
| Hawkes process | 4 | 07-point-processes-and-hawkes-processes |
| Hayashi--Yoshida estimator | 4 | 21-high-frequency-econometrics |
| hazard pointer | 13 | 11-lock-free-programming |
| hazard rate | 2 | 23-credit-default-swaps |
| health factor | 3 | 23-defi-credit-and-leverage |
| heartbeat | 13 | 15-protocols-i-fix |
| Heath--Jarrow--Morton framework | 6 | 08-forward-rate-and-market-models |
| heating degree day | 3 | 11-freight-weather-and-other-corners |
| heavy-tailed distribution | 4 | 15-robust-statistics-and-heavy-tails |
| hedge bleed | 9 | 07-tail-hedging-and-long-volatility |
| hedge fund | 1 | 01-what-a-trading-firm-does |
| hedge instrument | 11 | 11-hedging-and-inventory-in-practice |
| hedge monetisation | 9 | 07-tail-hedging-and-long-volatility |
| hedge venue | 11 | 24-crypto-high-frequency-trading-on-centralised-venues |
| hedged liquidity provision | 11 | 25-on-chain-trading |
| hedger | 1 | 18-futures-contracts-and-exchanges |
| hedging band | 5 | 26-options-market-making-in-practice |
| hedging P\&L | 5 | 04-greeks-and-the-hedging-pnl |
| hedging pressure | 8 | 24-positioning-and-sentiment |
| hedging programme | 3 | 12-commodity-options-and-structured-hedges |
| held-to-maturity portfolio | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| Henry Hub | 3 | 04-natural-gas-and-lng |
| Herstatt risk | 2 | 20-settlement-risk |
| Heston model | 5 | 10-stochastic-volatility |
| heterogeneous cores | 13 | 02-cpu-microarchitecture |
| hidden Markov model | 12 | 20-clustering-regimes-and-anomaly-detection |
| hidden order | 10 | 02-order-types-and-their-uses |
| hierarchical clustering | 12 | 20-clustering-regimes-and-anomaly-detection |
| hierarchical model | 4 | 14-bayesian-methods |
| hierarchical risk parity | 7 | 26-portfolio-construction-ii |
| high yield | 2 | 21-corporate-bonds |
| high-frequency trading | 10 | 24-market-quality-and-regulation |
| high-quality liquid assets | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| high-touch trading | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| high-water mark | 1 | 03-the-buy-side |
| Hill estimator | 4 | 15-robust-statistics-and-heavy-tails |
| historical scenario | 6 | 22-stress-testing-and-scenarios |
| historical simulation | 6 | 21-market-risk-measures |
| hit rate | 7 | 22-performance-measurement |
| hit ratio | 7 | 23-measuring-market-making-and-execution |
| hitting probability | 4 | 08-markov-chains-and-queues |
| hitting time | 4 | 02-brownian-motion |
| HJM drift condition | 6 | 08-forward-rate-and-market-models |
| hold time | 2 | 15-fx-spot-microstructure |
| holding-company discount | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| holdout creditor | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| holdout set | 7 | 01-the-research-process |
| Holm procedure | 4 | 12-testing-and-multiple-testing |
| hot path | 13 | 01-where-latency-comes-from |
| hot wallet | 3 | 24-the-crypto-trading-business |
| hot-potato trading | 10 | 24-market-quality-and-regulation |
| housekeeping core | 13 | 13-linux-tuning |
| housing turnover | 6 | 12-mortgage-modelling |
| Huang--Stoll model | 10 | 05-decomposing-the-spread |
| Huber loss | 4 | 15-robust-statistics-and-heavy-tails |
| huge page | 13 | 03-memory-hierarchy-and-caches |
| Hull--White model | 6 | 07-short-rate-models |
| hurdle rate | 6 | 19-funding-margin-and-capital-adjustments |
| Hurst exponent | 4 | 17-linear-time-series |
| hybrid factor model | 7 | 24-risk-models |
| hyperparameter | 12 | 01-why-financial-machine-learning-is-different |
| hyperparameter search | 12 | 03-validation |
| hypothesis test | 4 | 12-testing-and-multiple-testing |
| hypothetical P\&L | 6 | 23-regulatory-capital-for-trading-books |
| hypothetical scenario | 6 | 22-stress-testing-and-scenarios |
| I-spread | 2 | 21-corporate-bonds |
| I-would price | 10 | 28-build-an-execution-algorithm |
| IC decay curve | 7 | 13-half-life-decay-and-stability |
| IC information ratio | 7 | 06-anatomy-of-a-predictor |
| IC stability | 7 | 13-half-life-decay-and-stability |
| IC-weighted blend | 7 | 14-signal-combination |
| iceberg order | 10 | 02-order-types-and-their-uses |
| idempotent processing | 13 | 24-resilience |
| identifiability | 4 | 24-numerical-optimisation-in-practice |
| identifier mapping | 7 | 04-universe-symbology-and-corporate-actions |
| idle state | 13 | 02-cpu-microarchitecture |
| imbalance bar | 7 | 02-market-data-for-research |
| imbalance price | 3 | 06-power-markets-trading |
| imbalance volume | 3 | 06-power-markets-trading |
| imbalance-offsetting order | 11 | 16-auctions-and-the-close |
| IMM date | 2 | 08-short-term-interest-rate-futures |
| immediate-or-cancel order | 10 | 02-order-types-and-their-uses |
| impact curve | 10 | 11-the-empirics-of-price-impact |
| impact prefactor | 10 | 11-the-empirics-of-price-impact |
| impact reversion | 10 | 11-the-empirics-of-price-impact |
| impermanent loss | 3 | 20-automated-market-makers |
| implementation shortfall | 7 | 19-simulation-versus-live |
| implementation-shortfall algorithm | 10 | 16-benchmark-algorithms |
| implicit scheme | 4 | 27-finite-difference-methods |
| implied borrow rate | 5 | 05-dividends-borrow-and-forwards |
| implied correlation | 5 | 17-multi-asset-options |
| implied deal probability | 8 | 11-merger-arbitrage |
| implied dividend | 5 | 05-dividends-borrow-and-forwards |
| implied equilibrium returns | 7 | 26-portfolio-construction-ii |
| implied financing rate | 1 | 21-basis-roll-and-delivery |
| implied move | 9 | 04-gamma-scalping-and-event-volatility |
| implied policy path | 2 | 08-short-term-interest-rate-futures |
| implied probability | 3 | 27-prediction-and-betting-markets |
| implied repo rate | 2 | 06-bond-futures |
| implied volatility | 1 | 25-volatility-first-contact |
| implied volatility spread | 8 | 15-options-implied-signals-for-stocks |
| implied--realised spread | 5 | 25-trading-volatility |
| implied-in | 1 | 19-matching-algorithms-and-implied-spreads |
| implied-out | 1 | 19-matching-algorithms-and-implied-spreads |
| implied-price arbitrage | 11 | 15-futures-market-making |
| importance sampling | 4 | 26-monte-carlo |
| impulse control | 4 | 10-optimal-stopping-and-impulse-control |
| impulse response function | 4 | 20-multivariate-series-and-cointegration |
| in the money | 1 | 23-option-contracts-and-exchanges |
| in-block priority rule | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| in-flight order | 13 | 21-order-gateway-and-order-management |
| in-kind transfer | 1 | 14-exchange-traded-funds |
| in-play betting | 3 | 27-prediction-and-betting-markets |
| in-sample | 7 | 20-overfitting |
| incentive programme | 1 | 30-getting-access-futures-options |
| Incoterms | 3 | 01-physical-commodity-markets |
| incremental channel | 13 | 16-protocols-ii-binary-exchange-protocols |
| incremental information coefficient | 7 | 12-alternative-and-text-data |
| incremental XVA | 6 | 20-the-valuation-adjustment-desk |
| independent amount | 6 | 17-counterparty-exposure |
| independent price verification | 6 | 27-pnl-explain-and-independent-price-verification |
| index arbitrage | 9 | 26-delta-one-and-dividends |
| index backtest decay | 9 | 27-quantitative-investment-strategies |
| index divisor | 1 | 08-shares-corporate-actions-indices |
| index effect | 1 | 15-index-construction-and-rebalancing |
| index fund | 8 | 10-index-rebalancing |
| index methodology | 1 | 15-index-construction-and-rebalancing |
| index point | 1 | 22-index-and-single-stock-futures-worldwide |
| index price | 3 | 17-perpetual-futures |
| index reconstitution | 1 | 15-index-construction-and-rebalancing |
| index series | 2 | 24-credit-indices-and-tranches |
| index skew | 2 | 24-credit-indices-and-tranches |
| index-linked bond | 2 | 11-inflation-markets |
| indexation lag | 2 | 11-inflation-markets |
| indexer | 3 | 26-crypto-data-and-infrastructure |
| indication of interest | 10 | 09-dark-pools-and-blocks |
| indicative NAV | 1 | 14-exchange-traded-funds |
| indicative price | 1 | 13-auctions |
| indifference price | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| individual conditional expectation | 12 | 21-interpretability-and-model-governance |
| industry factor | 7 | 24-risk-models |
| industry momentum | 8 | 05-momentum |
| industry-adjusted reversal | 8 | 02-short-term-reversal |
| infeasibility certificate | 4 | 23-convex-optimisation |
| inference latency | 12 | 26-low-latency-inference |
| infinitely divisible distribution | 4 | 06-jump-processes |
| infinitesimal generator | 4 | 04-stochastic-differential-equations |
| inflation cap | 6 | 11-inflation-derivatives |
| inflation seasonality | 2 | 11-inflation-markets |
| influence function | 4 | 15-robust-statistics-and-heavy-tails |
| information chasing | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| information coefficient | 7 | 06-anatomy-of-a-predictor |
| information criterion | 4 | 17-linear-time-series |
| information leakage | 10 | 09-dark-pools-and-blocks |
| information ratio | 1 | 03-the-buy-side |
| information share | 10 | 08-fragmentation-and-routing |
| informed options trading | 8 | 15-options-implied-signals-for-stocks |
| informed trader | 10 | 04-why-there-is-a-spread |
| ingestion pipeline | 12 | 15-alternative-data-pipelines |
| inhomogeneous Poisson process | 4 | 07-point-processes-and-hawkes-processes |
| initial margin | 1 | 05-clearing-and-settlement |
| initial-margin model | 6 | 25-margin-models |
| initial-margin threshold | 6 | 25-margin-models |
| injected clock | 13 | 20-the-strategy-engine |
| injection season | 3 | 04-natural-gas-and-lng |
| inlining | 13 | 07-cpp-for-latency-ii-compile-time |
| innovation | 4 | 19-state-space-models-and-the-kalman-filter |
| input journal | 13 | 23-logging-capture-and-replay |
| instantaneous forward rate | 6 | 01-curve-construction |
| instruction pipeline | 13 | 02-cpu-microarchitecture |
| instructions per cycle | 13 | 02-cpu-microarchitecture |
| instrumentation point | 13 | 26-build-tick-to-trade-measured |
| instrumented principal component analysis | 12 | 09-cross-sectional-deep-models |
| insurance fund | 3 | 18-margin-liquidation-and-loss-allocation |
| integrated variance | 4 | 18-volatility-models |
| intent-based routing | 3 | 20-automated-market-makers |
| inter-commodity spread credit | 1 | 20-margin |
| inter-dealer broker | 2 | 04-the-treasury-market |
| interbank offered rate | 2 | 01-central-banks-and-the-short-rate |
| interest-coverage test | 2 | 25-loans-clos-and-securitisation |
| interest-only strip | 6 | 12-mortgage-modelling |
| interest-rate risk in the banking book | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| interest-rate swap | 2 | 09-interest-rate-swaps |
| interference | 7 | 21-live-experiments |
| interior-point method | 4 | 23-convex-optimisation |
| intermarket signal | 8 | 22-cross-asset-lead-lag |
| intermarket sweep order | 1 | 09-us-equity-market-structure |
| internal crossing | 7 | 27-transaction-costs-in-research |
| internal models approach | 6 | 23-regulatory-capital-for-trading-books |
| internalisation | 1 | 10-retail-flow-and-wholesaling |
| internalisation rate | 11 | 23-retail-wholesaling |
| interpolation locality | 6 | 01-curve-construction |
| interpretability | 12 | 21-interpretability-and-model-governance |
| interrupt affinity | 13 | 13-linux-tuning |
| intraday alpha | 8 | 14-intraday-machine-learned-alphas |
| intraday margin call | 1 | 20-margin |
| intraday market | 3 | 06-power-markets-trading |
| intraday mean reversion | 8 | 25-short-term-futures-strategies |
| intraday return | 8 | 13-intraday-patterns |
| intraday seasonality | 7 | 05-stylised-facts-of-returns |
| intraday volume forecast | 10 | 16-benchmark-algorithms |
| intraday volume profile | 7 | 05-stylised-facts-of-returns |
| intrinsic spread | 2 | 24-credit-indices-and-tranches |
| intrinsic storage value | 6 | 16-commodity-and-energy-derivatives |
| intrinsic value | 1 | 23-option-contracts-and-exchanges |
| invariant time-stamp counter | 13 | 05-measuring-latency |
| inventory | 2 | 30-market-making-games |
| inventory bound | 11 | 04-extensions-of-the-inventory-framework |
| inventory P\&L | 7 | 23-measuring-market-making-and-execution |
| inventory penalty | 11 | 03-inventory-models |
| inventory-holding cost | 10 | 04-why-there-is-a-spread |
| inverse contract | 3 | 17-perpetual-futures |
| inverse option | 3 | 19-dated-futures-options-and-etfs |
| inverse transform sampling | 4 | 26-monte-carlo |
| inverted venue | 1 | 09-us-equity-market-structure |
| investment grade | 2 | 21-corporate-bonds |
| invoice price | 2 | 06-bond-futures |
| ISDA master agreement | 2 | 28-getting-access-rates-credit |
| ISDA standard model | 6 | 13-reduced-form-credit |
| isolated margin | 3 | 18-margin-liquidation-and-loss-allocation |
| isolation forest | 12 | 20-clustering-regimes-and-anomaly-detection |
| isotonic regression | 7 | 15-from-signal-to-forecast |
| Itô integral | 4 | 03-ito-calculus |
| Itô process | 4 | 03-ito-calculus |
| jackknife | 4 | 13-resampling |
| James--Stein estimator | 4 | 14-bayesian-methods |
| Jamshidian decomposition | 6 | 07-short-rate-models |
| Japan Korea Marker | 3 | 04-natural-gas-and-lng |
| Jarrow--Rudd tree | 5 | 02-the-binomial-model |
| Jarrow--Yildirim model | 6 | 11-inflation-derivatives |
| jelly roll | 11 | 20-options-cross-venue-and-volatility-arbitrage-at-speed |
| jitter | 13 | 01-where-latency-comes-from |
| Johansen test | 4 | 20-multivariate-series-and-cointegration |
| jump chain | 4 | 08-markov-chains-and-queues |
| jump condition | 5 | 22-trees-and-finite-difference-pricers-in-practice |
| jump-diffusion | 4 | 06-jump-processes |
| jump-to-default risk | 6 | 13-reduced-form-credit |
| just-in-time compilation | 13 | 10-managed-and-functional-languages-on-the-desk |
| just-in-time liquidity | 3 | 20-automated-market-makers |
| k-means | 12 | 20-clustering-regimes-and-anomaly-detection |
| Kalman filter | 4 | 19-state-space-models-and-the-kalman-filter |
| Kalman gain | 4 | 19-state-space-models-and-the-kalman-filter |
| Kalman smoother | 4 | 19-state-space-models-and-the-kalman-filter |
| Karush--Kuhn--Tucker conditions | 4 | 23-convex-optimisation |
| Kelly criterion | 2 | 29-thinking-in-expected-value |
| Kendall's tau | 4 | 15-robust-statistics-and-heavy-tails |
| kernel bypass | 13 | 13-linux-tuning |
| key-rate duration | 6 | 03-rates-risk |
| kill criterion | 7 | 01-the-research-process |
| kill switch | 11 | 27-risk-controls |
| kimchi premium | 3 | 16-spot-markets |
| kinked interest-rate curve | 3 | 23-defi-credit-and-leverage |
| Kirk's approximation | 6 | 16-commodity-and-energy-derivatives |
| knock-in option | 2 | 19-the-fx-options-market |
| knock-out option | 2 | 19-the-fx-options-market |
| know-your-customer check | 3 | 25-getting-access-crypto-venues |
| knowledge time | 7 | 03-point-in-time-data-and-the-biases |
| Kolmogorov backward equation | 4 | 04-stochastic-differential-equations |
| Kolmogorov forward equation | 4 | 04-stochastic-differential-equations |
| Kolmogorov--Smirnov test | 4 | 12-testing-and-multiple-testing |
| Kou model | 5 | 13-jumps-and-levy-models |
| Kullback--Leibler divergence | 4 | 11-estimation |
| Kupiec test | 6 | 21-market-risk-measures |
| Kyle model | 10 | 04-why-there-is-a-spread |
| Kyle's lambda | 7 | 09-trade-flow-features |
| label concurrency | 12 | 02-targets-labels-and-sample-weights |
| label overlap | 7 | 20-overfitting |
| Lagrangian | 4 | 23-convex-optimisation |
| language model | 12 | 14-large-language-models-in-finance |
| language-model agent | 12 | 14-large-language-models-in-finance |
| large homogeneous pool | 6 | 15-portfolio-credit |
| large language model | 12 | 14-large-language-models-in-finance |
| large-in-scale waiver | 1 | 11-european-equity-market-structure |
| large-tick asset | 10 | 06-tick-size-queues-and-priority |
| lasso | 4 | 16-linear-models-under-stress |
| last look | 2 | 15-fx-spot-microstructure |
| last trading day | 3 | 02-crude-oil |
| latency | 13 | 01-where-latency-comes-from |
| latency arbitrage | 11 | 09-latency-arbitrage-and-its-defence |
| latency attribution | 13 | 26-build-tick-to-trade-measured |
| latency budget | 13 | 01-where-latency-comes-from |
| latency histogram | 13 | 05-measuring-latency |
| latency model | 7 | 18-order-book-replay-simulation |
| latency race | 11 | 09-latency-arbitrage-and-its-defence |
| latent Dirichlet allocation | 12 | 13-text-from-bag-of-words-to-embeddings |
| latent liquidity | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| latent order book | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| law of one price | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| lay bet | 3 | 27-prediction-and-betting-markets |
| layer normalisation | 12 | 07-neural-networks-for-noisy-tabular-data |
| layering | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| LBMA Gold Price | 3 | 08-metals |
| lead market maker | 1 | 19-matching-algorithms-and-implied-spreads |
| lead--lag estimator | 7 | 10-cross-sectional-and-cross-asset-features |
| lead--lag relationship | 7 | 10-cross-sectional-and-cross-asset-features |
| leakage audit | 12 | 03-validation |
| learning rate | 12 | 05-trees-and-boosting |
| Lee moment formula | 5 | 08-parametrising-the-surface |
| Lee--Ready algorithm | 7 | 09-trade-flow-features |
| legal entity identifier | 2 | 28-getting-access-rates-credit |
| legging risk | 11 | 13-index-and-basket-arbitrage |
| Leisen--Reimer tree | 5 | 02-the-binomial-model |
| lendable supply | 1 | 16-stock-loan-and-short-selling |
| lending pool | 3 | 23-defi-credit-and-leverage |
| letter of credit | 3 | 13-getting-access-commodities-and-power |
| level 1 | 1 | 28-reading-market-data |
| level 2 | 1 | 28-reading-market-data |
| level 3 | 1 | 28-reading-market-data |
| level factor | 6 | 03-rates-risk |
| Levenberg--Marquardt algorithm | 4 | 24-numerical-optimisation-in-practice |
| leverage | 1 | 06-financing |
| leverage effect | 4 | 18-volatility-models |
| leverage function | 5 | 20-fx-derivatives |
| leverage rebalancing flow | 8 | 26-volatility-targeting-and-risk-managed-portfolios |
| leveraged ETF | 1 | 14-exchange-traded-funds |
| leveraged loan | 2 | 25-loans-clos-and-securitisation |
| Lewis formula | 5 | 24-fourier-pricing-and-calibration-engineering |
| liability-driven investment | 2 | 07-european-and-japanese-government-bonds |
| LIBOR market model | 6 | 08-forward-rate-and-market-models |
| likelihood function | 4 | 11-estimation |
| likelihood-ratio Greek | 5 | 23-monte-carlo-pricers-in-practice |
| likelihood-ratio test | 4 | 12-testing-and-multiple-testing |
| limit order | 10 | 01-the-limit-order-book |
| limit order book | 10 | 01-the-limit-order-book |
| limit up--limit down | 1 | 31-stress-case-studies |
| limit-hit continuation | 8 | 18-asia-specific-equity-strategies |
| limit-locked market | 3 | 09-agriculturals-and-softs |
| limit-on-close order | 1 | 13-auctions |
| limited price indexation | 6 | 11-inflation-derivatives |
| line arbitration | 13 | 16-protocols-ii-binary-exchange-protocols |
| line search | 4 | 24-numerical-optimisation-in-practice |
| linear contract | 3 | 17-perpetual-futures |
| linear cost model | 7 | 16-vectorised-backtests |
| linear filter | 7 | 07-price-and-volume-features |
| linear probe | 12 | 10-representation-learning |
| linear programme | 4 | 23-convex-optimisation |
| linear shrinkage | 4 | 22-covariance-estimation-and-random-matrices |
| linear terminal swap-rate model | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| link-time optimisation | 13 | 08-cpp-for-latency-iii-the-compiler |
| liquefied natural gas | 3 | 04-natural-gas-and-lng |
| liquid staking token | 3 | 23-defi-credit-and-leverage |
| liquidation absorption | 11 | 24-crypto-high-frequency-trading-on-centralised-venues |
| liquidation bonus | 3 | 23-defi-credit-and-leverage |
| liquidation cascade | 3 | 18-margin-liquidation-and-loss-allocation |
| liquidation engine | 3 | 18-margin-liquidation-and-loss-allocation |
| liquidation price | 3 | 18-margin-liquidation-and-loss-allocation |
| liquidity aggregator | 10 | 21-execution-beyond-equities |
| liquidity constraint | 7 | 25-portfolio-construction-i |
| liquidity coverage ratio | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| liquidity filter | 7 | 04-universe-symbology-and-corporate-actions |
| liquidity horizon | 6 | 23-regulatory-capital-for-trading-books |
| liquidity pool | 3 | 20-automated-market-makers |
| liquidity spiral | 1 | 31-stress-case-studies |
| liquidity tier | 2 | 15-fx-spot-microstructure |
| liquidity vault | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| liquidity-provider review | 2 | 27-getting-access-fx |
| live surface fit | 11 | 19-automated-options-market-making |
| LME lending rule | 3 | 08-metals |
| LME official price | 3 | 08-metals |
| load-out queue | 3 | 08-metals |
| loan line | 3 | 25-getting-access-crypto-venues |
| loan-plus-call structure | 3 | 24-the-crypto-trading-business |
| loan-to-value ratio | 3 | 23-defi-credit-and-leverage |
| local correlation | 5 | 17-multi-asset-options |
| local level model | 4 | 19-state-space-models-and-the-kalman-filter |
| local martingale | 4 | 03-ito-calculus |
| local volatility | 5 | 09-local-volatility |
| local volatility model | 5 | 09-local-volatility |
| locally linear order book | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| locate | 1 | 06-financing |
| location spread | 9 | 21-commodity-spreads |
| locational basis | 3 | 04-natural-gas-and-lng |
| locational marginal price | 3 | 05-power-markets-design |
| lock-free | 13 | 11-lock-free-programming |
| locked market | 10 | 08-fragmentation-and-routing |
| loco London | 3 | 08-metals |
| log contract | 5 | 14-variance-swaps-and-volatility-derivatives |
| log-moneyness | 5 | 07-implied-volatility-and-its-surface |
| logistic regression | 12 | 04-linear-and-regularised-baselines |
| lognormal volatility | 6 | 04-vanilla-rates-options |
| long memory | 4 | 17-linear-time-series |
| long short-term memory | 12 | 08-sequence-models-on-order-books |
| Longstaff--Schwartz method | 5 | 23-monte-carlo-pricers-in-practice |
| look-ahead bias | 7 | 03-point-in-time-data-and-the-biases |
| lookback option | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| loss given default | 6 | 13-reduced-form-credit |
| loss limit | 11 | 27-risk-controls |
| loss spiral | 3 | 28-when-markets-break-together |
| loss-versus-rebalancing | 3 | 20-automated-market-makers |
| lot size (derivatives) | 1 | 27-options-markets-europe-asia |
| low-discrepancy sequence | 4 | 26-monte-carlo |
| low-frequency spread estimator | 10 | 05-decomposing-the-spread |
| low-risk anomaly | 8 | 06-value-quality-and-low-risk |
| low-touch trading | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| LU factorisation | 4 | 25-floating-point-and-numerical-linear-algebra |
| Lévy measure | 4 | 06-jump-processes |
| Lévy process | 4 | 06-jump-processes |
| Lévy triplet | 4 | 06-jump-processes |
| M-estimator | 4 | 11-estimation |
| M-matrix | 4 | 27-finite-difference-methods |
| M/M/1 queue | 4 | 08-markov-chains-and-queues |
| Macaulay duration | 2 | 03-government-bonds |
| machine epsilon | 4 | 25-floating-point-and-numerical-linear-algebra |
| machine-learning engineer | 12 | 28-the-machine-learning-team |
| machine-learning platform | 12 | 28-the-machine-learning-team |
| machine-readable news | 8 | 17-news-and-events |
| macro momentum | 9 | 16-systematic-macro |
| macro value signal | 9 | 16-systematic-macro |
| Madhavan--Richardson--Roomans model | 10 | 05-decomposing-the-spread |
| magnet effect | 8 | 18-asia-specific-equity-strategies |
| maintenance margin | 1 | 20-margin |
| make-me-a-market | 2 | 30-market-making-games |
| maker-taker pricing | 1 | 09-us-equity-market-structure |
| managed money | 3 | 09-agriculturals-and-softs |
| management fee | 1 | 03-the-buy-side |
| mandate | 1 | 03-the-buy-side |
| Marchenko--Pastur law | 4 | 22-covariance-estimation-and-random-matrices |
| margin call | 1 | 06-financing |
| margin period of risk | 1 | 20-margin |
| margin spiral | 3 | 28-when-markets-break-together |
| margin valuation adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| marginal fee | 11 | 17-rebates-inverted-venues-and-tiers |
| marine fuel sulphur cap | 3 | 03-refined-products-and-cracks |
| mark price | 3 | 17-perpetual-futures |
| mark-out | 2 | 15-fx-spot-microstructure |
| mark-out curve | 7 | 23-measuring-market-making-and-execution |
| mark-to-market | 1 | 07-pnl-and-positions |
| market access rule | 11 | 27-risk-controls |
| market beta | 7 | 22-performance-measurement |
| market capitalisation | 1 | 08-shares-corporate-actions-indices |
| market coupling | 3 | 05-power-markets-design |
| market data feed | 1 | 04-exchanges-brokers-venues |
| market fragmentation | 10 | 08-fragmentation-and-routing |
| market impact | 7 | 18-order-book-replay-simulation |
| market maker | 1 | 01-what-a-trading-firm-does |
| market order | 10 | 01-the-limit-order-book |
| market quality | 10 | 24-market-quality-and-regulation |
| market stability reserve | 3 | 07-emissions-and-environmental-markets |
| market time unit | 3 | 05-power-markets-design |
| market-based rate authorisation | 3 | 13-getting-access-commodities-and-power |
| market-by-order | 1 | 19-matching-algorithms-and-implied-spreads |
| market-by-price | 1 | 19-matching-algorithms-and-implied-spreads |
| market-data latency | 7 | 18-order-book-replay-simulation |
| market-data snapshot | 5 | 28-build-a-pricing-library |
| market-maker appointment | 1 | 30-getting-access-futures-options |
| market-making agent | 10 | 27-build-an-agent-based-market |
| market-on-close order | 1 | 13-auctions |
| market-wide circuit breaker | 1 | 31-stress-case-studies |
| marketable limit order | 10 | 02-order-types-and-their-uses |
| marketing fee | 1 | 24-options-market-structure |
| Markets in Crypto-Assets Regulation | 3 | 24-the-crypto-trading-business |
| marking the close | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| Markov chain | 4 | 08-markov-chains-and-queues |
| Markov chain Monte Carlo | 4 | 14-bayesian-methods |
| Markov decision process | 12 | 17-reinforcement-learning-foundations |
| Markov process | 4 | 02-brownian-motion |
| Markovian projection | 5 | 09-local-volatility |
| martingale | 4 | 01-probability-at-speed |
| mass cancel | 13 | 22-pre-trade-risk-and-kill-switches |
| mass quote | 11 | 19-automated-options-market-making |
| matching engine | 10 | 01-the-limit-order-book |
| material non-public information | 7 | 12-alternative-and-text-data |
| materialisation | 12 | 24-data-and-feature-stores |
| maximal extractable value | 3 | 22-maximal-extractable-value |
| maximum drawdown | 7 | 22-performance-measurement |
| maximum likelihood estimator | 4 | 11-estimation |
| maximum-ICIR blend | 7 | 14-signal-combination |
| mean decrease in impurity | 12 | 06-feature-engineering-selection-and-importance |
| mean reversion | 4 | 04-stochastic-differential-equations |
| mean--variance optimisation | 7 | 25-portfolio-construction-i |
| mean-reversion speed filter | 8 | 03-residual-and-principal-component-stat-arb |
| measurement overhead | 13 | 05-measuring-latency |
| median absolute deviation | 4 | 15-robust-statistics-and-heavy-tails |
| member rate | 1 | 30-getting-access-futures-options |
| membership prediction | 8 | 10-index-rebalancing |
| memorisation | 12 | 14-large-language-models-in-finance |
| memory coupon | 5 | 18-autocallables |
| memory locking | 13 | 13-linux-tuning |
| memory ordering | 13 | 11-lock-free-programming |
| memory-mapped dataset | 12 | 23-training-infrastructure |
| mempool | 3 | 14-blockchains-for-traders |
| merger arbitrage | 8 | 11-merger-arbitrage |
| merit order | 3 | 05-power-markets-design |
| Merton fraction | 4 | 09-stochastic-control |
| Merton jump-diffusion model | 5 | 13-jumps-and-levy-models |
| Merton model | 6 | 14-structural-credit-models |
| message burst | 13 | 18-the-feed-handler |
| message gap | 13 | 16-protocols-ii-binary-exchange-protocols |
| message throttle | 11 | 10-the-quoting-engine |
| meta-labelling | 12 | 02-targets-labels-and-sample-weights |
| metaorder | 7 | 09-trade-flow-features |
| method of lines | 4 | 27-finite-difference-methods |
| method of moments | 4 | 11-estimation |
| method of simulated moments | 10 | 27-build-an-agent-based-market |
| Metropolis--Hastings algorithm | 4 | 14-bayesian-methods |
| MEV relay | 3 | 22-maximal-extractable-value |
| micro contract | 1 | 22-index-and-single-stock-futures-worldwide |
| microbenchmark | 13 | 02-cpu-microarchitecture |
| microprice | 7 | 08-order-book-features |
| microstructure noise | 4 | 21-high-frequency-econometrics |
| mid price | 1 | 01-what-a-trading-firm-does |
| middle distillates | 3 | 03-refined-products-and-cracks |
| midpoint peg | 10 | 02-order-types-and-their-uses |
| midquote series | 7 | 02-market-data-for-research |
| Milstein scheme | 4 | 26-monte-carlo |
| Mincer--Zarnowitz regression | 4 | 18-volatility-models |
| mini contract | 1 | 22-index-and-single-stock-futures-worldwide |
| mini-batch | 12 | 07-neural-networks-for-noisy-tabular-data |
| minimum backtest length | 7 | 20-overfitting |
| minimum detectable effect | 7 | 21-live-experiments |
| minimum execution quantity | 10 | 09-dark-pools-and-blocks |
| minimum transfer amount | 6 | 17-counterparty-exposure |
| minimum-variance delta | 5 | 11-sabr-and-smile-dynamics |
| minimum-variance portfolio | 4 | 22-covariance-estimation-and-random-matrices |
| mixed dividend model | 5 | 05-dividends-borrow-and-forwards |
| mixed strategy | 4 | 29-games-auctions-and-information |
| mixed-precision training | 12 | 23-training-infrastructure |
| mixing formula | 5 | 10-stochastic-volatility |
| mixture density network | 12 | 11-probabilistic-models-and-uncertainty |
| mode collapse | 12 | 16-generative-models-and-synthetic-data |
| model artefact | 12 | 25-experiment-tracking-and-reproducibility |
| model card | 12 | 21-interpretability-and-model-governance |
| model compilation | 12 | 26-low-latency-inference |
| model inventory | 6 | 26-model-risk-and-validation |
| model lineage | 12 | 25-experiment-tracking-and-reproducibility |
| model monitoring | 12 | 27-monitoring-and-retraining |
| model owner | 12 | 28-the-machine-learning-team |
| model parallelism | 12 | 23-training-infrastructure |
| model registry | 12 | 25-experiment-tracking-and-reproducibility |
| model reserve | 5 | 27-managing-an-exotic-book |
| model risk | 6 | 26-model-risk-and-validation |
| model risk management | 6 | 26-model-risk-and-validation |
| model selection | 12 | 03-validation |
| model tiering | 6 | 26-model-risk-and-validation |
| model validation | 6 | 26-model-risk-and-validation |
| modified duration | 2 | 03-government-bonds |
| momentum crash | 8 | 05-momentum |
| momentum ignition | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| momentum method | 4 | 24-numerical-optimisation-in-practice |
| money-market account | 4 | 05-girsanov-and-changes-of-numeraire |
| money-market fund | 2 | 02-money-markets |
| money-market yield | 2 | 02-money-markets |
| monotone convex interpolation | 6 | 01-curve-construction |
| monotone cubic interpolation | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| monotonic constraint | 12 | 05-trees-and-boosting |
| Monte Carlo method | 4 | 26-monte-carlo |
| Monte Carlo value at risk | 6 | 21-market-risk-measures |
| month-end rebalancing | 2 | 17-fixings-and-flows |
| moving-average crossover | 7 | 07-price-and-volume-features |
| moving-average process | 4 | 17-linear-time-series |
| moving-block bootstrap | 4 | 13-resampling |
| multi-armed bandit | 12 | 17-reinforcement-learning-foundations |
| multi-asset market making | 11 | 04-extensions-of-the-inventory-framework |
| multi-curve framework | 6 | 02-multi-curve-and-collateral-discounting |
| multi-manager platform | 1 | 01-what-a-trading-firm-does |
| multi-party computation | 3 | 24-the-crypto-trading-business |
| multi-period optimisation | 7 | 26-portfolio-construction-ii |
| multi-strategy book | 8 | 28-running-a-multi-strategy-book |
| multicast | 13 | 16-protocols-ii-binary-exchange-protocols |
| multicollinearity | 4 | 16-linear-models-under-stress |
| multilateral trading facility | 1 | 04-exchanges-brokers-venues |
| multilayer perceptron | 12 | 07-neural-networks-for-noisy-tabular-data |
| multilevel Monte Carlo | 4 | 26-monte-carlo |
| multiple testing | 4 | 12-testing-and-multiple-testing |
| multistart | 4 | 24-numerical-optimisation-in-practice |
| multivariate Hawkes process | 4 | 07-point-processes-and-hawkes-processes |
| mutual information | 4 | 29-games-auctions-and-information |
| n-gram | 12 | 13-text-from-bag-of-words-to-embeddings |
| naked short sale | 1 | 16-stock-loan-and-short-selling |
| name limit | 7 | 25-portfolio-construction-i |
| named-entity recognition | 12 | 13-text-from-bag-of-words-to-embeddings |
| Nash equilibrium | 4 | 29-games-auctions-and-information |
| national best bid and offer | 1 | 09-us-equity-market-structure |
| natural cubic spline | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| nearest correlation matrix | 4 | 23-convex-optimisation |
| negative basis trade | 9 | 18-credit-relative-value |
| negative convexity | 2 | 12-mortgages-and-agencies |
| Nelson--Siegel curve | 6 | 01-curve-construction |
| nested cross-validation | 12 | 03-validation |
| Nesterov acceleration | 4 | 24-numerical-optimisation-in-practice |
| net asset value | 1 | 14-exchange-traded-funds |
| net basis | 2 | 06-bond-futures |
| net capture | 1 | 01-what-a-trading-firm-does |
| net exposure | 1 | 07-pnl-and-positions |
| net interest income sensitivity | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| net open position limit | 2 | 27-getting-access-fx |
| net stable funding ratio | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| netback | 3 | 01-physical-commodity-markets |
| netting set | 6 | 17-counterparty-exposure |
| neural network | 12 | 07-neural-networks-for-noisy-tabular-data |
| neutralisation | 7 | 06-anatomy-of-a-predictor |
| new crop | 3 | 09-agriculturals-and-softs |
| new-issue concession | 2 | 21-corporate-bonds |
| news reaction window | 8 | 17-news-and-events |
| Newton's method | 4 | 24-numerical-optimisation-in-practice |
| no-dynamic-arbitrage condition | 10 | 12-transient-impact-and-propagator-models |
| no-touch option | 5 | 15-barriers-and-digitals |
| no-trade region | 4 | 10-optimal-stopping-and-impulse-control |
| noise trader | 10 | 04-why-there-is-a-spread |
| non-deliverable forward | 2 | 18-emerging-market-fx-and-ndfs |
| non-display fee | 1 | 29-getting-access-equities |
| non-execution risk | 10 | 17-child-order-placement |
| non-maturity deposit | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| non-modellable risk factor | 6 | 23-regulatory-capital-for-trading-books |
| non-synchronous trading | 4 | 21-high-frequency-econometrics |
| non-uniform grid | 4 | 27-finite-difference-methods |
| non-uniform memory access | 13 | 04-multi-socket-machines-and-interconnects |
| nonlinear least squares | 4 | 24-numerical-optimisation-in-practice |
| nonlinear shrinkage | 4 | 22-covariance-estimation-and-random-matrices |
| normal SABR | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| normal volatility | 2 | 13-the-rates-options-market |
| normal-form game | 4 | 29-games-auctions-and-information |
| normalisation | 1 | 28-reading-market-data |
| northbound flow | 8 | 18-asia-specific-equity-strategies |
| notional | 1 | 07-pnl-and-positions |
| notional turnover | 1 | 27-options-markets-europe-asia |
| novation | 1 | 05-clearing-and-settlement |
| Novikov's condition | 4 | 05-girsanov-and-changes-of-numeraire |
| nowcast | 8 | 16-alternative-data-strategies |
| null hypothesis | 4 | 12-testing-and-multiple-testing |
| NUMA node | 13 | 04-multi-socket-machines-and-interconnects |
| numeraire | 4 | 05-girsanov-and-changes-of-numeraire |
| Obizhaeva--Wang model | 10 | 12-transient-impact-and-propagator-models |
| object pool | 13 | 06-cpp-for-latency-i-memory |
| odd lot | 1 | 09-us-equity-market-structure |
| odds | 2 | 29-thinking-in-expected-value |
| off-exchange settlement | 3 | 15-centralised-exchanges |
| off-heap memory | 13 | 10-managed-and-functional-languages-on-the-desk |
| off-policy evaluation | 12 | 17-reinforcement-learning-foundations |
| off-the-run | 2 | 04-the-treasury-market |
| official selling price | 3 | 02-crude-oil |
| offline store | 12 | 24-data-and-feature-stores |
| offshore market | 2 | 18-emerging-market-fx-and-ndfs |
| oil indexation | 3 | 04-natural-gas-and-lng |
| old crop | 3 | 09-agriculturals-and-softs |
| Omega ratio | 7 | 22-performance-measurement |
| on-chain order book | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| on-chain signal | 8 | 27-crypto-medium-frequency-strategies |
| on-the-run | 2 | 04-the-treasury-market |
| on-the-run premium | 9 | 13-supply-trades |
| one-touch option | 5 | 15-barriers-and-digitals |
| online learning | 12 | 12-online-learning-and-drift |
| online store | 12 | 24-data-and-feature-stores |
| onshore market | 2 | 18-emerging-market-fx-and-ndfs |
| open addressing | 13 | 19-the-order-book-builder |
| open interest | 1 | 18-futures-contracts-and-exchanges |
| open-interest cap | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| open-market operation | 2 | 01-central-banks-and-the-short-rate |
| opening range breakout | 8 | 25-short-term-futures-strategies |
| operational loss event | 6 | 28-operational-risk-and-rogue-trading |
| operational risk | 6 | 28-operational-risk-and-rogue-trading |
| operator fusion | 12 | 26-low-latency-inference |
| opportunity cost | 7 | 23-measuring-market-making-and-execution |
| OPRA | 1 | 24-options-market-structure |
| optimal stopping problem | 4 | 10-optimal-stopping-and-impulse-control |
| option cost | 6 | 12-mortgage-modelling |
| option cut | 2 | 17-fixings-and-flows |
| option multiplier | 1 | 23-option-contracts-and-exchanges |
| option overwriting | 9 | 01-harvesting-the-variance-risk-premium |
| option premium | 1 | 23-option-contracts-and-exchanges |
| option series | 1 | 23-option-contracts-and-exchanges |
| option-adjusted spread | 2 | 21-corporate-bonds |
| option-to-stock volume ratio | 8 | 15-options-implied-signals-for-stocks |
| options market maker | 1 | 24-options-market-structure |
| oracle | 3 | 14-blockchains-for-traders |
| oracle manipulation | 3 | 23-defi-credit-and-leverage |
| oracle-priced exchange | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| order | 1 | 04-exchanges-brokers-venues |
| order gateway | 13 | 21-order-gateway-and-order-management |
| order imbalance | 1 | 13-auctions |
| order lifecycle | 7 | 17-event-driven-backtests |
| order lifetime | 10 | 03-empirical-facts-of-order-books |
| order management system | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| order placement problem | 10 | 17-child-order-placement |
| order protection rule | 1 | 09-us-equity-market-structure |
| order state machine | 13 | 21-order-gateway-and-order-management |
| order-book event | 10 | 01-the-limit-order-book |
| order-book replay | 7 | 18-order-book-replay-simulation |
| order-entry latency | 7 | 18-order-book-replay-simulation |
| order-entry protocol | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| order-entry session | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| order-flow auction | 3 | 22-maximal-extractable-value |
| order-flow imbalance | 7 | 08-order-book-features |
| order-processing cost | 10 | 04-why-there-is-a-spread |
| order-sign autocorrelation | 7 | 09-trade-flow-features |
| order-to-trade ratio | 10 | 24-market-quality-and-regulation |
| ordinary least squares | 4 | 16-linear-models-under-stress |
| organised trading facility | 1 | 11-european-equity-market-structure |
| Ornstein--Uhlenbeck process | 4 | 04-stochastic-differential-equations |
| orthogonalisation | 7 | 14-signal-combination |
| out-of-bag error | 12 | 05-trees-and-boosting |
| out-of-order execution | 13 | 02-cpu-microarchitecture |
| out-of-sample | 7 | 20-overfitting |
| out-of-sample R-squared | 12 | 01-why-financial-machine-learning-is-different |
| outcomes analysis | 6 | 26-model-risk-and-validation |
| outright forward | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| over-quoting | 11 | 15-futures-market-making |
| over-the-counter search model | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| overcollateralisation test | 2 | 25-loans-clos-and-securitisation |
| overfitting | 12 | 01-why-financial-machine-learning-is-different |
| overnight benchmark rate | 2 | 01-central-banks-and-the-short-rate |
| overnight index swap | 2 | 09-interest-rate-swaps |
| overnight return | 8 | 13-intraday-patterns |
| overnight reversal | 8 | 02-short-term-reversal |
| overnight-rate future | 2 | 08-short-term-interest-rate-futures |
| overround | 3 | 27-prediction-and-betting-markets |
| p-value | 4 | 12-testing-and-multiple-testing |
| P\&L attribution | 1 | 07-pnl-and-positions |
| P\&L attribution test | 6 | 23-regulatory-capital-for-trading-books |
| pack | 2 | 08-short-term-interest-rate-futures |
| page fault | 13 | 06-cpp-for-latency-i-memory |
| Page--Hinkley test | 12 | 12-online-learning-and-drift |
| pairs trading | 8 | 04-pairs-and-baskets |
| panel bias | 12 | 15-alternative-data-pipelines |
| panel data | 4 | 16-linear-models-under-stress |
| panel drift | 7 | 12-alternative-and-text-data |
| panel reweighting | 12 | 15-alternative-data-pipelines |
| paper market | 3 | 01-physical-commodity-markets |
| paper trading | 7 | 21-live-experiments |
| par | 2 | 03-government-bonds |
| par swap rate | 2 | 09-interest-rate-swaps |
| par yield | 2 | 03-government-bonds |
| parameter bid--offer | 5 | 27-managing-an-exotic-book |
| parameter change control | 11 | 28-pnl-analytics-and-the-strategy-lifecycle |
| parametric portfolio policy | 12 | 22-from-prediction-to-portfolio |
| parametric value at risk | 6 | 21-market-risk-measures |
| parent order | 10 | 14-the-almgren-chriss-framework |
| pari passu clause | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| Parkinson estimator | 7 | 07-price-and-volume-features |
| partial autocorrelation function | 4 | 17-linear-time-series |
| partial basket | 11 | 13-index-and-basket-arbitrage |
| partial dependence | 12 | 21-interpretability-and-model-governance |
| partial fill | 7 | 17-event-driven-backtests |
| partial least squares | 12 | 04-linear-and-regularised-baselines |
| participation algorithm | 10 | 16-benchmark-algorithms |
| participation band | 10 | 28-build-an-execution-algorithm |
| participation rate | 5 | 19-the-structured-products-business |
| particle filter | 4 | 19-state-space-models-and-the-kalman-filter |
| pass-through | 2 | 12-mortgages-and-agencies |
| passive fill probability | 7 | 18-order-book-replay-simulation |
| passive management | 1 | 03-the-buy-side |
| path-dependent volatility model | 5 | 12-rough-volatility-and-forward-variance-models |
| pathwise Greek | 5 | 23-monte-carlo-pricers-in-practice |
| pay-as-bid auction | 4 | 29-games-auctions-and-information |
| payer swap | 2 | 09-interest-rate-swaps |
| payer swaption | 2 | 13-the-rates-options-market |
| payment for order flow | 1 | 10-retail-flow-and-wholesaling |
| payment netting | 2 | 20-settlement-risk |
| payment versus payment | 2 | 20-settlement-risk |
| payment waterfall | 2 | 25-loans-clos-and-securitisation |
| payoff smoothing | 5 | 22-trees-and-finite-difference-pricers-in-practice |
| PCI Express | 13 | 04-multi-socket-machines-and-interconnects |
| peak impact | 10 | 11-the-empirics-of-price-impact |
| peaks over threshold | 4 | 15-robust-statistics-and-heavy-tails |
| peer group | 7 | 10-cross-sectional-and-cross-asset-features |
| peer-relative return | 7 | 10-cross-sectional-and-cross-asset-features |
| peer-universe comparison | 10 | 19-transaction-cost-analysis |
| pegged order | 10 | 02-order-types-and-their-uses |
| penetration fill | 7 | 17-event-driven-backtests |
| penny program | 1 | 24-options-market-structure |
| percentage of volume | 7 | 27-transaction-costs-in-research |
| performance alarm | 12 | 27-monitoring-and-retraining |
| performance bond | 1 | 20-margin |
| performance fee | 1 | 03-the-buy-side |
| performance regression gate | 13 | 25-testing-and-deploying-low-latency-systems |
| periodic auction | 1 | 11-european-equity-market-structure |
| periodogram | 4 | 17-linear-time-series |
| permanent identifier | 7 | 04-universe-symbology-and-corporate-actions |
| permanent impact | 7 | 27-transaction-costs-in-research |
| permutation importance | 12 | 06-feature-engineering-selection-and-importance |
| permutation test | 4 | 13-resampling |
| permutation-invariant network | 12 | 09-cross-sectional-deep-models |
| perpetual DEX | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| perpetual future | 3 | 17-perpetual-futures |
| persistent connection | 13 | 17-websocket-rest-tls-and-json-at-speed |
| physical delivery | 1 | 21-basis-roll-and-delivery |
| physical market | 3 | 01-physical-commodity-markets |
| pillar | 6 | 01-curve-construction |
| pin risk | 1 | 23-option-contracts-and-exchanges |
| pinball loss | 12 | 11-probabilistic-models-and-uncertainty |
| pinging order | 10 | 09-dark-pools-and-blocks |
| pinning | 9 | 06-zero-day-options-and-dealer-gamma-flows |
| pip | 2 | 14-the-fx-market |
| pipeline stage | 7 | 29-build-a-research-workflow |
| pod | 8 | 28-running-a-multi-strategy-book |
| point of non-viability | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| point process | 4 | 07-point-processes-and-hawkes-processes |
| point-in-time data | 7 | 03-point-in-time-data-and-the-biases |
| Poisson process | 4 | 06-jump-processes |
| policy | 12 | 17-reinforcement-learning-foundations |
| policy gradient | 12 | 17-reinforcement-learning-foundations |
| policy rate | 2 | 01-central-banks-and-the-short-rate |
| pooled panel model | 12 | 09-cross-sectional-deep-models |
| population stability index | 12 | 27-monitoring-and-retraining |
| portfolio margining | 1 | 20-margin |
| portfolio trade | 2 | 22-how-bonds-trade |
| portfolio turnover | 7 | 16-vectorised-backtests |
| porting | 2 | 10-swap-clearing-and-the-ccp-basis |
| position | 1 | 07-pnl-and-positions |
| position limit | 1 | 27-options-markets-europe-asia |
| positioning signal | 8 | 24-positioning-and-sentiment |
| post-earnings-announcement drift | 8 | 07-earnings |
| post-model adjustment | 6 | 26-model-risk-and-validation |
| post-only order | 3 | 15-centralised-exchanges |
| post-publication decay | 7 | 13-half-life-decay-and-stability |
| post-trade reversion | 10 | 19-transaction-cost-analysis |
| post-training quantisation | 12 | 26-low-latency-inference |
| posterior distribution | 4 | 14-bayesian-methods |
| posterior predictive distribution | 4 | 14-bayesian-methods |
| potential future exposure | 6 | 17-counterparty-exposure |
| power of a test | 4 | 12-testing-and-multiple-testing |
| power purchase agreement | 3 | 06-power-markets-trading |
| pre-announcement drift | 8 | 25-short-term-futures-strategies |
| pre-averaging estimator | 4 | 21-high-frequency-econometrics |
| pre-faulting | 13 | 06-cpp-for-latency-i-memory |
| pre-registration | 7 | 01-the-research-process |
| pre-release | 11 | 14-depositary-receipts-and-dual-listings |
| pre-trade cost estimate | 10 | 19-transaction-cost-analysis |
| pre-trade risk check | 11 | 27-risk-controls |
| pre-training | 12 | 10-representation-learning |
| precision--recall curve | 12 | 20-clustering-regimes-and-anomaly-detection |
| preconditioner | 4 | 25-floating-point-and-numerical-linear-algebra |
| predict-then-optimise | 12 | 22-from-prediction-to-portfolio |
| predictability ceiling | 12 | 01-why-financial-machine-learning-is-different |
| prediction drift | 12 | 27-monitoring-and-retraining |
| prediction horizon | 8 | 14-intraday-machine-learned-alphas |
| prediction target | 7 | 06-anatomy-of-a-predictor |
| prediction-error decomposition | 4 | 19-state-space-models-and-the-kalman-filter |
| predictive distribution | 12 | 11-probabilistic-models-and-uncertainty |
| predictor | 7 | 06-anatomy-of-a-predictor |
| predictor card | 7 | 06-anatomy-of-a-predictor |
| premium | 1 | 14-exchange-traded-funds |
| premium index | 3 | 17-perpetual-futures |
| premium turnover | 1 | 27-options-markets-europe-asia |
| premium-adjusted delta | 2 | 19-the-fx-options-market |
| prepayment | 2 | 12-mortgages-and-agencies |
| prepayment model | 6 | 12-mortgage-modelling |
| prepayment S-curve | 6 | 12-mortgage-modelling |
| prepayment trade | 9 | 20-mortgage-and-structured-credit-strategies |
| prepositioned inventory | 3 | 16-spot-markets |
| price alignment interest | 6 | 02-multi-curve-and-collateral-discounting |
| price collar | 11 | 27-risk-controls |
| price differential | 3 | 01-physical-commodity-markets |
| price discovery | 10 | 08-fragmentation-and-routing |
| price improvement | 1 | 10-retail-flow-and-wholesaling |
| price level | 10 | 01-the-limit-order-book |
| price limit | 1 | 12-asian-and-emerging-equity-markets |
| price pressure | 8 | 09-flows |
| price-improvement auction | 1 | 24-options-market-structure |
| price-reporting agency | 3 | 01-physical-commodity-markets |
| price-time priority | 1 | 19-matching-algorithms-and-implied-spreads |
| pricing basket | 11 | 12-etf-market-making |
| pricing engine | 5 | 28-build-a-pricing-library |
| pricing period | 3 | 01-physical-commodity-markets |
| primary dealer | 2 | 04-the-treasury-market |
| primary venue | 2 | 14-the-fx-market |
| primary--backup replication | 13 | 24-resilience |
| primary--secondary spread | 6 | 12-mortgage-modelling |
| prime broker | 1 | 06-financing |
| prime services | 1 | 02-the-sell-side |
| prime-of-prime | 2 | 27-getting-access-fx |
| principal | 1 | 01-what-a-trading-firm-does |
| principal component analysis | 4 | 22-covariance-estimation-and-random-matrices |
| principal component regression | 12 | 04-linear-and-regularised-baselines |
| principal-only strip | 6 | 12-mortgage-modelling |
| prior distribution | 4 | 14-bayesian-methods |
| priority fee | 3 | 14-blockchains-for-traders |
| priority gas auction | 3 | 22-maximal-extractable-value |
| priority inversion | 13 | 11-lock-free-programming |
| private key | 3 | 14-blockchains-for-traders |
| private order flow | 3 | 22-maximal-extractable-value |
| private-value auction | 4 | 29-games-auctions-and-information |
| pro-forma index | 1 | 15-index-construction-and-rebalancing |
| pro-rata allocation | 1 | 19-matching-algorithms-and-implied-spreads |
| probability of backtest overfitting | 7 | 20-overfitting |
| probability of default | 6 | 13-reduced-form-credit |
| probability of informed trading | 10 | 04-why-there-is-a-spread |
| processing-spread trade | 9 | 21-commodity-spreads |
| procyclicality | 1 | 20-margin |
| product control | 6 | 27-pnl-explain-and-independent-price-verification |
| product slate | 3 | 03-refined-products-and-cracks |
| profile-guided optimisation | 13 | 08-cpp-for-latency-iii-the-compiler |
| profit factor | 7 | 22-performance-measurement |
| profit-maximising size | 7 | 28-capacity-decay-and-crowding |
| profitability factor | 8 | 06-value-quality-and-low-risk |
| projection curve | 6 | 02-multi-curve-and-collateral-discounting |
| prompt | 12 | 14-large-language-models-in-finance |
| prompt date | 3 | 08-metals |
| proof of liabilities | 3 | 15-centralised-exchanges |
| proof of reserves | 3 | 15-centralised-exchanges |
| proof of stake | 3 | 14-blockchains-for-traders |
| proof of work | 3 | 14-blockchains-for-traders |
| propagator model | 10 | 12-transient-impact-and-propagator-models |
| proper scoring rule | 12 | 11-probabilistic-models-and-uncertainty |
| property-based test | 13 | 25-testing-and-deploying-low-latency-systems |
| proportional dividend | 5 | 05-dividends-borrow-and-forwards |
| proposer--builder separation | 3 | 22-maximal-extractable-value |
| proprietary trading firm | 1 | 01-what-a-trading-firm-does |
| protected quote | 10 | 08-fragmentation-and-routing |
| protection barrier | 5 | 18-autocallables |
| protection buyer | 2 | 23-credit-default-swaps |
| protection seller | 2 | 23-credit-default-swaps |
| proximal gradient method | 4 | 24-numerical-optimisation-in-practice |
| proximal operator | 4 | 24-numerical-optimisation-in-practice |
| proxy credit spread | 6 | 20-the-valuation-adjustment-desk |
| prudent valuation | 6 | 27-pnl-explain-and-independent-price-verification |
| PSA benchmark | 2 | 12-mortgages-and-agencies |
| pseudo-random number generator | 4 | 26-monte-carlo |
| purging | 7 | 20-overfitting |
| put option | 1 | 23-option-contracts-and-exchanges |
| put--call parity | 1 | 25-volatility-first-contact |
| put--call ratio | 8 | 15-options-implied-signals-for-stocks |
| Q-learning | 12 | 17-reinforcement-learning-foundations |
| QLIKE loss | 4 | 18-volatility-models |
| QR factorisation | 4 | 25-floating-point-and-numerical-linear-algebra |
| quadratic approximation | 5 | 06-american-options-and-early-exercise |
| quadratic covariation | 4 | 03-ito-calculus |
| quadratic programme | 4 | 23-convex-optimisation |
| quadratic variation | 4 | 02-brownian-motion |
| quadratic-exponential scheme | 5 | 23-monte-carlo-pricers-in-practice |
| qualified foreign investor | 1 | 12-asian-and-emerging-equity-markets |
| quality factor | 8 | 06-value-quality-and-low-risk |
| quality option | 2 | 06-bond-futures |
| quality spread | 9 | 21-commodity-spreads |
| quantile regression | 12 | 11-probabilistic-models-and-uncertainty |
| quantile spread | 7 | 06-anatomy-of-a-predictor |
| quantisation | 12 | 26-low-latency-inference |
| quantisation-aware training | 12 | 26-low-latency-inference |
| quantitative easing | 2 | 01-central-banks-and-the-short-rate |
| quantitative investment strategy | 9 | 27-quantitative-investment-strategies |
| quanto adjustment | 5 | 17-multi-asset-options |
| quanto contract | 3 | 17-perpetual-futures |
| quanto option | 5 | 17-multi-asset-options |
| quasi-maximum likelihood | 4 | 11-estimation |
| quasi-Monte Carlo | 4 | 26-monte-carlo |
| quasi-Newton method | 4 | 24-numerical-optimisation-in-practice |
| quasi-variational inequality | 4 | 10-optimal-stopping-and-impulse-control |
| queue depletion rate | 7 | 08-order-book-features |
| queue imbalance | 7 | 08-order-book-features |
| queue position | 7 | 18-order-book-replay-simulation |
| queue value | 10 | 06-tick-size-queues-and-priority |
| queue-aware placement | 10 | 17-child-order-placement |
| queue-exit rule | 11 | 05-queue-reactive-models-and-large-tick-assets |
| queue-join rule | 11 | 05-queue-reactive-models-and-large-tick-assets |
| queue-position model | 7 | 18-order-book-replay-simulation |
| queue-reactive model | 11 | 05-queue-reactive-models-and-large-tick-assets |
| quote currency | 2 | 14-the-fx-market |
| quote fade | 10 | 18-smart-order-routing |
| quote ladder | 11 | 10-the-quoting-engine |
| quote protection | 1 | 24-options-market-structure |
| quote rule | 7 | 09-trade-flow-features |
| quote skewing | 2 | 15-fx-spot-microstructure |
| quoted depth | 3 | 16-spot-markets |
| quoted spread | 10 | 05-decomposing-the-spread |
| quoting obligation | 1 | 24-options-market-structure |
| Radon--Nikodym derivative | 4 | 01-probability-at-speed |
| random end | 10 | 10-auction-mechanics-and-theory |
| random forest | 12 | 05-trees-and-boosting |
| randomisation unit | 7 | 21-live-experiments |
| randomised quasi-Monte Carlo | 4 | 26-monte-carlo |
| range-based volatility estimator | 7 | 07-price-and-volume-features |
| rank correlation | 4 | 15-robust-statistics-and-heavy-tails |
| rank day | 8 | 10-index-rebalancing |
| rank information coefficient | 7 | 06-anatomy-of-a-predictor |
| rank transform | 7 | 06-anatomy-of-a-predictor |
| Rannacher time-stepping | 4 | 27-finite-difference-methods |
| rate limit | 3 | 15-centralised-exchanges |
| ratio adjustment | 7 | 02-market-data-for-research |
| real yield | 2 | 11-inflation-markets |
| real-time scheduling policy | 13 | 13-linux-tuning |
| realised correlation | 9 | 02-dispersion-and-correlation |
| realised kernel | 4 | 21-high-frequency-econometrics |
| realised P\&L | 1 | 07-pnl-and-positions |
| realised spread | 1 | 10-retail-flow-and-wholesaling |
| realised variance | 4 | 18-volatility-models |
| realised volatility | 1 | 25-volatility-first-contact |
| Reality Check | 4 | 12-testing-and-multiple-testing |
| rebalance frequency | 7 | 16-vectorised-backtests |
| rebalancing-flow estimate | 9 | 15-fx-flow-strategies |
| rebate capture | 11 | 17-rebates-inverted-venues-and-tiers |
| rebate rate | 1 | 06-financing |
| Rebonato's formula | 6 | 08-forward-rate-and-market-models |
| recalibration P\&L | 5 | 24-fourier-pricing-and-calibration-engineering |
| recall | 1 | 16-stock-loan-and-short-selling |
| receive buffer overrun | 13 | 18-the-feed-handler |
| receive timestamp | 1 | 28-reading-market-data |
| receiver swap | 2 | 09-interest-rate-swaps |
| receiver swaption | 2 | 13-the-rates-options-market |
| recombining tree | 5 | 02-the-binomial-model |
| record date | 1 | 08-shares-corporate-actions-indices |
| record linkage | 12 | 15-alternative-data-pipelines |
| recovery latency | 13 | 18-the-feed-handler |
| recovery rate | 2 | 21-corporate-bonds |
| recurrent neural network | 12 | 08-sequence-models-on-order-books |
| recursive least squares | 12 | 12-online-learning-and-drift |
| recycling trade | 9 | 28-hedging-a-structured-products-book |
| redenomination risk | 2 | 07-european-and-japanese-government-bonds |
| reduced-form model | 6 | 13-reduced-form-credit |
| redundant feed lines | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| reference data | 1 | 28-reading-market-data |
| reference entity | 2 | 23-credit-default-swaps |
| reference index | 2 | 11-inflation-markets |
| reference price waiver | 1 | 11-european-equity-market-structure |
| reference pricer | 5 | 28-build-a-pricing-library |
| reference quarter | 2 | 08-short-term-interest-rate-futures |
| refinancing incentive | 6 | 12-mortgage-modelling |
| reflected Brownian motion | 4 | 10-optimal-stopping-and-impulse-control |
| refresh-time sampling | 4 | 21-high-frequency-econometrics |
| regime-switching model | 12 | 20-clustering-regimes-and-anomaly-detection |
| regularisation | 4 | 16-linear-models-under-stress |
| regularisation path | 12 | 04-linear-and-regularised-baselines |
| regulated market | 1 | 11-european-equity-market-structure |
| rehypothecation | 1 | 06-financing |
| Reid vapour pressure | 3 | 03-refined-products-and-cracks |
| reinforcement learning | 12 | 17-reinforcement-learning-foundations |
| reject rate | 2 | 15-fx-spot-microstructure |
| relative limit price | 10 | 03-empirical-facts-of-order-books |
| relative risk aversion | 4 | 09-stochastic-control |
| relative tick size | 10 | 06-tick-size-queues-and-priority |
| release lock-up | 11 | 18-news-and-event-trading |
| release race | 11 | 18-news-and-event-trading |
| REMIT | 3 | 13-getting-access-commodities-and-power |
| renewable energy certificate | 3 | 07-emissions-and-environmental-markets |
| reopening auction | 10 | 25-circuit-breakers-and-halts |
| reorder buffer | 13 | 02-cpu-microarchitecture |
| replay parity test | 7 | 19-simulation-versus-live |
| replicated state machine | 13 | 24-resilience |
| replicating portfolio | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| repo rate | 2 | 05-repo-and-specials |
| repo rollover risk | 9 | 11-the-bond-futures-basis-trade |
| representation learning | 12 | 10-representation-learning |
| repricing rule | 10 | 17-child-order-placement |
| reproducible result | 7 | 29-build-a-research-workflow |
| repurchase agreement | 1 | 06-financing |
| request for quote | 2 | 22-how-bonds-trade |
| request for stream | 10 | 21-execution-beyond-equities |
| request weight | 3 | 15-centralised-exchanges |
| research hypothesis | 7 | 01-the-research-process |
| research log | 7 | 01-the-research-process |
| research review | 7 | 01-the-research-process |
| research unbundling | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| resend request | 13 | 15-protocols-i-fix |
| reservation price | 11 | 03-inventory-models |
| reserve price | 4 | 29-games-auctions-and-information |
| reserves | 2 | 01-central-banks-and-the-short-rate |
| residual momentum | 8 | 05-momentum |
| residual return | 7 | 06-anatomy-of-a-predictor |
| residual reversal | 8 | 02-short-term-reversal |
| residual risk add-on | 6 | 23-regulatory-capital-for-trading-books |
| residual risk hedge | 9 | 25-the-central-risk-book |
| resolution source | 3 | 27-prediction-and-betting-markets |
| REST interface | 13 | 17-websocket-rest-tls-and-json-at-speed |
| restaking | 3 | 23-defi-credit-and-leverage |
| restatement | 7 | 03-point-in-time-data-and-the-biases |
| retail liquidity programme | 11 | 23-retail-wholesaling |
| retraining schedule | 12 | 12-online-learning-and-drift |
| retransmission request | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| retrieval-augmented generation | 12 | 14-large-language-models-in-finance |
| return feature | 7 | 07-price-and-volume-features |
| return seasonality | 8 | 23-seasonality-and-calendar-effects |
| return smoothing | 7 | 22-performance-measurement |
| revaluation grid | 6 | 29-build-a-risk-engine |
| revaluation-based attribution | 6 | 27-pnl-explain-and-independent-price-verification |
| revenue capture | 11 | 01-the-business-of-market-making |
| reversal arbitrage | 11 | 20-options-cross-venue-and-volatility-arbitrage-at-speed |
| reverse cliquet | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| reverse convertible | 5 | 19-the-structured-products-business |
| reverse mode | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| reverse repo | 2 | 05-repo-and-specials |
| reverse repo facility | 2 | 02-money-markets |
| reverse stress test | 6 | 22-stress-testing-and-scenarios |
| review checklist | 7 | 29-build-a-research-workflow |
| reward | 12 | 17-reinforcement-learning-foundations |
| reward shaping | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| rho | 5 | 04-greeks-and-the-hedging-pnl |
| rich-cheap signal | 9 | 10-government-bond-relative-value |
| Richardson extrapolation | 4 | 27-finite-difference-methods |
| ridge regression | 4 | 16-linear-models-under-stress |
| rights issue | 1 | 08-shares-corporate-actions-indices |
| ring buffer | 13 | 12-queues-ring-buffers-and-shared-memory |
| ring dealing member | 3 | 13-getting-access-commodities-and-power |
| risk bid | 10 | 22-portfolio-trades-and-risk-bids |
| risk budgeting | 7 | 26-portfolio-construction-ii |
| risk contribution | 7 | 26-portfolio-construction-ii |
| risk data aggregation | 6 | 29-build-a-risk-engine |
| risk engine | 6 | 29-build-a-risk-engine |
| risk factor | 6 | 21-market-risk-measures |
| risk gate | 13 | 22-pre-trade-risk-and-kill-switches |
| risk hierarchy | 6 | 29-build-a-risk-engine |
| risk ladder | 6 | 03-rates-risk |
| risk limit | 6 | 29-build-a-risk-engine |
| risk of ruin | 2 | 29-thinking-in-expected-value |
| risk parity | 7 | 26-portfolio-construction-ii |
| risk pooling | 9 | 25-the-central-risk-book |
| risk reversal | 2 | 19-the-fx-options-market |
| risk transfer price | 10 | 21-execution-beyond-equities |
| risk-aversion parameter | 7 | 25-portfolio-construction-i |
| risk-based attribution | 6 | 27-pnl-explain-and-independent-price-verification |
| risk-factor eligibility test | 6 | 23-regulatory-capital-for-trading-books |
| risk-neutral density | 5 | 07-implied-volatility-and-its-surface |
| risk-neutral measure | 4 | 05-girsanov-and-changes-of-numeraire |
| risk-theoretical P\&L | 6 | 23-regulatory-capital-for-trading-books |
| risk-weighted assets | 1 | 02-the-sell-side |
| risky annuity | 6 | 13-reduced-form-credit |
| risky discount factor | 6 | 13-reduced-form-credit |
| robust portfolio optimisation | 7 | 26-portfolio-construction-ii |
| rogue trading | 6 | 28-operational-risk-and-rogue-trading |
| roll | 1 | 21-basis-roll-and-delivery |
| roll window | 3 | 10-forward-curves-storage-and-convenience-yield |
| roll yield | 3 | 10-forward-curves-storage-and-convenience-yield |
| Roll's estimator | 4 | 21-high-frequency-econometrics |
| rolling intrinsic | 6 | 16-commodity-and-energy-derivatives |
| rollup | 3 | 14-blockchains-for-traders |
| rotation-equivariant estimator | 4 | 22-covariance-estimation-and-random-matrices |
| rough Bergomi model | 5 | 12-rough-volatility-and-forward-variance-models |
| rough volatility | 5 | 12-rough-volatility-and-forward-variance-models |
| round lot | 1 | 09-us-equity-market-structure |
| round-trip efficiency | 3 | 06-power-markets-trading |
| route index | 3 | 11-freight-weather-and-other-corners |
| RPC endpoint | 3 | 26-crypto-data-and-infrastructure |
| Rule 605 report | 1 | 10-retail-flow-and-wholesaling |
| Rule 606 report | 1 | 10-retail-flow-and-wholesaling |
| run record | 12 | 25-experiment-tracking-and-reproducibility |
| run-to-completion processing | 13 | 20-the-strategy-engine |
| Runge phenomenon | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| s-score | 8 | 03-residual-and-principal-component-stat-arb |
| SABR model | 5 | 11-sabr-and-smile-dynamics |
| sales-trader | 1 | 02-the-sell-side |
| sample covariance matrix | 4 | 22-covariance-estimation-and-random-matrices |
| sample ratio mismatch | 7 | 21-live-experiments |
| sample weight | 12 | 02-targets-labels-and-sample-weights |
| sampled replication | 8 | 29-the-asset-managers-strategies |
| sampling profiler | 13 | 05-measuring-latency |
| Samuelson effect | 3 | 10-forward-curves-storage-and-convenience-yield |
| sandwich attack | 3 | 22-maximal-extractable-value |
| sandwich variance | 4 | 11-estimation |
| scanning range | 1 | 20-margin |
| scenario conditioning | 6 | 22-stress-testing-and-scenarios |
| schedule nomination | 3 | 13-getting-access-commodities-and-power |
| schedule-based initial margin | 6 | 25-margin-models |
| schema validation | 12 | 15-alternative-data-pipelines |
| Schwartz--Smith model | 6 | 16-commodity-and-energy-derivatives |
| score function | 4 | 11-estimation |
| search friction | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| searcher | 3 | 22-maximal-extractable-value |
| secant method | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| second-order cone programme | 4 | 23-convex-optimisation |
| second-price auction | 4 | 29-games-auctions-and-information |
| securities information processor | 1 | 09-us-equity-market-structure |
| securities lending | 1 | 06-financing |
| securities transaction tax | 1 | 12-asian-and-emerging-equity-markets |
| securitisation | 2 | 25-loans-clos-and-securitisation |
| security master | 7 | 04-universe-symbology-and-corporate-actions |
| segregation of duties | 6 | 28-operational-risk-and-rogue-trading |
| self-custody | 3 | 24-the-crypto-trading-business |
| self-financing strategy | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| self-supervised learning | 12 | 10-representation-learning |
| self-trade prevention | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| sell side | 1 | 02-the-sell-side |
| semidefinite programme | 4 | 23-convex-optimisation |
| semimartingale | 4 | 06-jump-processes |
| seniority | 2 | 21-corporate-bonds |
| sensitivities-based method | 6 | 23-regulatory-capital-for-trading-books |
| sentiment index | 8 | 24-positioning-and-sentiment |
| sentiment score | 7 | 12-alternative-and-text-data |
| sequence lock | 13 | 12-queues-ring-buffers-and-shared-memory |
| sequence number | 1 | 28-reading-market-data |
| sequencer | 3 | 14-blockchains-for-traders |
| sequencer architecture | 13 | 24-resilience |
| sequential bootstrap | 12 | 02-targets-labels-and-sample-weights |
| sequential consistency | 13 | 11-lock-free-programming |
| sequential importance resampling | 4 | 19-state-space-models-and-the-kalman-filter |
| sequential test | 7 | 21-live-experiments |
| sequential-trade model | 10 | 04-why-there-is-a-spread |
| session resumption | 13 | 17-websocket-rest-tls-and-json-at-speed |
| set-associative cache | 13 | 03-memory-hierarchy-and-caches |
| settlement | 1 | 05-clearing-and-settlement |
| settlement cycle | 1 | 05-clearing-and-settlement |
| settlement fail | 1 | 05-clearing-and-settlement |
| settlement limit | 2 | 27-getting-access-fx |
| settlement risk | 2 | 20-settlement-risk |
| shadow deployment | 12 | 27-monitoring-and-retraining |
| shadow price | 4 | 23-convex-optimisation |
| shadow trading | 7 | 19-simulation-versus-live |
| SHAP value | 12 | 06-feature-engineering-selection-and-importance |
| shape risk | 3 | 06-power-markets-trading |
| Shapley value | 12 | 06-feature-engineering-selection-and-importance |
| share | 1 | 08-shares-corporate-actions-indices |
| shared-memory transport | 13 | 12-queues-ring-buffers-and-shared-memory |
| Sharpe ratio | 4 | 11-estimation |
| shifted lognormal model | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| shifted SABR | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| short interest | 1 | 16-stock-loan-and-short-selling |
| short sale | 1 | 06-financing |
| short squeeze | 1 | 16-stock-loan-and-short-selling |
| short-crowding measure | 8 | 08-short-interest-borrow-and-crowding |
| short-horizon alpha | 11 | 07-short-horizon-alpha |
| short-rate model | 6 | 07-short-rate-models |
| short-term reversal | 8 | 02-short-term-reversal |
| short-volatility strategy | 9 | 01-harvesting-the-variance-risk-premium |
| shrinkage estimator | 4 | 14-bayesian-methods |
| signal autocorrelation | 7 | 13-half-life-decay-and-stability |
| signal combination | 7 | 14-signal-combination |
| signal half-life | 7 | 13-half-life-decay-and-stability |
| signal smoothing | 7 | 27-transaction-costs-in-research |
| signal-adaptive schedule | 10 | 15-beyond-almgren-chriss |
| signal-to-noise ratio | 4 | 19-state-space-models-and-the-kalman-filter |
| signature plot | 4 | 21-high-frequency-econometrics |
| sim-to-live reconciliation | 7 | 19-simulation-versus-live |
| sim-to-real gap | 12 | 17-reinforcement-learning-foundations |
| SIMD | 13 | 14-vector-instructions-and-data-parallel-code |
| simple binary encoding | 13 | 16-protocols-ii-binary-exchange-protocols |
| simple process | 4 | 03-ito-calculus |
| simulated clock | 7 | 17-event-driven-backtests |
| simulator calibration | 7 | 19-simulation-versus-live |
| simultaneous multithreading | 13 | 02-cpu-microarchitecture |
| single-dealer platform | 2 | 14-the-fx-market |
| single-producer single-consumer queue | 13 | 12-queues-ring-buffers-and-shared-memory |
| single-stock future | 1 | 22-index-and-single-stock-futures-worldwide |
| singular control | 4 | 10-optimal-stopping-and-impulse-control |
| singular value decomposition | 4 | 25-floating-point-and-numerical-linear-algebra |
| size of a test | 4 | 12-testing-and-multiple-testing |
| skew trade | 9 | 03-skew-and-term-structure-relative-value |
| skip period | 7 | 07-price-and-volume-features |
| Slater's condition | 4 | 23-convex-optimisation |
| slippage attribution | 10 | 19-transaction-cost-analysis |
| slippage tolerance | 3 | 22-maximal-extractable-value |
| slope factor | 6 | 03-rates-risk |
| slow consumer | 13 | 12-queues-ring-buffers-and-shared-memory |
| slow diffusion | 8 | 22-cross-asset-lead-lag |
| small-buffer optimisation | 13 | 06-cpp-for-latency-i-memory |
| small-tick asset | 10 | 06-tick-size-queues-and-priority |
| smart contract | 3 | 14-blockchains-for-traders |
| smart order router | 10 | 18-smart-order-routing |
| smooth pasting | 4 | 10-optimal-stopping-and-impulse-control |
| snapshot channel | 13 | 16-protocols-ii-binary-exchange-protocols |
| snapshot recovery | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| snapshot-and-delta feed | 3 | 26-crypto-data-and-infrastructure |
| Snell envelope | 4 | 10-optimal-stopping-and-impulse-control |
| snowball | 5 | 18-autocallables |
| Sobol sequence | 4 | 26-monte-carlo |
| socialised loss | 3 | 18-margin-liquidation-and-loss-allocation |
| socket interconnect | 13 | 04-multi-socket-machines-and-interconnects |
| soft call | 5 | 21-convertibles-and-the-credit-equity-link |
| softs | 3 | 09-agriculturals-and-softs |
| Sortino ratio | 7 | 22-performance-measurement |
| sound abstraction | 13 | 09-rust-for-low-latency |
| sour crude | 3 | 02-crude-oil |
| sovereign spread | 2 | 07-european-and-japanese-government-bonds |
| spark spread | 3 | 05-power-markets-design |
| Spearman's rank correlation | 4 | 15-robust-statistics-and-heavy-tails |
| special | 1 | 16-stock-loan-and-short-selling |
| special opening quotation | 1 | 21-basis-roll-and-delivery |
| special purpose acquisition company | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| special repo rate | 2 | 05-repo-and-specials |
| special-purpose vehicle | 2 | 25-loans-clos-and-securitisation |
| specialness | 2 | 05-repo-and-specials |
| specific return | 7 | 24-risk-models |
| specific risk | 7 | 24-risk-models |
| specified pool | 2 | 12-mortgages-and-agencies |
| spectral density | 4 | 17-linear-time-series |
| speculator | 1 | 18-futures-contracts-and-exchanges |
| speed bump | 11 | 09-latency-arbitrage-and-its-defence |
| spiked covariance model | 4 | 22-covariance-estimation-and-random-matrices |
| spin-off | 1 | 08-shares-corporate-actions-indices |
| split brain | 13 | 24-resilience |
| sponsored access | 1 | 04-exchanges-brokers-venues |
| sponsored member | 2 | 28-getting-access-rates-credit |
| sponsored repo | 2 | 05-repo-and-specials |
| spoofing | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| spot delta | 2 | 19-the-fx-options-market |
| spot measure | 6 | 08-forward-rate-and-market-models |
| spot return | 3 | 10-forward-curves-storage-and-convenience-yield |
| spot value date | 2 | 14-the-fx-market |
| spot--volatility correlation | 5 | 10-stochastic-volatility |
| spray order | 10 | 18-smart-order-routing |
| spread capture | 7 | 23-measuring-market-making-and-execution |
| spread decomposition | 10 | 05-decomposing-the-spread |
| spread mean reversion | 8 | 21-calendar-spreads-and-curve-trades |
| spread option | 6 | 16-commodity-and-energy-derivatives |
| spurious regression | 4 | 17-linear-time-series |
| square-root impact law | 7 | 27-transaction-costs-in-research |
| square-root process | 4 | 04-stochastic-differential-equations |
| square-root-of-time rule | 6 | 21-market-risk-measures |
| squeeze risk | 8 | 08-short-interest-borrow-and-crowding |
| stability selection | 12 | 06-feature-engineering-selection-and-importance |
| stable scheme | 4 | 27-finite-difference-methods |
| stablecoin | 3 | 14-blockchains-for-traders |
| stableswap | 3 | 20-automated-market-makers |
| stacking | 7 | 14-signal-combination |
| stage gate | 7 | 01-the-research-process |
| staged rollout | 7 | 21-live-experiments |
| stake limiting | 11 | 26-prediction-and-sports-market-making |
| staking yield | 3 | 23-defi-credit-and-leverage |
| stale-book flag | 13 | 18-the-feed-handler |
| stale-quote sniping | 11 | 09-latency-arbitrage-and-its-defence |
| stamp duty | 1 | 12-asian-and-emerging-equity-markets |
| standard coupon | 2 | 23-credit-default-swaps |
| standard error | 4 | 11-estimation |
| standard initial margin model | 6 | 25-margin-models |
| standardised approach for counterparty credit risk | 6 | 19-funding-margin-and-capital-adjustments |
| standardised unexpected earnings | 7 | 11-fundamental-analyst-and-event-features |
| standing facility | 2 | 01-central-banks-and-the-short-rate |
| stat-arb book | 8 | 01-anatomy-of-a-stat-arb-book |
| state price | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| state-price density | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| state-space model | 4 | 19-state-space-models-and-the-kalman-filter |
| static arbitrage | 5 | 07-implied-volatility-and-its-surface |
| static hedging | 5 | 15-barriers-and-digitals |
| static polymorphism | 13 | 07-cpp-for-latency-ii-compile-time |
| static price band | 10 | 25-circuit-breakers-and-halts |
| stationary bootstrap | 4 | 13-resampling |
| stationary distribution | 4 | 04-stochastic-differential-equations |
| stationary process | 4 | 17-linear-time-series |
| statistical arbitrage | 8 | 01-anatomy-of-a-stat-arb-book |
| statistical factor model | 7 | 24-risk-models |
| steepener | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| sticky delta | 5 | 07-implied-volatility-and-its-surface |
| sticky strike | 5 | 07-implied-volatility-and-its-surface |
| stochastic control problem | 4 | 09-stochastic-control |
| stochastic differential equation | 4 | 04-stochastic-differential-equations |
| stochastic exponential | 4 | 03-ito-calculus |
| stochastic gradient descent | 4 | 24-numerical-optimisation-in-practice |
| stochastic liquidity | 10 | 15-beyond-almgren-chriss |
| stochastic volatility model | 5 | 10-stochastic-volatility |
| stochastic-local volatility model | 5 | 20-fx-derivatives |
| Stock Connect | 1 | 12-asian-and-emerging-equity-markets |
| stock split | 1 | 08-shares-corporate-actions-indices |
| stock-deal collar | 8 | 11-merger-arbitrage |
| stocks-to-use ratio | 3 | 09-agriculturals-and-softs |
| stop discipline | 9 | 17-discretionary-macro |
| stop order | 10 | 02-order-types-and-their-uses |
| stop-limit order | 10 | 02-order-types-and-their-uses |
| stop-the-world pause | 13 | 10-managed-and-functional-languages-on-the-desk |
| stopping region | 4 | 10-optimal-stopping-and-impulse-control |
| stopping time | 4 | 01-probability-at-speed |
| storage deal | 9 | 22-storage-transport-and-physical-optionality |
| storage-limit risk | 8 | 21-calendar-spreads-and-curve-trades |
| straddle | 5 | 04-greeks-and-the-hedging-pnl |
| strangle | 2 | 19-the-fx-options-market |
| strategy capacity | 7 | 28-capacity-decay-and-crowding |
| strategy correlation | 8 | 28-running-a-multi-strategy-book |
| strategy lifecycle | 11 | 28-pnl-analytics-and-the-strategy-lifecycle |
| strategy wrapper | 9 | 27-quantitative-investment-strategies |
| stratified sampling | 4 | 26-monte-carlo |
| Stratonovich integral | 4 | 03-ito-calculus |
| streaming quote | 2 | 15-fx-spot-microstructure |
| stress test | 6 | 22-stress-testing-and-scenarios |
| stressed expected shortfall | 6 | 23-regulatory-capital-for-trading-books |
| strict aliasing | 13 | 08-cpp-for-latency-iii-the-compiler |
| strike price | 1 | 23-option-contracts-and-exchanges |
| strike risk limit | 11 | 19-automated-options-market-making |
| STRIPS | 2 | 03-government-bonds |
| strong duality | 4 | 23-convex-optimisation |
| strong Markov property | 4 | 02-brownian-motion |
| strong order of convergence | 4 | 26-monte-carlo |
| strong solution | 4 | 04-stochastic-differential-equations |
| structural break | 7 | 13-half-life-decay-and-stability |
| structural model | 6 | 14-structural-credit-models |
| structure of arrays | 13 | 14-vector-instructions-and-data-parallel-code |
| structure padding | 13 | 06-cpp-for-latency-i-memory |
| structured note | 5 | 19-the-structured-products-business |
| structured product | 5 | 19-the-structured-products-business |
| structuring margin | 5 | 19-the-structured-products-business |
| stub quote | 1 | 31-stress-case-studies |
| Student-t copula | 6 | 15-portfolio-credit |
| style factor | 7 | 24-risk-models |
| stylised fact | 7 | 05-stylised-facts-of-returns |
| sub-account | 3 | 15-centralised-exchanges |
| submartingale | 4 | 01-probability-at-speed |
| subnormal number | 4 | 25-floating-point-and-numerical-linear-algebra |
| subordinator | 4 | 06-jump-processes |
| substitution effect | 12 | 06-feature-engineering-selection-and-importance |
| summer--winter spread | 3 | 04-natural-gas-and-lng |
| super senior tranche | 6 | 15-portfolio-credit |
| super-replication price | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| superior predictive ability test | 4 | 12-testing-and-multiple-testing |
| supermartingale | 4 | 01-probability-at-speed |
| supervised learning | 12 | 01-why-financial-machine-learning-is-different |
| supervisory stress test | 6 | 22-stress-testing-and-scenarios |
| supplemental liquidity provider | 1 | 29-getting-access-equities |
| supply trade | 9 | 13-supply-trades |
| surface SVI | 5 | 08-parametrising-the-surface |
| surrogate model | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| survival probability | 2 | 23-credit-default-swaps |
| survivorship bias | 7 | 03-point-in-time-data-and-the-biases |
| SVI parametrisation | 5 | 08-parametrising-the-surface |
| swap execution facility | 2 | 09-interest-rate-swaps |
| swap market model | 6 | 08-forward-rate-and-market-models |
| swap spread | 2 | 09-interest-rate-swaps |
| swap-spread trade | 9 | 12-swap-spread-and-asset-swap-trades |
| swaption | 2 | 13-the-rates-options-market |
| swaption matrix | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| sweet crude | 3 | 02-crude-oil |
| swing contract | 3 | 12-commodity-options-and-structured-hedges |
| switch option | 6 | 09-bermudans-and-callables |
| switching price | 3 | 07-emissions-and-environmental-markets |
| symbology | 1 | 28-reading-market-data |
| symmetric orthogonalisation | 7 | 14-signal-combination |
| synchronised routing | 10 | 18-smart-order-routing |
| syndication | 2 | 07-european-and-japanese-government-bonds |
| synthetic cross | 11 | 21-fx-market-making |
| synthetic twin | 8 | 04-pairs-and-baskets |
| systematic internaliser | 1 | 11-european-equity-market-structure |
| systematic strategy index | 5 | 19-the-structured-products-business |
| T+0 restriction | 1 | 12-asian-and-emerging-equity-markets |
| tag-value encoding | 13 | 15-protocols-i-fix |
| tail dependence coefficient | 4 | 15-robust-statistics-and-heavy-tails |
| tail hedge | 9 | 07-tail-hedging-and-long-volatility |
| tail index | 4 | 15-robust-statistics-and-heavy-tails |
| tail latency | 13 | 01-where-latency-comes-from |
| take threshold | 11 | 07-short-horizon-alpha |
| take-or-pay clause | 3 | 12-commodity-options-and-structured-hedges |
| tape | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| target leakage | 12 | 03-validation |
| target network | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| target redemption forward | 5 | 20-fx-derivatives |
| target-close algorithm | 10 | 16-benchmark-algorithms |
| Taylor effect | 7 | 05-stylised-facts-of-returns |
| temporal convolutional network | 12 | 08-sequence-models-on-order-books |
| temporal-difference learning | 12 | 17-reinforcement-learning-foundations |
| temporary impact | 7 | 27-transaction-costs-in-research |
| tender offer | 8 | 11-merger-arbitrage |
| tenor basis | 6 | 02-multi-curve-and-collateral-discounting |
| tenor basis swap | 6 | 02-multi-curve-and-collateral-discounting |
| term frequency--inverse document frequency | 12 | 13-text-from-bag-of-words-to-embeddings |
| term loan B | 2 | 25-loans-clos-and-securitisation |
| term repo | 2 | 05-repo-and-specials |
| term structure of volatility | 1 | 25-volatility-first-contact |
| term-structure trade | 9 | 03-skew-and-term-structure-relative-value |
| terminal measure | 6 | 08-forward-rate-and-market-models |
| test set | 12 | 01-why-financial-machine-learning-is-different |
| theoretical value | 5 | 26-options-market-making-in-practice |
| theory of storage | 3 | 10-forward-curves-storage-and-convenience-yield |
| theta | 5 | 04-greeks-and-the-hedging-pnl |
| theta scheme | 4 | 27-finite-difference-methods |
| thinning | 4 | 07-point-processes-and-hawkes-processes |
| three lines of defence | 6 | 26-model-risk-and-validation |
| three-month price | 3 | 08-metals |
| three-way collar | 3 | 12-commodity-options-and-structured-hedges |
| tick bar | 7 | 02-market-data-for-research |
| tick rule | 7 | 09-trade-flow-features |
| tick size | 10 | 01-the-limit-order-book |
| tick value | 1 | 18-futures-contracts-and-exchanges |
| tick-to-trade latency | 13 | 01-where-latency-comes-from |
| ticker change | 7 | 04-universe-symbology-and-corporate-actions |
| tickless kernel | 13 | 13-linux-tuning |
| tier cliff | 11 | 17-rebates-inverted-venues-and-tiers |
| tier matching | 3 | 25-getting-access-crypto-venues |
| time bar | 7 | 02-market-data-for-research |
| time charter | 3 | 11-freight-weather-and-other-corners |
| time in force | 10 | 02-order-types-and-their-uses |
| time-charter equivalent | 3 | 11-freight-weather-and-other-corners |
| time-decay weight | 12 | 02-targets-labels-and-sample-weights |
| time-series momentum | 8 | 19-trend-following |
| time-stamp counter | 13 | 02-cpu-microarchitecture |
| timer wheel | 13 | 20-the-strategy-engine |
| timing adjustment | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| Title Transfer Facility | 3 | 04-natural-gas-and-lng |
| TLS handshake | 13 | 17-websocket-rest-tls-and-json-at-speed |
| to-be-announced trade | 2 | 12-mortgages-and-agencies |
| token | 3 | 14-blockchains-for-traders |
| token bucket | 13 | 21-order-gateway-and-order-management |
| token market-making agreement | 3 | 24-the-crypto-trading-business |
| token unlock | 3 | 24-the-crypto-trading-business |
| tokenisation | 12 | 13-text-from-bag-of-words-to-embeddings |
| tom-next | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| tool call | 12 | 14-large-language-models-in-finance |
| top-order allocation | 1 | 19-matching-algorithms-and-implied-spreads |
| topic model | 12 | 13-text-from-bag-of-words-to-embeddings |
| total implied variance | 5 | 07-implied-volatility-and-its-surface |
| total least squares | 4 | 16-linear-models-under-stress |
| total number of allowances in circulation | 3 | 07-emissions-and-environmental-markets |
| total return future | 1 | 22-index-and-single-stock-futures-worldwide |
| total return index | 1 | 08-shares-corporate-actions-indices |
| total return swap | 1 | 06-financing |
| touch fill | 7 | 17-event-driven-backtests |
| toxicity score | 11 | 06-adverse-selection-and-toxicity |
| tracking error | 1 | 03-the-buy-side |
| tradable universe | 7 | 04-universe-symbology-and-corporate-actions |
| trade at settlement | 1 | 21-basis-roll-and-delivery |
| trade compression | 2 | 09-interest-rate-swaps |
| trade condition | 1 | 28-reading-market-data |
| trade expression | 9 | 17-discretionary-macro |
| trade finance | 3 | 13-getting-access-commodities-and-power |
| trade price impact | 10 | 05-decomposing-the-spread |
| trade reporting | 2 | 22-how-bonds-trade |
| trade sign | 7 | 09-trade-flow-features |
| trade-through | 1 | 09-us-equity-market-structure |
| trading book | 6 | 23-regulatory-capital-for-trading-books |
| trading halt | 8 | 17-news-and-events |
| trading pause | 10 | 25-circuit-breakers-and-halts |
| trading period | 8 | 04-pairs-and-baskets |
| trading trajectory | 10 | 14-the-almgren-chriss-framework |
| traffic-light test | 6 | 21-market-risk-measures |
| trailing twelve months | 7 | 11-fundamental-analyst-and-event-features |
| train--test contamination | 12 | 03-validation |
| train-on-synthetic test-on-real | 12 | 16-generative-models-and-synthetic-data |
| training checkpoint | 12 | 23-training-infrastructure |
| training cut-off | 12 | 14-large-language-models-in-finance |
| training set | 12 | 01-why-financial-machine-learning-is-different |
| training--serving skew | 12 | 24-data-and-feature-stores |
| tranche | 2 | 24-credit-indices-and-tranches |
| tranche delta | 6 | 15-portfolio-credit |
| tranche relative value | 9 | 20-mortgage-and-structured-credit-strategies |
| transaction bundle | 3 | 22-maximal-extractable-value |
| transaction cost analysis | 7 | 23-measuring-market-making-and-execution |
| transaction-triggered price manipulation | 10 | 12-transient-impact-and-propagator-models |
| transfer coefficient | 7 | 15-from-signal-to-forecast |
| transfer latency | 3 | 16-spot-markets |
| transformer | 12 | 08-sequence-models-on-order-books |
| transient impact model | 10 | 12-transient-impact-and-propagator-models |
| transition management | 8 | 29-the-asset-managers-strategies |
| translation lookaside buffer | 13 | 03-memory-hierarchy-and-caches |
| transport option | 9 | 22-storage-transport-and-physical-optionality |
| travel rule | 3 | 24-the-crypto-trading-business |
| Treasury bill | 2 | 02-money-markets |
| trend following | 8 | 19-trend-following |
| tri-party repo | 2 | 05-repo-and-specials |
| trial count | 7 | 01-the-research-process |
| triangular arbitrage | 3 | 16-spot-markets |
| tridiagonal matrix algorithm | 4 | 25-floating-point-and-numerical-linear-algebra |
| trimmed mean | 4 | 15-robust-statistics-and-heavy-tails |
| trinomial tree | 5 | 22-trees-and-finite-difference-pricers-in-practice |
| triple-barrier label | 12 | 02-targets-labels-and-sample-weights |
| truncation error | 4 | 27-finite-difference-methods |
| trust value | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| turn | 2 | 02-money-markets |
| turn-of-the-month effect | 8 | 23-seasonality-and-calendar-effects |
| turnover penalty | 7 | 25-portfolio-construction-i |
| turnover ratio | 7 | 07-price-and-volume-features |
| turnover velocity | 3 | 29-a-map-of-all-markets |
| TWAP algorithm | 10 | 16-benchmark-algorithms |
| two-factor Gaussian model | 6 | 07-short-rate-models |
| two-scales realised variance | 4 | 21-high-frequency-econometrics |
| unallocated gold | 3 | 08-metals |
| unbiased estimator | 4 | 11-estimation |
| uncertainty set | 7 | 26-portfolio-construction-ii |
| uncertainty-zone model | 10 | 06-tick-size-queues-and-priority |
| uncleared margin rules | 2 | 10-swap-clearing-and-the-ccp-basis |
| uncrossing price | 1 | 13-auctions |
| undefined behaviour | 13 | 08-cpp-for-latency-iii-the-compiler |
| underwriting | 1 | 02-the-sell-side |
| unexplained P\&L | 6 | 27-pnl-explain-and-independent-price-verification |
| uniform integrability | 4 | 01-probability-at-speed |
| uniform-price auction | 2 | 04-the-treasury-market |
| unilateral irrevocable payment time | 2 | 20-settlement-risk |
| unit in the last place | 4 | 25-floating-point-and-numerical-linear-algebra |
| unit root | 4 | 17-linear-time-series |
| universe membership | 7 | 04-universe-symbology-and-corporate-actions |
| unrealised P\&L | 1 | 07-pnl-and-positions |
| unsupervised learning | 12 | 01-why-financial-machine-learning-is-different |
| unwind | 7 | 28-capacity-decay-and-crowding |
| upfront payment | 2 | 23-credit-default-swaps |
| uptick rule | 1 | 12-asian-and-emerging-equity-markets |
| uptime requirement | 3 | 25-getting-access-crypto-venues |
| upwind scheme | 4 | 27-finite-difference-methods |
| urgency | 10 | 14-the-almgren-chriss-framework |
| utilisation | 1 | 16-stock-loan-and-short-selling |
| utility function | 4 | 09-stochastic-control |
| valid time | 7 | 03-point-in-time-data-and-the-biases |
| validation set | 12 | 01-why-financial-machine-learning-is-different |
| validator | 3 | 14-blockchains-for-traders |
| valuation reserve | 5 | 27-managing-an-exotic-book |
| value at risk | 6 | 21-market-risk-measures |
| value function | 4 | 09-stochastic-control |
| value strategy | 8 | 06-value-quality-and-low-risk |
| vanna | 5 | 04-greeks-and-the-hedging-pnl |
| vanna--volga method | 5 | 20-fx-derivatives |
| VaR exception | 6 | 21-market-risk-measures |
| variance | 1 | 25-volatility-first-contact |
| variance gamma model | 5 | 13-jumps-and-levy-models |
| variance inflation factor | 4 | 16-linear-models-under-stress |
| variance notional | 5 | 14-variance-swaps-and-volatility-derivatives |
| variance reduction | 4 | 26-monte-carlo |
| variance risk premium | 5 | 14-variance-swaps-and-volatility-derivatives |
| variance swap | 5 | 14-variance-swaps-and-volatility-derivatives |
| variation margin | 1 | 05-clearing-and-settlement |
| variational autoencoder | 12 | 16-generative-models-and-synthetic-data |
| variational inequality | 4 | 10-optimal-stopping-and-impulse-control |
| Vasicek model | 6 | 07-short-rate-models |
| vector autoregression | 4 | 20-multivariate-series-and-cointegration |
| vector error-correction model | 4 | 20-multivariate-series-and-cointegration |
| vector instruction | 13 | 14-vector-instructions-and-data-parallel-code |
| vectorised backtest | 7 | 16-vectorised-backtests |
| vega | 5 | 04-greeks-and-the-hedging-pnl |
| vega bucket | 5 | 26-options-market-making-in-practice |
| vega notional | 5 | 14-variance-swaps-and-volatility-derivatives |
| vega weighting | 5 | 24-fourier-pricing-and-calibration-engineering |
| velocity logic | 10 | 25-circuit-breakers-and-halts |
| venue profile | 11 | 29-a-venue-playbook |
| venue ranking | 10 | 18-smart-order-routing |
| venue risk | 8 | 27-crypto-medium-frequency-strategies |
| virtual bid | 3 | 06-power-markets-trading |
| virtual trading point | 3 | 04-natural-gas-and-lng |
| viscosity solution | 4 | 09-stochastic-control |
| Viterbi algorithm | 12 | 20-clustering-regimes-and-anomaly-detection |
| VIX future | 1 | 25-volatility-first-contact |
| VIX option | 5 | 14-variance-swaps-and-volatility-derivatives |
| VIX term-structure slope | 9 | 05-the-volatility-index-complex |
| volatility clustering | 4 | 18-volatility-models |
| volatility crush | 9 | 04-gamma-scalping-and-event-volatility |
| volatility cube | 2 | 13-the-rates-options-market |
| volatility decay | 1 | 14-exchange-traded-funds |
| volatility index | 1 | 25-volatility-first-contact |
| volatility interruption | 1 | 13-auctions |
| volatility of volatility | 5 | 10-stochastic-volatility |
| volatility per trade | 10 | 03-empirical-facts-of-order-books |
| volatility persistence | 4 | 18-volatility-models |
| volatility regime adjustment | 7 | 24-risk-models |
| volatility roll-down | 5 | 25-trading-volatility |
| volatility skew | 1 | 25-volatility-first-contact |
| volatility surface | 5 | 07-implied-volatility-and-its-surface |
| volatility swap | 5 | 14-variance-swaps-and-volatility-derivatives |
| volatility targeting | 8 | 19-trend-following |
| volatility-managed portfolio | 8 | 26-volatility-targeting-and-risk-managed-portfolios |
| volatility-scaled momentum | 8 | 05-momentum |
| volatility-target index | 5 | 19-the-structured-products-business |
| volga | 5 | 04-greeks-and-the-hedging-pnl |
| volume bar | 7 | 02-market-data-for-research |
| volume participation cap | 7 | 17-event-driven-backtests |
| volume smile | 8 | 13-intraday-patterns |
| volume surprise | 7 | 07-price-and-volume-features |
| volume tier | 1 | 29-getting-access-equities |
| volume-weighted average price | 7 | 02-market-data-for-research |
| von Neumann stability analysis | 4 | 27-finite-difference-methods |
| voyage charter | 3 | 11-freight-weather-and-other-corners |
| VPIN | 7 | 09-trade-flow-features |
| VWAP algorithm | 10 | 16-benchmark-algorithms |
| VWAP slippage | 7 | 23-measuring-market-making-and-execution |
| wait-free | 13 | 11-lock-free-programming |
| walk-forward analysis | 7 | 20-overfitting |
| warehouse warrant | 3 | 08-metals |
| warm-up period | 13 | 10-managed-and-functional-languages-on-the-desk |
| WASDE report | 3 | 09-agriculturals-and-softs |
| wash trading | 3 | 16-spot-markets |
| weak order of convergence | 4 | 26-monte-carlo |
| weak solution | 4 | 04-stochastic-differential-equations |
| weak stationarity | 4 | 17-linear-time-series |
| weather derivative | 3 | 11-freight-weather-and-other-corners |
| weather-driven position | 9 | 23-power-and-gas-trading |
| WebSocket | 13 | 17-websocket-rest-tls-and-json-at-speed |
| WebSocket frame | 13 | 17-websocket-rest-tls-and-json-at-speed |
| weekly expiry | 1 | 27-options-markets-europe-asia |
| weekly option | 1 | 26-zero-day-options-and-retail-flow |
| weight decay | 12 | 07-neural-networks-for-noisy-tabular-data |
| weighted least squares | 4 | 16-linear-models-under-stress |
| weighted mid price | 7 | 08-order-book-features |
| Welford's algorithm | 4 | 25-floating-point-and-numerical-linear-algebra |
| when-issued trading | 2 | 04-the-treasury-market |
| white noise | 4 | 17-linear-time-series |
| wholesaler | 1 | 10-retail-flow-and-wholesaling |
| width | 2 | 30-market-making-games |
| wildcard option | 2 | 06-bond-futures |
| win-probability model | 11 | 22-bond-and-etf-request-for-quote-market-making |
| winner's curse | 2 | 30-market-making-games |
| winsorisation | 4 | 15-robust-statistics-and-heavy-tails |
| wire-to-wire latency | 13 | 01-where-latency-comes-from |
| withholding tax | 1 | 17-delta-one-instruments |
| word embedding | 12 | 13-text-from-bag-of-words-to-embeddings |
| working set | 13 | 03-memory-hierarchy-and-caches |
| worst-case exposure | 13 | 22-pre-trade-risk-and-kill-switches |
| worst-of option | 5 | 17-multi-asset-options |
| wrong-way risk | 6 | 17-counterparty-exposure |
| XVA | 6 | 18-credit-and-debit-valuation-adjustments |
| XVA charge | 6 | 20-the-valuation-adjustment-desk |
| XVA desk | 6 | 20-the-valuation-adjustment-desk |
| Yang--Zhang estimator | 7 | 07-price-and-volume-features |
| year-on-year convexity adjustment | 6 | 11-inflation-derivatives |
| year-on-year inflation swap | 6 | 11-inflation-derivatives |
| yield to maturity | 2 | 03-government-bonds |
| yield-curve control | 2 | 07-european-and-japanese-government-bonds |
| Z-spread | 2 | 21-corporate-bonds |
| zero-cost abstraction | 13 | 09-rust-for-low-latency |
| zero-coupon inflation swap | 2 | 11-inflation-markets |
| zero-coupon rate | 2 | 03-government-bonds |
| zero-day option | 1 | 26-zero-day-options-and-retail-flow |
| zero-intelligence model | 10 | 01-the-limit-order-book |
| zero-sum game | 4 | 29-games-auctions-and-information |

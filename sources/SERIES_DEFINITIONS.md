# Series definition map (One Quant Books 1–18)

Regenerated 2026-09-29 after the Books 17–18 batch (the whole series), from the `\index{}` harvest of
all eighteen books (first written 2026-09-24 for Books 1–6) (multi-line aware; the same harvest as `tools/gates.sh book`). **A term
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

## Rulings at the Books 14–16 sync (2026-09-28)

Ownership rule: Books 1–13 keep their terms; otherwise Book 14 owns network, hardware, timing,
physical-access, colocation-product, long-haul, cloud-networking and connectivity-contract terms; Book 15
data-system, storage-format, platform, pricing-library-architecture, post-trade-systems and
software-engineering-practice terms; Book 16 business-model, organisation, control-function,
funding/treasury, legal-documentation, compensation-policy and firm-strategy terms. Ties go to the lower
book. Planned maps: `sources/{networks,platforms,desk}/DEFINITIONS.md` (181 + 248 + 201 terms; one exact
collision, *vendor lock-in*). Forward pointers (a lower book using a higher book's term) are prose only.

| term | owner | not | reason |
|---|---|---|---|
| vendor lock-in | B16 ch. 20 | B14 ch. 27 | a property of the build-or-buy decision (switching cost, option to switch); B14 keeps *independent software vendor*, *ticker plant* |
| data-transfer charge | B14 ch. 16 | B15 ch. 26 (*egress charge*) | same concept, cloud-networking pricing, lower book; B15 drops *egress charge* and uses B14's term |
| public cloud | B14 ch. 16 | B15 ch. 26 (fallback) | B14's chapter is titled by it and comes first |
| network segmentation | B15 ch. 29 | — | security architecture; B14 does not define it |
| mean time to repair, mean time between failures, service-level agreement, service credit, route diversity, cross-connect, colocation | B14 ch. 9, 15 | — | connectivity contracts and products |
| time to restore, service-level indicator, service-level objective, error budget | B15 ch. 28 | — | internal engineering targets; B15 ch. 28 says how *time to restore* (an incident) differs from B14's *mean time to repair* (a circuit) |
| business continuity plan, operational resilience, important business service, impact tolerance, RTO, RPO, disaster-recovery site, exchange failover test | B14 ch. 28 | B16 ch. 17, 27 | the resilience rules as examined; B16 keeps *crisis management plan*, *crisis committee*; B15 keeps incident response |
| latency tier | B16 ch. 19 | B14 ch. 9 | the strategic speed class a firm buys; B14 ch. 9 describes port speeds and connectivity options without defining the term |
| critical path | B14 ch. 6 | — | timing closure; B16 defines *critical-path method*, a distinct term |
| front office, middle office, back office | B16 ch. 13 | B15 ch. 1, 21 | organisation terms; B15 uses them with a forward pointer |
| four-eyes principle | B16 ch. 12 | B15 ch. 16 | control principle; B15 uses it |
| trade capture, booking model, straight-through processing, confirmation matching, settlement instruction, reconciliation break, break ageing | B15 ch. 21–22 | B16 ch. 13 | the systems; B16 describes the function |
| entitlement, usage report, market-data audit, derived data, unit of count | B15 ch. 23 | B16 ch. 22 | data-system terms; B16 keeps *data budget*, *enterprise/derived-data/redistribution licence*, *back-billing* |
| reactive simulation | B15 ch. 11 | — | the exchsim-driven backtest, presented as Book 7's fidelity level 4 with the simulator standing in for the venue; *fidelity level* stays Book 7's |

## Rulings at the Books 17–18 sync (2026-09-29)

Books 1–16 keep their terms. Book 17 owns industry-landscape, employer-type, role, career-path and pay-structure
and pay-data terms; Book 18 owns interview-process, offer-process and question-method terms. Ties go to Book 17.
Planned maps: `sources/industry/DEFINITIONS.md` (112 terms), `sources/interviews/DEFINITIONS.md` (47); one exact
collision.

| term | owner | not | reason |
|---|---|---|---|
| return offer | B17 ch. 28 | B18 ch. 2 | an entry route (internship to job); B18 uses it |
| internship | B17 ch. 28 | — | entry route, added to B17's map (B18 uses it) |
| base salary, total compensation, sign-on bonus, guaranteed bonus, forfeiture, good-leaver provision, restricted stock unit, carried interest, partnership share | B17 ch. 13 | B18 ch. 7 | pay structure; the clauses of Book 16 ch. 10–11 stay Book 16's |
| graduate programme, lateral hire, notice period, pay band | B17 ch. 9, 28 | B18 | career paths |
| counteroffer, offer letter, exploding offer | B18 ch. 7 | B17 ch. 28 | offer process; B17 uses them |
| employee referral, agency recruiter, CV screen, online assessment, technical screen, final round, superday, take-home assignment, research case study, trading game, interview loop, hiring committee | B18 ch. 2–6 | B17 ch. 28–29 | interview and application process |
| role titles (quantitative researcher, risk trader, execution trader, desk strategist, model validator, research engineer, low-latency engineer, portfolio manager, structurer, compliance officer, head of desk …) | B17 ch. 16–25 | B18 ch. 1 | B18 uses B17's exact strings; *quant developer* stays B16 ch. 21, *machine-learning engineer* B12 ch. 28, *sales-trader* B1 ch. 2, *chief risk officer* B16 ch. 12 |

## Map (3540 terms)

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
| ACID transaction | 15 | 25-databases-and-sql |
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
| additional termination event | 16 | 18-legal-documentation |
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
| affirmation | 15 | 22-post-trade-systems |
| agency mortgage-backed security | 2 | 12-mortgages-and-agencies |
| agency portfolio trade | 10 | 22-portfolio-trades-and-risk-bids |
| agency recruiter | 18 | 03-applications |
| agent | 1 | 01-what-a-trading-firm-does |
| agent-based model | 10 | 27-build-an-agent-based-market |
| aggregate impact | 10 | 11-the-empirics-of-price-impact |
| aggregational Gaussianity | 7 | 05-stylised-facts-of-returns |
| aggressive-in-the-money strategy | 10 | 15-beyond-almgren-chriss |
| aim portfolio | 7 | 26-portfolio-construction-ii |
| aleatoric uncertainty | 12 | 11-probabilistic-models-and-uncertainty |
| alert triage | 15 | 30-surveillance-and-compliance-technology |
| algo wheel | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| algorithm supervisor | 17 | 16-trader |
| algorithmic differentiation | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| algorithmic stablecoin | 3 | 23-defi-credit-and-leverage |
| algorithmic trading | 10 | 24-market-quality-and-regulation |
| all-reduce | 12 | 23-training-infrastructure |
| all-to-all trading | 2 | 22-how-bonds-trade |
| Allan deviation | 14 | 04-time-synchronisation |
| allocated cost | 16 | 06-the-head-of-desks-job |
| allocated equity | 16 | 05-the-bank-markets-division |
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
| analytics library | 15 | 19-pricing-library-architecture |
| ancillary activity exemption | 3 | 13-getting-access-commodities-and-power |
| ancillary service | 3 | 05-power-markets-design |
| announcement premium | 8 | 07-earnings |
| announcement window | 7 | 11-fundamental-analyst-and-event-features |
| annualisation | 7 | 22-performance-measurement |
| annuity | 2 | 09-interest-rate-swaps |
| annuity measure | 4 | 05-girsanov-and-changes-of-numeraire |
| anomaly detection | 12 | 20-clustering-regimes-and-anomaly-detection |
| anomaly flag | 15 | 07-data-quality-and-lineage |
| anonymisation test | 12 | 14-large-language-models-in-finance |
| anti-gaming logic | 10 | 18-smart-order-routing |
| anti-procyclicality tool | 6 | 25-margin-models |
| antithetic variates | 4 | 26-monte-carlo |
| anycast | 14 | 17-where-the-crypto-venues-live |
| API gravity | 3 | 02-crude-oil |
| API key | 3 | 15-centralised-exchanges |
| app-chain | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| append-only file | 15 | 04-a-tick-store-on-open-formats |
| application binary interface | 15 | 09-native-extensions |
| arbitrage | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| arbitrage window | 3 | 03-refined-products-and-cracks |
| ARCH model | 4 | 18-volatility-models |
| archive node | 3 | 26-crypto-data-and-infrastructure |
| arena allocator | 13 | 06-cpp-for-latency-i-memory |
| arithmetic intensity | 15 | 14-accelerators-for-quantitative-work |
| ARMA process | 4 | 17-linear-time-series |
| array programming | 15 | 08-python-at-scale |
| arrival price | 7 | 19-simulation-versus-live |
| Arrow--Debreu security | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| as-of join | 7 | 03-point-in-time-data-and-the-biases |
| Asian option | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| assessment window | 3 | 01-physical-commodity-markets |
| asset manager | 1 | 01-what-a-trading-firm-does |
| asset owner | 17 | 08-asset-managers-pensions-sovereign-funds-and-insurers |
| asset tokenisation | 16 | 30-competition-and-the-future |
| asset--liability management | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| asset-backed trading | 9 | 22-storage-transport-and-physical-optionality |
| asset-swap spread | 2 | 21-corporate-bonds |
| assets under management | 1 | 01-what-a-trading-firm-does |
| assignment | 1 | 23-option-contracts-and-exchanges |
| asymmetric speed bump | 11 | 09-latency-arbitrage-and-its-defence |
| async runtime | 13 | 09-rust-for-low-latency |
| at-least-once delivery | 15 | 24-messaging-and-event-driven-architecture |
| at-most-once delivery | 15 | 24-messaging-and-event-driven-architecture |
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
| authorisation | 16 | 17-regulators-and-licences |
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
| automated coding assessment | 18 | 04-online-assessments |
| automated execution rule | 14 | 25-fixed-income-and-rfq-platform-connectivity |
| automated market maker | 3 | 20-automated-market-makers |
| autonomous system | 14 | 17-where-the-crypto-venues-live |
| autoregressive process | 4 | 17-linear-time-series |
| availability zone | 14 | 16-trading-in-a-public-cloud |
| availability-zone identifier | 14 | 16-trading-in-a-public-cloud |
| Avellaneda--Stoikov model | 11 | 03-inventory-models |
| average cost | 1 | 07-pnl-and-positions |
| average headcount | 17 | 11-reading-a-trading-firms-accounts |
| average tax rate | 17 | 15-pay-regulation-and-tax-by-location |
| average uniqueness | 12 | 02-targets-labels-and-sample-weights |
| average-price option | 3 | 12-commodity-options-and-structured-hedges |
| axe | 2 | 22-how-bonds-trade |
| axe-driven skew | 9 | 24-flow-market-making-at-a-bank |
| B-tree index | 15 | 25-databases-and-sql |
| Bachelier model | 2 | 13-the-rates-options-market |
| back bet | 3 | 27-prediction-and-betting-markets |
| back office | 16 | 13-operations |
| back-adjustment | 7 | 02-market-data-for-research |
| back-billing | 16 | 22-data-strategy-and-costs |
| back-pressure | 13 | 12-queues-ring-buffers-and-shared-memory |
| back-running | 3 | 22-maximal-extractable-value |
| backbone | 5 | 11-sabr-and-smile-dynamics |
| backfill bias | 7 | 03-point-in-time-data-and-the-biases |
| backpropagation | 12 | 07-neural-networks-for-noisy-tabular-data |
| backtest | 7 | 16-vectorised-backtests |
| backtest engine | 15 | 11-backtest-engine-architecture |
| backtest overfitting | 7 | 20-overfitting |
| backward error | 4 | 25-floating-point-and-numerical-linear-algebra |
| backward induction | 18 | 12-brainteasers-and-logic |
| backward stability | 4 | 25-floating-point-and-numerical-linear-algebra |
| backward-looking caplet | 6 | 10-modelling-overnight-rate-products |
| backward-looking rate | 6 | 10-modelling-overnight-rate-products |
| backwardation | 1 | 21-basis-roll-and-delivery |
| bag of words | 12 | 13-text-from-bag-of-words-to-embeddings |
| bagging | 12 | 05-trees-and-boosting |
| bail-in | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| balance-sheet charge | 16 | 05-the-bank-markets-division |
| balance-sheet cost | 9 | 12-swap-spread-and-asset-swap-trades |
| balancing group | 3 | 13-getting-access-commodities-and-power |
| balancing responsible party | 3 | 06-power-markets-trading |
| banging the close | 2 | 17-fixings-and-flows |
| bank run | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| banking book | 6 | 23-regulatory-capital-for-trading-books |
| bankruptcy price | 3 | 18-margin-liquidation-and-loss-allocation |
| bar | 7 | 02-market-data-for-research |
| bare-metal instance | 14 | 16-trading-in-a-public-cloud |
| bargaining power | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| barrier option | 2 | 19-the-fx-options-market |
| barrier rebate | 5 | 15-barriers-and-digitals |
| barrier shift | 5 | 15-barriers-and-digitals |
| base correlation | 2 | 24-credit-indices-and-tranches |
| base currency | 2 | 14-the-fx-market |
| base fee | 3 | 14-blockchains-for-traders |
| base salary | 17 | 13-how-pay-works |
| baseboard management controller | 14 | 08-servers |
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
| batch processing | 15 | 01-the-platform-map |
| batch window | 15 | 20-the-risk-grid |
| Bates model | 5 | 13-jumps-and-levy-models |
| battery arbitrage | 9 | 23-power-and-gas-trading |
| Bayes--Nash equilibrium | 4 | 29-games-auctions-and-information |
| Bayesian game | 4 | 29-games-auctions-and-information |
| Bayesian update | 2 | 30-market-making-games |
| bear flattening | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| behavioural question | 18 | 28-behavioural-and-fit |
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
| best alternative to a negotiated agreement | 16 | 23-commercial-relationships-with-venues-brokers-and-vendors |
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
| bilateral credit screen | 14 | 24-fx-connectivity |
| bilateral CVA | 6 | 18-credit-and-debit-valuation-adjustments |
| bilateral repo | 2 | 05-repo-and-specials |
| bill of lading | 3 | 01-physical-commodity-markets |
| bill of materials | 14 | 29-build-a-connectivity-plan |
| binary log | 13 | 23-logging-capture-and-replay |
| binding capital constraint | 16 | 05-the-bank-markets-division |
| binomial model | 5 | 02-the-binomial-model |
| bipower variation | 4 | 21-high-frequency-econometrics |
| birth--death process | 4 | 08-markov-chains-and-queues |
| bisection method | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| bit packing | 15 | 03-columnar-formats |
| bitemporal data | 7 | 03-point-in-time-data-and-the-biases |
| bitwise reproducibility | 4 | 25-floating-point-and-numerical-linear-algebra |
| Black model | 5 | 03-black-scholes-three-ways |
| Black--Karasinski model | 6 | 07-short-rate-models |
| Black--Litterman model | 7 | 26-portfolio-construction-ii |
| Black--Scholes equation | 5 | 03-black-scholes-three-ways |
| Black--Scholes formula | 5 | 03-black-scholes-three-ways |
| Black--Scholes model | 5 | 03-black-scholes-three-ways |
| blackout period | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| blameless review | 15 | 28-observability-and-incident-response |
| blast radius | 15 | 01-the-platform-map |
| blind risk bid | 10 | 22-portfolio-trades-and-risk-bids |
| block allocation | 15 | 21-trade-capture-and-booking |
| block builder | 3 | 22-maximal-extractable-value |
| block engine | 14 | 21-on-chain-connectivity |
| block leave | 6 | 28-operational-risk-and-rogue-trading |
| block order | 3 | 05-power-markets-design |
| block RAM | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| block trade | 1 | 02-the-sell-side |
| blockchain | 3 | 14-blockchains-for-traders |
| blue--green deployment | 15 | 27-testing-and-continuous-delivery |
| BM25 | 12 | 14-large-language-models-in-finance |
| board lot | 1 | 12-asian-and-emerging-equity-markets |
| bond floor | 5 | 21-convertibles-and-the-credit-equity-link |
| bond-equivalent yield | 2 | 02-money-markets |
| Bonferroni correction | 4 | 12-testing-and-multiple-testing |
| bonus cap | 17 | 15-pay-regulation-and-tax-by-location |
| bonus pool | 16 | 10-hiring-and-compensation |
| book builder | 13 | 19-the-order-book-builder |
| book checksum | 3 | 26-crypto-data-and-infrastructure |
| book resilience | 10 | 03-empirical-facts-of-order-books |
| book-to-price ratio | 8 | 06-value-quality-and-low-risk |
| booking | 15 | 21-trade-capture-and-booking |
| booking model | 15 | 21-trade-capture-and-booking |
| bookmaker | 3 | 27-prediction-and-betting-markets |
| bootstrap | 4 | 13-resampling |
| bootstrap percentile interval | 4 | 13-resampling |
| Border Gateway Protocol | 14 | 19-cross-region-crypto-networks |
| borrow fee | 1 | 06-financing |
| borrow-fee signal | 8 | 08-short-interest-borrow-and-crowding |
| boundary clock | 14 | 04-time-synchronisation |
| boundary-crossing cost | 15 | 09-native-extensions |
| bounds-check elimination | 13 | 09-rust-for-low-latency |
| box spread | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| branch misprediction | 13 | 02-cpu-microarchitecture |
| branch prediction | 13 | 02-cpu-microarchitecture |
| branching ratio | 4 | 07-point-processes-and-hawkes-processes |
| breadth | 7 | 15-from-signal-to-forecast |
| break ageing | 15 | 22-post-trade-systems |
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
| Brier score | 16 | 26-culture-and-decision-making |
| broker | 1 | 04-exchanges-brokers-venues |
| broker scorecard | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| broker-dealer | 1 | 02-the-sell-side |
| brokerless messaging | 15 | 24-messaging-and-event-driven-architecture |
| Brownian bridge | 4 | 02-brownian-motion |
| Brownian bridge construction | 4 | 26-monte-carlo |
| Brownian motion | 4 | 02-brownian-motion |
| Brownian motion with drift | 4 | 02-brownian-motion |
| bucket-shaped trajectory | 10 | 15-beyond-almgren-chriss |
| bucketed sensitivity | 6 | 03-rates-risk |
| buffer protocol | 15 | 09-native-extensions |
| buffer rule | 1 | 15-index-construction-and-rebalancing |
| build against buy | 16 | 20-build-against-buy |
| bulk volume classification | 7 | 09-trade-flow-features |
| bull steepening | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| bump-and-reprice | 5 | 04-greeks-and-the-hedging-pnl |
| Bund | 2 | 07-european-and-japanese-government-bonds |
| bundle | 2 | 08-short-term-interest-rate-futures |
| bundle bid | 11 | 25-on-chain-trading |
| burn analysis | 3 | 11-freight-weather-and-other-corners |
| burn-in | 4 | 14-bayesian-methods |
| burn-in test | 14 | 08-servers |
| burn-rate alert | 15 | 28-observability-and-incident-response |
| burnout | 6 | 12-mortgage-modelling |
| bus factor | 16 | 21-engineering-organisation-design |
| business continuity plan | 14 | 28-disaster-recovery-and-regulatory-requirements |
| business time | 5 | 08-parametrising-the-surface |
| busted convertible | 9 | 08-convertible-arbitrage |
| busy polling | 13 | 13-linux-tuning |
| butterfly | 2 | 19-the-fx-options-market |
| butterfly arbitrage | 5 | 07-implied-volatility-and-its-surface |
| buy side | 1 | 03-the-buy-side |
| buy-in | 1 | 16-stock-loan-and-short-selling |
| cable landing station | 14 | 13-long-haul-fibre |
| cache coherence | 13 | 03-memory-hierarchy-and-caches |
| cache line | 13 | 03-memory-hierarchy-and-caches |
| cache miss | 13 | 03-memory-hierarchy-and-caches |
| calendar arbitrage | 5 | 07-implied-volatility-and-its-surface |
| calendar effect | 8 | 23-seasonality-and-calendar-effects |
| calendar month average | 3 | 02-crude-oil |
| calendar spread | 1 | 19-matching-algorithms-and-implied-spreads |
| calendar-spread option | 3 | 12-commodity-options-and-structured-hedges |
| calibrated interval | 18 | 09-estimation |
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
| canonical trade model | 15 | 21-trade-capture-and-booking |
| cap | 2 | 13-the-rates-options-market |
| cap-and-trade | 3 | 07-emissions-and-environmental-markets |
| capacity curve | 7 | 28-capacity-decay-and-crowding |
| capacity estimate | 18 | 26-system-design |
| capacity market | 3 | 05-power-markets-design |
| capacity right | 16 | 25-launching-a-fund-and-raising-capital |
| capital charge | 16 | 07-limits-and-capital-allocation |
| capital control | 2 | 18-emerging-market-fx-and-ndfs |
| capital valuation adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| capital-protected note | 5 | 19-the-structured-products-business |
| capital-structure arbitrage | 6 | 14-structural-credit-models |
| caplet | 2 | 13-the-rates-options-market |
| caplet stripping | 6 | 04-vanilla-rates-options |
| caplet volatility | 6 | 04-vanilla-rates-options |
| capture appliance | 14 | 05-capturing-and-monitoring-the-network |
| capture decay | 11 | 28-pnl-analytics-and-the-strategy-lifecycle |
| capture price | 3 | 06-power-markets-trading |
| carbon border adjustment mechanism | 3 | 07-emissions-and-environmental-markets |
| carbon credit | 3 | 07-emissions-and-environmental-markets |
| Carr--Madan formula | 5 | 24-fourier-pricing-and-calibration-engineering |
| carried interest | 17 | 13-how-pay-works |
| carrier-neutral data centre | 14 | 11-the-european-map |
| carry | 1 | 07-pnl-and-positions |
| carry crash | 8 | 20-carry-across-asset-classes |
| carry strategy | 8 | 20-carry-across-asset-classes |
| case management system | 15 | 30-surveillance-and-compliance-technology |
| cash annuity | 6 | 04-vanilla-rates-options |
| cash creation | 3 | 19-dated-futures-options-and-etfs |
| cash gamma | 5 | 04-greeks-and-the-hedging-pnl |
| cash settlement | 1 | 21-basis-roll-and-delivery |
| cash-and-carry trade | 3 | 10-forward-curves-storage-and-convenience-yield |
| cash-settled swaption | 6 | 04-vanilla-rates-options |
| casting out nines | 18 | 08-mental-arithmetic |
| catastrophic cancellation | 4 | 25-floating-point-and-numerical-linear-algebra |
| causal convolution | 12 | 08-sequence-models-on-order-books |
| CCP basis | 2 | 10-swap-clearing-and-the-ccp-basis |
| central counterparty | 1 | 05-clearing-and-settlement |
| central risk book | 9 | 25-the-central-risk-book |
| central securities depository | 1 | 05-clearing-and-settlement |
| central team | 16 | 21-engineering-organisation-design |
| central-bank backstop | 2 | 07-european-and-japanese-government-bonds |
| central-bank reaction trade | 9 | 15-fx-flow-strategies |
| centralised exchange | 3 | 15-centralised-exchanges |
| centre book | 16 | 03-the-multi-manager-platform |
| certainty equivalent | 4 | 09-stochastic-control |
| certificate of deposit | 2 | 02-money-markets |
| certification regime | 17 | 16-trader |
| CEX--DEX arbitrage | 3 | 22-maximal-extractable-value |
| CFL condition | 4 | 27-finite-difference-methods |
| champion--challenger | 12 | 27-monitoring-and-retraining |
| change control | 15 | 27-testing-and-continuous-delivery |
| change of measure | 4 | 01-probability-at-speed |
| change of numeraire | 4 | 05-girsanov-and-changes-of-numeraire |
| change-the-bank spending | 16 | 19-technology-strategy |
| characteristic exponent | 4 | 06-jump-processes |
| characteristic function | 4 | 01-probability-at-speed |
| chartist agent | 10 | 27-build-an-agent-based-market |
| cheapest-to-deliver | 2 | 06-bond-futures |
| checkpointing | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| Cheyette model | 6 | 10-modelling-overnight-rate-products |
| chief risk officer | 16 | 12-the-risk-management-function |
| child order | 10 | 14-the-almgren-chriss-framework |
| Cholesky factorisation | 4 | 25-floating-point-and-numerical-linear-algebra |
| Christoffersen test | 6 | 21-market-risk-measures |
| chromatic dispersion | 14 | 13-long-haul-fibre |
| chunked processing | 15 | 08-python-at-scale |
| Classification of Instructional Programs | 17 | 29-education-pipelines |
| classifier two-sample test | 12 | 16-generative-models-and-synthetic-data |
| clawback | 16 | 10-hiring-and-compensation |
| clean dark spread | 3 | 07-emissions-and-environmental-markets |
| clean price | 2 | 03-government-bonds |
| clean spark spread | 3 | 07-emissions-and-environmental-markets |
| clean-up trade | 10 | 17-child-order-placement |
| clearing | 1 | 05-clearing-and-settlement |
| clearing broker | 1 | 29-getting-access-equities |
| clearing broker (swaps) | 2 | 28-getting-access-rates-credit |
| clearing mandate | 2 | 10-swap-clearing-and-the-ccp-basis |
| clearing member | 1 | 30-getting-access-futures-options |
| clearing-firm credit control | 14 | 23-futures-connectivity |
| clearly erroneous trade | 1 | 31-stress-case-studies |
| click trader | 17 | 16-trader |
| client clearing | 2 | 10-swap-clearing-and-the-ccp-basis |
| client tiering | 9 | 24-flow-market-making-at-a-bank |
| cliquet | 5 | 16-asians-lookbacks-cliquets-and-forward-starts |
| clock domain crossing | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| clock offset | 14 | 04-time-synchronisation |
| clock servo | 14 | 04-time-synchronisation |
| close-out amount | 6 | 18-credit-and-debit-valuation-adjustments |
| close-out netting | 6 | 17-counterparty-exposure |
| closed-end fund discount | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| closing price | 1 | 13-auctions |
| cloud backbone | 14 | 19-cross-region-crypto-networks |
| cloud bursting | 15 | 26-cloud-against-on-premises |
| cloud region | 3 | 26-crypto-data-and-infrastructure |
| clustered feature importance | 12 | 06-feature-engineering-selection-and-importance |
| clustered standard errors | 4 | 16-linear-models-under-stress |
| clustering | 12 | 20-clustering-regimes-and-anomaly-detection |
| CMS convexity adjustment | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| CMS spread option | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| co-terminal swaption | 6 | 09-bermudans-and-callables |
| code review | 15 | 15-the-research-environment |
| coherent risk measure | 6 | 21-market-risk-measures |
| coin-margined contract | 3 | 19-dated-futures-options-and-etfs |
| cointegrating vector | 4 | 20-multivariate-series-and-cointegration |
| cointegration | 4 | 20-multivariate-series-and-cointegration |
| cointegration rank | 4 | 20-multivariate-series-and-cointegration |
| cold path | 13 | 07-cpp-for-latency-ii-compile-time |
| cold wallet | 3 | 24-the-crypto-trading-business |
| collar | 3 | 12-commodity-options-and-structured-hedges |
| collateral choice option | 6 | 02-multi-curve-and-collateral-discounting |
| collateral dispute | 16 | 13-operations |
| collateral management | 16 | 13-operations |
| collateral mirroring | 3 | 25-getting-access-crypto-venues |
| collateral rate | 6 | 02-multi-curve-and-collateral-discounting |
| collateral return | 3 | 10-forward-curves-storage-and-convenience-yield |
| collateral threshold | 6 | 17-counterparty-exposure |
| collateralised loan obligation | 2 | 25-loans-clos-and-securitisation |
| collective action clause | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| colocation | 14 | 09-colocation-products-and-how-they-are-sold |
| colocation cabinet | 14 | 09-colocation-products-and-how-they-are-sold |
| colocation cage | 14 | 09-colocation-products-and-how-they-are-sold |
| column chunk | 15 | 03-columnar-formats |
| columnar layout | 15 | 03-columnar-formats |
| combinatorial purged cross-validation | 7 | 20-overfitting |
| combinatorially symmetric cross-validation | 7 | 20-overfitting |
| commercial paper | 2 | 02-money-markets |
| commission sharing agreement | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| Commitments of Traders report | 3 | 09-agriculturals-and-softs |
| commodity index | 3 | 10-forward-curves-storage-and-convenience-yield |
| commodity pool operator | 16 | 17-regulators-and-licences |
| commodity swap | 3 | 01-physical-commodity-markets |
| commodity trading advisor | 1 | 03-the-buy-side |
| commodity trading house | 3 | 01-physical-commodity-markets |
| common equity tier 1 capital | 16 | 05-the-bank-markets-division |
| common-value auction | 4 | 29-games-auctions-and-information |
| communications archive | 15 | 30-surveillance-and-compliance-technology |
| communications surveillance | 15 | 30-surveillance-and-compliance-technology |
| comomentum | 7 | 28-capacity-decay-and-crowding |
| company registry | 17 | 11-reading-a-trading-firms-accounts |
| compare-and-swap | 13 | 11-lock-free-programming |
| compensated Poisson process | 4 | 06-jump-processes |
| compensated summation | 4 | 25-floating-point-and-numerical-linear-algebra |
| compensation ratio | 16 | 01-the-economics-of-a-trading-firm |
| compensator | 4 | 07-point-processes-and-hawkes-processes |
| compile-time evaluation | 13 | 07-cpp-for-latency-ii-compile-time |
| compiler barrier | 13 | 02-cpu-microarchitecture |
| compiler intrinsic | 13 | 14-vector-instructions-and-data-parallel-code |
| complementary counting | 18 | 10-probability-i |
| complete market | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| complex order book | 1 | 24-options-market-structure |
| compliance officer | 17 | 24-risk-operations-product-control-and-compliance |
| component share | 10 | 08-fragmentation-and-routing |
| composite option | 5 | 17-multi-asset-options |
| composite price | 2 | 22-how-bonds-trade |
| composite signal | 7 | 14-signal-combination |
| compound correlation | 6 | 15-portfolio-credit |
| compound Poisson process | 4 | 06-jump-processes |
| compounding in arrears | 2 | 01-central-banks-and-the-short-rate |
| compression ratio | 15 | 02-capturing-and-storing-tick-data |
| computational notebook | 15 | 15-the-research-environment |
| compute cluster | 15 | 13-distributed-compute-and-schedulers |
| compute-bound kernel | 15 | 14-accelerators-for-quantitative-work |
| concentrated liquidity | 3 | 20-automated-market-makers |
| concentration add-on | 6 | 25-margin-models |
| concentration limit | 16 | 07-limits-and-capital-allocation |
| concept drift | 12 | 12-online-learning-and-drift |
| condition number | 4 | 25-floating-point-and-numerical-linear-algebra |
| conditional autoencoder | 12 | 09-cross-sectional-deep-models |
| conditional expectation | 4 | 01-probability-at-speed |
| conditional heteroskedasticity | 4 | 18-volatility-models |
| conditional intensity | 4 | 07-point-processes-and-hawkes-processes |
| conditional order | 10 | 09-dark-pools-and-blocks |
| conditional prepayment rate | 2 | 12-mortgages-and-agencies |
| confidentiality agreement | 16 | 11-intellectual-property-and-non-competes |
| configurable logic block | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| configuration as data | 15 | 16-signal-serving-and-parameter-management |
| configuration drift | 15 | 16-signal-serving-and-parameter-management |
| configuration schema | 15 | 16-signal-serving-and-parameter-management |
| confirmation matching | 15 | 22-post-trade-systems |
| conflation | 13 | 12-queues-ring-buffers-and-shared-memory |
| conformal prediction | 12 | 11-probabilistic-models-and-uncertainty |
| congestion rent | 3 | 05-power-markets-design |
| conjugate gradient method | 4 | 25-floating-point-and-numerical-linear-algebra |
| conjugate prior | 4 | 14-bayesian-methods |
| connection pool | 13 | 17-websocket-rest-tls-and-json-at-speed |
| connection sharding | 14 | 20-api-engineering-for-crypto-venues |
| connectivity plan | 14 | 29-build-a-connectivity-plan |
| consensus forecast | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| consensus protocol | 3 | 14-blockchains-for-traders |
| consistent estimator | 4 | 11-estimation |
| consistent scheme | 4 | 27-finite-difference-methods |
| consolidated accounts | 17 | 11-reading-a-trading-firms-accounts |
| consolidated fair price | 11 | 02-fair-value |
| consolidated tape provider | 1 | 11-european-equity-market-structure |
| constant-maturity swap | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| constant-product market maker | 3 | 20-automated-market-makers |
| consumer group | 15 | 24-messaging-and-event-driven-architecture |
| consumer offset | 15 | 24-messaging-and-event-driven-architecture |
| container image | 15 | 15-the-research-environment |
| contango | 1 | 21-basis-roll-and-delivery |
| content-addressed storage | 7 | 29-build-a-research-workflow |
| context switch | 13 | 13-linux-tuning |
| context window | 12 | 14-large-language-models-in-finance |
| contextual bandit | 12 | 17-reinforcement-learning-foundations |
| contingent claim | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| contingent convertible bond | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| contingent credit default swap | 6 | 20-the-valuation-adjustment-desk |
| continuation region | 4 | 10-optimal-stopping-and-impulse-control |
| continuous delivery | 15 | 27-testing-and-continuous-delivery |
| continuous futures series | 7 | 02-market-data-for-research |
| continuous integration | 15 | 27-testing-and-continuous-delivery |
| continuous ranked probability score | 12 | 11-probabilistic-models-and-uncertainty |
| continuous-time Markov chain | 4 | 08-markov-chains-and-queues |
| contract for difference | 1 | 17-delta-one-instruments |
| contract multiplier | 1 | 18-futures-contracts-and-exchanges |
| contrastive learning | 12 | 10-representation-learning |
| control function | 17 | 24-risk-operations-product-control-and-compliance |
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
| coordination cost | 16 | 21-engineering-organisation-design |
| copula | 4 | 15-robust-statistics-and-heavy-tails |
| core isolation | 13 | 13-linux-tuning |
| core--periphery network | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| corporate-action event | 15 | 06-reference-data-and-symbology-services |
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
| counteroffer | 18 | 07-offers-compensation-and-non-competes |
| counterparty credit risk | 6 | 17-counterparty-exposure |
| counterparty exposure | 6 | 17-counterparty-exposure |
| counterparty master | 15 | 06-reference-data-and-symbology-services |
| counting process | 4 | 07-point-processes-and-hawkes-processes |
| coupling argument | 18 | 11-probability-ii |
| coupon | 2 | 03-government-bonds |
| coupon barrier | 5 | 18-autocallables |
| courtsiding | 11 | 26-prediction-and-sports-market-making |
| covariance matrix | 4 | 22-covariance-estimation-and-random-matrices |
| covariate shift | 12 | 12-online-learning-and-drift |
| covenant | 2 | 21-corporate-bonds |
| covenant-lite | 2 | 25-loans-clos-and-securitisation |
| cover price | 11 | 22-bond-and-etf-request-for-quote-market-making |
| coverage probability | 4 | 13-resampling |
| coverage requirement | 17 | 26-hours-rhythm-and-intensity |
| covered interest parity | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| Cox process | 4 | 07-point-processes-and-hawkes-processes |
| Cox--Ross--Rubinstein tree | 5 | 02-the-binomial-model |
| CPU affinity | 13 | 13-linux-tuning |
| CPU feature dispatch | 13 | 14-vector-instructions-and-data-parallel-code |
| CPU steal time | 14 | 16-trading-in-a-public-cloud |
| crack spread | 3 | 03-refined-products-and-cracks |
| Crank--Nicolson scheme | 4 | 27-finite-difference-methods |
| crash-hedged carry | 9 | 14-cross-currency-basis-and-fx-carry |
| creation basket | 1 | 14-exchange-traded-funds |
| creation fee | 11 | 12-etf-market-making |
| creation unit | 1 | 14-exchange-traded-funds |
| credible interval | 4 | 14-bayesian-methods |
| credit attribution | 16 | 09-managing-researchers-traders-and-engineers |
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
| crisis committee | 16 | 27-crisis-management |
| crisis management plan | 16 | 27-crisis-management |
| critical path | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| critical-path method | 16 | 24-entering-a-new-market |
| crop year | 3 | 09-agriculturals-and-softs |
| cross margin | 3 | 18-margin-liquidation-and-loss-allocation |
| cross rate | 2 | 14-the-fx-market |
| cross-asset feature | 7 | 10-cross-sectional-and-cross-asset-features |
| cross-asset hedge ratio | 9 | 09-capital-structure-arbitrage |
| cross-connect | 14 | 09-colocation-products-and-how-they-are-sold |
| cross-currency basis | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| cross-currency basis swap | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| cross-default clause | 16 | 18-legal-documentation |
| cross-exchange market making | 11 | 24-crypto-high-frequency-trading-on-centralised-venues |
| cross-gamma | 6 | 03-rates-risk |
| cross-impact | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| cross-impact matrix | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| cross-instrument fair price | 11 | 02-fair-value |
| cross-listed futures | 11 | 13-index-and-basket-arbitrage |
| cross-sectional momentum | 8 | 05-momentum |
| cross-sectional z-score | 7 | 06-anatomy-of-a-predictor |
| cross-source check | 15 | 07-data-quality-and-lineage |
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
| crystallisation | 16 | 04-the-asset-manager-and-the-fund |
| CS01 | 6 | 13-reduced-form-credit |
| CSA discounting | 6 | 02-multi-curve-and-collateral-discounting |
| cubic spline | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| cum-ex trading | 16 | 15-finance-product-control-and-tax |
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
| custodian | 16 | 04-the-asset-manager-and-the-fund |
| custom basket | 11 | 12-etf-market-making |
| customer asset segregation | 3 | 15-centralised-exchanges |
| customer priority | 1 | 24-options-market-structure |
| CUSUM test | 7 | 13-half-life-decay-and-stability |
| cut-through decision | 14 | 07-programmable-hardware-ii-trading-designs |
| cut-through switching | 14 | 02-switches-and-layer-1-devices |
| CV screen | 18 | 03-applications |
| CVA risk capital | 6 | 19-funding-margin-and-capital-adjustments |
| cycle-accurate model | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| daily P\&L attribution | 8 | 01-anatomy-of-a-stat-arb-book |
| daily settlement price | 1 | 18-futures-contracts-and-exchanges |
| dark fibre | 14 | 13-long-haul-fibre |
| dark pool | 1 | 09-us-equity-market-structure |
| dark spread | 3 | 05-power-markets-design |
| dash for cash | 2 | 04-the-treasury-market |
| data augmentation | 12 | 10-representation-learning |
| data budget | 16 | 22-data-strategy-and-costs |
| data contract | 15 | 07-data-quality-and-lineage |
| data decay | 8 | 16-alternative-data-strategies |
| data engineer | 17 | 21-machine-learning-and-data-engineer |
| data gravity | 15 | 26-cloud-against-on-premises |
| data lineage | 15 | 07-data-quality-and-lineage |
| data loader | 12 | 23-training-infrastructure |
| data page | 15 | 03-columnar-formats |
| data parallelism | 12 | 23-training-infrastructure |
| data race | 13 | 09-rust-for-low-latency |
| data scientist | 17 | 21-machine-learning-and-data-engineer |
| data snapshot | 7 | 29-build-a-research-workflow |
| data snooping | 4 | 12-testing-and-multiple-testing |
| data surprise | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| data trial | 7 | 12-alternative-and-text-data |
| data versioning | 12 | 25-experiment-tracking-and-reproducibility |
| data vintage | 7 | 03-point-in-time-data-and-the-biases |
| data-access layer | 15 | 11-backtest-engine-architecture |
| data-flow map | 15 | 01-the-platform-map |
| data-loss prevention | 15 | 29-security |
| data-quality rule | 15 | 07-data-quality-and-lineage |
| data-transfer charge | 14 | 16-trading-in-a-public-cloud |
| dataframe | 15 | 10-dataframes |
| Dated Brent | 3 | 02-crude-oil |
| dated future | 3 | 19-dated-futures-options-and-etfs |
| day-ahead market | 3 | 05-power-markets-design |
| day-ahead-intraday spread | 9 | 23-power-and-gas-trading |
| day-count convention | 2 | 03-government-bonds |
| day-one P\&L | 5 | 27-managing-an-exotic-book |
| days to cover | 1 | 16-stock-loan-and-short-selling |
| days to liquidate | 16 | 28-case-studies-i |
| de-risking ladder | 16 | 08-managing-a-book-through-drawdown |
| dead-letter queue | 15 | 24-messaging-and-event-driven-architecture |
| deal spread | 8 | 11-merger-arbitrage |
| dealer gamma | 1 | 26-zero-day-options-and-retail-flow |
| dealer-to-client platform | 2 | 04-the-treasury-market |
| dealing on own account | 16 | 17-regulators-and-licences |
| debit valuation adjustment | 6 | 18-credit-and-debit-valuation-adjustments |
| decay kernel | 10 | 12-transient-impact-and-propagator-models |
| decentralised exchange | 3 | 20-automated-market-makers |
| decision journal | 16 | 26-culture-and-decision-making |
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
| deferral buyout | 16 | 10-hiring-and-compensation |
| deferred compensation | 16 | 10-hiring-and-compensation |
| deferred formatting | 13 | 23-logging-capture-and-replay |
| defined-benefit pension plan | 17 | 08-asset-managers-pensions-sovereign-funds-and-insurers |
| deflated Sharpe ratio | 4 | 12-testing-and-multiple-testing |
| deflation floor | 2 | 11-inflation-markets |
| delay cost | 7 | 23-measuring-market-making-and-execution |
| delisting return | 7 | 04-universe-symbology-and-corporate-actions |
| deliverable basket | 2 | 06-bond-futures |
| delivery versus payment | 1 | 05-clearing-and-settlement |
| delta | 1 | 26-zero-day-options-and-retail-flow |
| delta encoding | 15 | 03-columnar-formats |
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
| deployment pipeline | 15 | 27-testing-and-continuous-delivery |
| deposit beta | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| depositary receipt | 1 | 17-delta-one-instruments |
| depositary receipt issuance | 11 | 14-depositary-receipts-and-dual-listings |
| depositary receipt ratio | 11 | 14-depositary-receipts-and-dual-listings |
| depth imbalance | 7 | 08-order-book-features |
| depth profile | 7 | 08-order-book-features |
| derived data | 15 | 23-market-data-distribution-and-entitlements |
| derived-data licence | 16 | 22-data-strategy-and-costs |
| descriptor ring | 14 | 03-network-cards-and-kernel-bypass |
| designated contract market | 3 | 13-getting-access-commodities-and-power |
| designated market maker | 1 | 29-getting-access-equities |
| designation notice | 2 | 27-getting-access-fx |
| desk strategist | 17 | 18-bank-quant |
| destination flexibility | 3 | 04-natural-gas-and-lng |
| detachment point | 2 | 24-credit-indices-and-tranches |
| detailed balance | 4 | 08-markov-chains-and-queues |
| determinations committee | 2 | 23-credit-default-swaps |
| deterministic replay | 13 | 23-logging-capture-and-replay |
| device locality | 13 | 04-multi-socket-machines-and-interconnects |
| devirtualisation | 13 | 07-cpp-for-latency-ii-compile-time |
| DEX aggregator | 3 | 20-automated-market-makers |
| Dickey--Fuller test | 4 | 17-linear-time-series |
| dictionary encoding | 15 | 03-columnar-formats |
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
| direct-attach cable | 14 | 02-switches-and-layer-1-devices |
| dirty price | 2 | 03-government-bonds |
| disaster-recovery site | 14 | 28-disaster-recovery-and-regulatory-requirements |
| disclosure bias | 17 | 12-revenue-and-profit-across-the-industry |
| discount curve | 6 | 02-multi-curve-and-collateral-discounting |
| discount yield | 2 | 02-money-markets |
| discounting switch | 6 | 02-multi-curve-and-collateral-discounting |
| discrete Fourier transform | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| discrete hedging error | 5 | 04-greeks-and-the-hedging-pnl |
| discretionary bonus | 16 | 10-hiring-and-compensation |
| discretionary manager | 17 | 04-quantitative-hedge-funds-and-systematic-managers |
| discriminatory auction | 4 | 29-games-auctions-and-information |
| dispersion compensation | 14 | 13-long-haul-fibre |
| dispersion trade | 5 | 17-multi-asset-options |
| dispersion weighting | 9 | 02-dispersion-and-correlation |
| disposable pay after housing | 17 | 27-locations |
| disruptor pattern | 13 | 12-queues-ring-buffers-and-shared-memory |
| dissemination cap | 2 | 22-how-bonds-trade |
| dissemination fairness | 14 | 12-the-asia-pacific-map |
| distance method | 8 | 04-pairs-and-baskets |
| distance to default | 6 | 14-structural-credit-models |
| distressed debt | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| distributed tracing | 15 | 28-observability-and-incident-response |
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
| dominated alternative | 17 | 30-choosing |
| Doob martingale | 4 | 01-probability-at-speed |
| double volume cap | 1 | 11-european-equity-market-structure |
| double-barrier option | 5 | 15-barriers-and-digitals |
| doubly robust estimator | 12 | 17-reinforcement-learning-foundations |
| downsampling | 15 | 05-time-series-databases-and-the-alternatives |
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
| due diligence questionnaire | 16 | 25-launching-a-fund-and-raising-capital |
| Dupire formula | 5 | 09-local-volatility |
| duration-neutral butterfly | 9 | 10-government-bond-relative-value |
| Dutch auction | 4 | 29-games-auctions-and-information |
| DV01 | 2 | 03-government-bonds |
| dynamic batching | 12 | 26-low-latency-inference |
| dynamic dispatch | 13 | 07-cpp-for-latency-ii-compile-time |
| dynamic frequency scaling | 13 | 02-cpu-microarchitecture |
| dynamic margining | 16 | 29-case-studies-ii |
| dynamic price band | 10 | 25-circuit-breakers-and-halts |
| dynamic programming | 4 | 09-stochastic-control |
| dynamic VWAP | 10 | 16-benchmark-algorithms |
| eager evaluation | 15 | 10-dataframes |
| early stopping | 12 | 05-trees-and-boosting |
| early-exercise premium | 5 | 06-american-options-and-early-exercise |
| earnings surprise | 7 | 11-fundamental-analyst-and-event-features |
| earnings-revision strategy | 8 | 07-earnings |
| earth bulge | 14 | 14-long-haul-wireless |
| economic capital | 16 | 07-limits-and-capital-allocation |
| economic link | 7 | 10-cross-sectional-and-cross-asset-features |
| economic moat | 16 | 30-competition-and-the-future |
| economic rationale | 7 | 01-the-research-process |
| economic release | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| economic value of equity | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| economic-surprise signal | 9 | 16-systematic-macro |
| edge | 2 | 29-thinking-in-expected-value |
| edge network | 14 | 17-where-the-crypto-venues-live |
| effective breadth | 7 | 15-from-signal-to-forecast |
| effective challenge | 6 | 26-model-risk-and-validation |
| effective duration | 2 | 12-mortgages-and-agencies |
| effective lower bound | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| effective sample size | 4 | 14-bayesian-methods |
| effective spread | 1 | 10-retail-flow-and-wholesaling |
| effective tick size | 10 | 07-fees-rebates-and-venue-economics |
| efficient frontier | 7 | 25-portfolio-construction-i |
| efficient trading frontier | 10 | 14-the-almgren-chriss-framework |
| egress queue | 14 | 01-networking-for-trading |
| eigenportfolio | 8 | 03-residual-and-principal-component-stat-arb |
| eigenvalue clipping | 4 | 22-covariance-estimation-and-random-matrices |
| elastic net | 4 | 16-linear-models-under-stress |
| electronic communication network | 2 | 14-the-fx-market |
| electronic market maker | 11 | 01-the-business-of-market-making |
| embargo | 7 | 20-overfitting |
| embarrassingly parallel workload | 15 | 13-distributed-compute-and-schedulers |
| embedded database | 15 | 05-time-series-databases-and-the-alternatives |
| embedded team | 16 | 21-engineering-organisation-design |
| emerging manager | 16 | 25-launching-a-fund-and-raising-capital |
| emission allowance | 3 | 07-emissions-and-environmental-markets |
| empirical Bayes | 4 | 14-bayesian-methods |
| empirical distribution function | 4 | 13-resampling |
| employee referral | 18 | 03-applications |
| employer taxonomy | 17 | 01-a-map-of-the-industry |
| end-of-day batch | 15 | 01-the-platform-map |
| end-of-day compaction | 15 | 04-a-tick-store-on-open-formats |
| end-of-day flattening | 11 | 11-hedging-and-inventory-in-practice |
| end-of-day hedging flow | 8 | 13-intraday-patterns |
| end-of-day mark | 15 | 17-position-and-pnl-services |
| end-to-end test | 15 | 27-testing-and-continuous-delivery |
| Engle--Granger test | 4 | 20-multivariate-series-and-cointegration |
| English auction | 4 | 29-games-auctions-and-information |
| enterprise licence | 16 | 22-data-strategy-and-costs |
| entitlement | 15 | 23-market-data-distribution-and-entitlements |
| entitlement system | 15 | 23-market-data-distribution-and-entitlements |
| entity embedding | 12 | 09-cross-sectional-deep-models |
| entity linking | 12 | 13-text-from-bag-of-words-to-embeddings |
| entity resolution | 12 | 15-alternative-data-pipelines |
| entropic risk measure | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| entropy | 4 | 29-games-auctions-and-information |
| entry plan | 16 | 24-entering-a-new-market |
| environment adapter | 15 | 12-simulation-production-parity |
| environment lock | 7 | 29-build-a-research-workflow |
| epistemic uncertainty | 12 | 11-probabilistic-models-and-uncertainty |
| epoch | 12 | 07-neural-networks-for-noisy-tabular-data |
| epoch-based reclamation | 13 | 11-lock-free-programming |
| Epps effect | 4 | 21-high-frequency-econometrics |
| equal risk contribution portfolio | 7 | 26-portfolio-construction-ii |
| equal-weight blend | 7 | 14-signal-combination |
| equalisation | 16 | 04-the-asset-manager-and-the-fund |
| equity swap | 1 | 17-delta-one-instruments |
| equity tranche | 2 | 25-loans-clos-and-securitisation |
| equity-implied spread | 9 | 09-capital-structure-arbitrage |
| equity-to-credit model | 5 | 21-convertibles-and-the-credit-equity-link |
| equivalent martingale measure | 4 | 05-girsanov-and-changes-of-numeraire |
| equivalent measures | 4 | 01-probability-at-speed |
| error budget | 15 | 28-observability-and-incident-response |
| error maximisation | 7 | 25-portfolio-construction-i |
| error-correcting code memory | 14 | 08-servers |
| errors-in-variables | 4 | 16-linear-models-under-stress |
| escalation procedure | 16 | 12-the-risk-management-function |
| escrowed dividend model | 5 | 05-dividends-borrow-and-forwards |
| estimator | 4 | 11-estimation |
| ETF create-redeem arbitrage | 9 | 19-systematic-credit-and-bond-etf-arbitrage |
| ETF discount | 9 | 19-systematic-credit-and-bond-etf-arbitrage |
| Ethernet frame | 14 | 01-networking-for-trading |
| ETP rebalancing flow | 9 | 05-the-volatility-index-complex |
| Euler allocation | 6 | 20-the-valuation-adjustment-desk |
| Euler--Maruyama scheme | 4 | 04-stochastic-differential-equations |
| European exercise | 1 | 23-option-contracts-and-exchanges |
| event calendar | 7 | 11-fundamental-analyst-and-event-features |
| event contract | 3 | 27-prediction-and-betting-markets |
| event extraction | 12 | 13-text-from-bag-of-words-to-embeddings |
| event log | 3 | 26-crypto-data-and-infrastructure |
| event loop | 13 | 20-the-strategy-engine |
| event model | 15 | 11-backtest-engine-architecture |
| event of default | 16 | 18-legal-documentation |
| event protocol | 11 | 18-news-and-event-trading |
| event sourcing | 15 | 24-messaging-and-event-driven-architecture |
| event straddle | 9 | 04-gamma-scalping-and-event-volatility |
| event study | 8 | 07-earnings |
| event variance | 5 | 08-parametrising-the-surface |
| event window | 8 | 07-earnings |
| event-driven backtest | 7 | 17-event-driven-backtests |
| EWMA volatility | 4 | 18-volatility-models |
| ex-dividend date | 1 | 08-shares-corporate-actions-indices |
| exactly-once processing | 15 | 24-messaging-and-event-driven-architecture |
| exceedance correlation | 7 | 05-stylised-facts-of-returns |
| exchange | 1 | 04-exchanges-brokers-venues |
| exchange certification | 13 | 25-testing-and-deploying-low-latency-systems |
| exchange failover test | 14 | 28-disaster-recovery-and-regulatory-requirements |
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
| execution identifier | 15 | 17-position-and-pnl-services |
| execution lag | 7 | 16-vectorised-backtests |
| execution management system | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| execution report | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| execution risk | 10 | 14-the-almgren-chriss-framework |
| execution trader | 17 | 16-trader |
| exempt employee | 17 | 26-hours-rhythm-and-intensity |
| exempt reporting adviser | 17 | 04-quantitative-hedge-funds-and-systematic-managers |
| exercise boundary | 5 | 06-american-options-and-early-exercise |
| exit race | 16 | 29-case-studies-ii |
| exotic book exposure | 9 | 28-hedging-a-structured-products-book |
| expanded limit | 3 | 09-agriculturals-and-softs |
| expatriate tax regime | 17 | 15-pay-regulation-and-tax-by-location |
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
| exploding offer | 18 | 07-offers-compensation-and-non-competes |
| exploration--exploitation trade-off | 12 | 17-reinforcement-learning-foundations |
| exposure aggregation | 15 | 18-real-time-risk |
| exposure at default | 6 | 19-funding-margin-and-capital-adjustments |
| extreme-value theory | 4 | 15-robust-statistics-and-heavy-tails |
| extrinsic value | 6 | 16-commodity-and-energy-derivatives |
| factor exposure | 7 | 24-risk-models |
| factor model | 4 | 22-covariance-estimation-and-random-matrices |
| factor overlay | 16 | 03-the-multi-manager-platform |
| factor product | 8 | 29-the-asset-managers-strategies |
| factor return | 7 | 24-risk-models |
| factor timing | 8 | 06-value-quality-and-low-risk |
| factor-neutrality constraint | 7 | 25-portfolio-construction-i |
| fade margin | 14 | 14-long-haul-wireless |
| fail-closed design | 13 | 22-pre-trade-risk-and-kill-switches |
| failover | 13 | 24-resilience |
| fails charge | 2 | 05-repo-and-specials |
| fair price | 11 | 02-fair-value |
| fair pricing condition | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| fair value | 1 | 21-basis-roll-and-delivery |
| fair-price filter | 11 | 02-fair-value |
| fair-share scheduling | 15 | 13-distributed-compute-and-schedulers |
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
| feature flag | 15 | 16-signal-serving-and-parameter-management |
| feature freshness | 12 | 24-data-and-feature-stores |
| feature selection | 12 | 06-feature-engineering-selection-and-importance |
| feature store | 12 | 24-data-and-feature-stores |
| fee hurdle | 16 | 04-the-asset-manager-and-the-fund |
| fee neutrality | 10 | 07-fees-rebates-and-venue-economics |
| fee-adjusted price | 10 | 07-fees-rebates-and-venue-economics |
| feed handler | 13 | 18-the-feed-handler |
| feed partition | 14 | 22-equities-and-options-connectivity |
| feedback control | 4 | 09-stochastic-control |
| feedback speed | 17 | 17-quant-researcher |
| Feller condition | 4 | 04-stochastic-differential-equations |
| Fermi estimate | 18 | 09-estimation |
| FICC | 17 | 07-bank-markets-divisions |
| fictitious trade | 6 | 28-operational-risk-and-rogue-trading |
| fidelity level | 7 | 16-vectorised-backtests |
| field-programmable gate array | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| filing lag | 7 | 11-fundamental-analyst-and-event-features |
| fill intensity | 11 | 03-inventory-models |
| fill model | 7 | 17-event-driven-backtests |
| fill rate | 7 | 23-measuring-market-making-and-execution |
| fill-or-kill order | 10 | 02-order-types-and-their-uses |
| filtered historical simulation | 6 | 21-market-risk-measures |
| filtration | 4 | 01-probability-at-speed |
| final round | 18 | 06-the-final-round-and-trading-games |
| finality | 3 | 14-blockchains-for-traders |
| financial extranet | 14 | 15-buying-connectivity |
| financial market infrastructure | 17 | 09-exchanges-brokers-vendors-and-regulators-as-employers |
| financial transmission right | 3 | 06-power-markets-trading |
| financing trade | 9 | 26-delta-one-and-dividends |
| fine-tuning | 12 | 10-representation-learning |
| finite-difference method | 4 | 27-finite-difference-methods |
| fire sale | 3 | 28-when-markets-break-together |
| firm liquidity | 10 | 21-execution-beyond-equities |
| firm profile | 17 | 02-proprietary-market-makers-and-high-frequency-firms |
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
| fixed cost base | 16 | 01-the-economics-of-a-trading-firm |
| fixed effects | 4 | 16-linear-models-under-stress |
| fixed leg | 2 | 09-interest-rate-swaps |
| fixed overheads requirement | 16 | 02-the-proprietary-market-making-firm |
| fixed-capacity container | 13 | 06-cpp-for-latency-i-memory |
| fixed-horizon label | 12 | 02-targets-labels-and-sample-weights |
| fixing order | 2 | 17-fixings-and-flows |
| fixing source | 2 | 18-emerging-market-fx-and-ndfs |
| fixing window | 2 | 17-fixings-and-flows |
| flash crash | 1 | 31-stress-case-studies |
| flash loan | 3 | 23-defi-credit-and-leverage |
| flash P\&L | 16 | 15-finance-product-control-and-tax |
| flash rally | 2 | 04-the-treasury-market |
| flash-to-final walk | 16 | 15-finance-product-control-and-tax |
| flat file format | 15 | 04-a-tick-store-on-open-formats |
| flat pricing | 10 | 07-fees-rebates-and-venue-economics |
| flat volatility | 6 | 04-vanilla-rates-options |
| flat-forward interpolation | 6 | 01-curve-construction |
| flattener | 2 | 31-reading-a-macro-calendar-and-a-rates-screen |
| flawed-asset clause | 16 | 18-legal-documentation |
| fleeting order | 10 | 03-empirical-facts-of-order-books |
| flight to quality | 3 | 28-when-markets-break-together |
| float adjustment | 1 | 15-index-construction-and-rebalancing |
| floating leg | 2 | 09-interest-rate-swaps |
| floating storage | 3 | 10-forward-curves-storage-and-convenience-yield |
| floating-point number | 4 | 25-floating-point-and-numerical-linear-algebra |
| floor | 2 | 13-the-rates-options-market |
| floor system | 2 | 01-central-banks-and-the-short-rate |
| floor trader | 17 | 02-proprietary-market-makers-and-high-frequency-firms |
| flow segmentation | 11 | 23-retail-wholesaling |
| flow steering | 14 | 03-network-cards-and-kernel-bypass |
| flow toxicity | 7 | 09-trade-flow-features |
| flow trading | 1 | 02-the-sell-side |
| flow-induced trading | 8 | 09-flows |
| flyweight codec | 13 | 16-protocols-ii-binary-exchange-protocols |
| FOCUS report | 17 | 11-reading-a-trading-firms-accounts |
| Fokker--Planck equation | 4 | 04-stochastic-differential-equations |
| follow-the-sun trading | 3 | 29-a-map-of-all-markets |
| forecast aggregation | 16 | 26-culture-and-decision-making |
| forecast calibration | 7 | 15-from-signal-to-forecast |
| forecast combination puzzle | 7 | 14-signal-combination |
| forecast dispersion | 7 | 11-fundamental-analyst-and-event-features |
| forecast horizon | 7 | 06-anatomy-of-a-predictor |
| forecast skew | 11 | 07-short-horizon-alpha |
| forecast-error variance decomposition | 4 | 20-multivariate-series-and-cointegration |
| foreign function interface | 15 | 09-native-extensions |
| foreign key | 15 | 25-databases-and-sql |
| foreign ownership limit | 1 | 12-asian-and-emerging-equity-markets |
| forfeiture | 17 | 13-how-pay-works |
| forgetting factor | 12 | 12-online-learning-and-drift |
| formation period | 8 | 04-pairs-and-baskets |
| Formosa bond | 6 | 09-bermudans-and-callables |
| formulaic payout | 16 | 10-hiring-and-compensation |
| forward Brent | 3 | 02-crude-oil |
| forward curve | 3 | 10-forward-curves-storage-and-convenience-yield |
| forward delta | 2 | 19-the-fx-options-market |
| forward error correction | 14 | 13-long-haul-fibre |
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
| founders' share class | 16 | 25-launching-a-fund-and-raising-capital |
| four-eyes principle | 16 | 12-the-risk-management-function |
| FPGA engineer | 17 | 20-software-engineer |
| fractional Brownian motion | 4 | 17-linear-time-series |
| fractional differencing | 4 | 17-linear-time-series |
| fractional frequency offset | 14 | 04-time-synchronisation |
| fractional Kelly | 2 | 29-thinking-in-expected-value |
| franchise | 1 | 02-the-sell-side |
| franchise P\&L | 9 | 24-flow-market-making-at-a-bank |
| free allocation | 3 | 07-emissions-and-environmental-markets |
| free float | 1 | 08-shares-corporate-actions-indices |
| free list | 13 | 06-cpp-for-latency-i-memory |
| free on board | 3 | 01-physical-commodity-markets |
| free option of a limit order | 10 | 02-order-types-and-their-uses |
| free-boundary problem | 4 | 10-optimal-stopping-and-impulse-control |
| free-entry equilibrium | 16 | 30-competition-and-the-future |
| free-space optical link | 14 | 14-long-haul-wireless |
| frequent batch auction | 10 | 10-auction-mechanics-and-theory |
| Fresnel zone | 14 | 14-long-haul-wireless |
| front month | 1 | 18-futures-contracts-and-exchanges |
| front office | 16 | 13-operations |
| front-running | 3 | 22-maximal-extractable-value |
| front-to-back flow | 15 | 01-the-platform-map |
| full carry | 3 | 10-forward-curves-storage-and-convenience-yield |
| full node | 3 | 26-crypto-data-and-infrastructure |
| full replication | 8 | 29-the-asset-managers-strategies |
| full revaluation | 6 | 29-build-a-risk-engine |
| function multiversioning | 13 | 08-cpp-for-latency-iii-the-compiler |
| fund administrator | 16 | 04-the-asset-manager-and-the-fund |
| fundamental factor model | 7 | 24-risk-models |
| fundamental law of active management | 7 | 15-from-signal-to-forecast |
| Fundamental Review of the Trading Book | 6 | 23-regulatory-capital-for-trading-books |
| fundamental theorem of asset pricing | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| fundamentalist agent | 10 | 27-build-an-agent-based-market |
| funded-trader programme | 17 | 06-medium-frequency-proprietary-shops |
| funding arbitrage | 3 | 17-perpetual-futures |
| funding benefit adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| funding carry | 8 | 27-crypto-medium-frequency-strategies |
| funding cost adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| funding interval | 3 | 17-perpetual-futures |
| funding liquidity risk | 16 | 28-case-studies-i |
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
| G-SIB surcharge | 16 | 05-the-bank-markets-division |
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
| garden leave | 16 | 11-intellectual-property-and-non-competes |
| garden of forking paths | 4 | 12-testing-and-multiple-testing |
| Garman--Klass estimator | 7 | 07-price-and-volume-features |
| Garman--Kohlhagen model | 5 | 20-fx-derivatives |
| gas | 3 | 14-blockchains-for-traders |
| gas day | 3 | 04-natural-gas-and-lng |
| gate closure | 3 | 06-power-markets-trading |
| gateway fairness | 14 | 23-futures-connectivity |
| Gauss--Newton method | 4 | 24-numerical-optimisation-in-practice |
| Gaussian copula | 6 | 15-portfolio-credit |
| Gaussian process | 4 | 02-brownian-motion |
| general collateral | 1 | 16-stock-loan-and-short-selling |
| general partner | 16 | 04-the-asset-manager-and-the-fund |
| generalisation error | 12 | 01-why-financial-machine-learning-is-different |
| generalised extreme value distribution | 4 | 15-robust-statistics-and-heavy-tails |
| generalised forward market model | 6 | 10-modelling-overnight-rate-products |
| generalised least squares | 4 | 16-linear-models-under-stress |
| generalised method of moments | 4 | 11-estimation |
| generalised Pareto distribution | 4 | 15-robust-statistics-and-heavy-tails |
| generative adversarial network | 12 | 16-generative-models-and-synthetic-data |
| generative model | 12 | 16-generative-models-and-synthetic-data |
| generator matrix | 4 | 08-markov-chains-and-queues |
| geodesic distance | 14 | 10-the-north-american-map |
| geometric Brownian motion | 4 | 04-stochastic-differential-equations |
| Gibbs sampler | 4 | 14-bayesian-methods |
| gilt | 2 | 07-european-and-japanese-government-bonds |
| give-up | 1 | 30-getting-access-futures-options |
| give-up (equities) | 1 | 29-getting-access-equities |
| give-up line | 2 | 27-getting-access-fx |
| GJR-GARCH model | 4 | 18-volatility-models |
| global allocator | 13 | 09-rust-for-low-latency |
| global interpreter lock | 15 | 08-python-at-scale |
| Global Master Repurchase Agreement | 2 | 28-getting-access-rates-credit |
| global surrogate | 12 | 21-interpretability-and-model-governance |
| Glosten--Milgrom model | 10 | 04-why-there-is-a-spread |
| GNSS time reference | 14 | 04-time-synchronisation |
| golden copy | 15 | 06-reference-data-and-symbology-services |
| golden source | 15 | 01-the-platform-map |
| golden-file test | 15 | 27-testing-and-continuous-delivery |
| good-leaver provision | 17 | 13-how-pay-works |
| good-till-cancelled order | 10 | 02-order-types-and-their-uses |
| gossip protocol | 14 | 21-on-chain-connectivity |
| gradient accumulation | 12 | 23-training-infrastructure |
| gradient boosting | 12 | 05-trees-and-boosting |
| gradient descent | 4 | 24-numerical-optimisation-in-practice |
| graduate programme | 17 | 28-career-paths-and-moves |
| grandmaster clock | 14 | 04-time-synchronisation |
| Granger causality | 4 | 20-multivariate-series-and-cointegration |
| grantor trust | 3 | 19-dated-futures-options-and-etfs |
| Greeks | 5 | 04-greeks-and-the-hedging-pnl |
| gross basis | 2 | 06-bond-futures |
| gross exposure | 1 | 07-pnl-and-positions |
| gross refining margin | 3 | 03-refined-products-and-cracks |
| group exercise | 18 | 06-the-final-round-and-trading-games |
| group index | 14 | 10-the-north-american-map |
| growth rate | 2 | 29-thinking-in-expected-value |
| guarantee of origin | 3 | 07-emissions-and-environmental-markets |
| guaranteed bonus | 17 | 13-how-pay-works |
| HAC estimator | 4 | 11-estimation |
| Hagan formula | 5 | 11-sabr-and-smile-dynamics |
| haircut | 1 | 06-financing |
| half-life | 4 | 04-stochastic-differential-equations |
| hallucination | 12 | 14-large-language-models-in-finance |
| Hamilton--Jacobi--Bellman equation | 4 | 09-stochastic-control |
| handoff specification | 12 | 28-the-machine-learning-team |
| HAR model | 4 | 18-volatility-models |
| hard limit | 16 | 07-limits-and-capital-allocation |
| hard-to-borrow list | 8 | 01-anatomy-of-a-stat-arb-book |
| hardware description language | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| hardware performance counter | 13 | 05-measuring-latency |
| hardware prefetching | 13 | 03-memory-hierarchy-and-caches |
| hardware security module | 15 | 29-security |
| hardware timestamp | 13 | 05-measuring-latency |
| hardware trigger | 14 | 07-programmable-hardware-ii-trading-designs |
| hat matrix | 4 | 16-linear-models-under-stress |
| Hawkes process | 4 | 07-point-processes-and-hawkes-processes |
| Hayashi--Yoshida estimator | 4 | 21-high-frequency-econometrics |
| hazard pointer | 13 | 11-lock-free-programming |
| hazard rate | 2 | 23-credit-default-swaps |
| head of desk | 17 | 25-leadership-roles |
| head-of-line blocking | 14 | 01-networking-for-trading |
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
| Herfindahl--Hirschman index | 16 | 30-competition-and-the-future |
| Herstatt risk | 2 | 20-settlement-risk |
| Heston model | 5 | 10-stochastic-volatility |
| heterogeneous cores | 13 | 02-cpu-microarchitecture |
| hidden Markov model | 12 | 20-clustering-regimes-and-anomaly-detection |
| hidden order | 10 | 02-order-types-and-their-uses |
| hidden state | 15 | 15-the-research-environment |
| hierarchical clustering | 12 | 20-clustering-regimes-and-anomaly-detection |
| hierarchical model | 4 | 14-bayesian-methods |
| hierarchical risk parity | 7 | 26-portfolio-construction-ii |
| high earner | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| high yield | 2 | 21-corporate-bonds |
| high-frequency trading | 10 | 24-market-quality-and-regulation |
| high-level synthesis | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| high-quality liquid assets | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| high-touch trading | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| high-water mark | 1 | 03-the-buy-side |
| Hill estimator | 4 | 15-robust-statistics-and-heavy-tails |
| hiring committee | 18 | 02-the-process-by-firm-type |
| historical scenario | 6 | 22-stress-testing-and-scenarios |
| historical simulation | 6 | 21-market-risk-measures |
| historical store | 15 | 04-a-tick-store-on-open-formats |
| hit rate | 7 | 22-performance-measurement |
| hit ratio | 7 | 23-measuring-market-making-and-execution |
| hitting probability | 4 | 08-markov-chains-and-queues |
| hitting time | 4 | 02-brownian-motion |
| HJM drift condition | 6 | 08-forward-rate-and-market-models |
| hold time | 2 | 15-fx-spot-microstructure |
| holding-company discount | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| holdout creditor | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| holdout set | 7 | 01-the-research-process |
| holdover | 14 | 04-time-synchronisation |
| hollow-core fibre | 14 | 13-long-haul-fibre |
| Holm procedure | 4 | 12-testing-and-multiple-testing |
| host--device transfer | 15 | 14-accelerators-for-quantitative-work |
| hosted node provider | 14 | 21-on-chain-connectivity |
| hot path | 13 | 01-where-latency-comes-from |
| hot wallet | 3 | 24-the-crypto-trading-business |
| hot-potato trading | 10 | 24-market-quality-and-regulation |
| house margin | 16 | 14-treasury-and-funding |
| housekeeping core | 13 | 13-linux-tuning |
| housing turnover | 6 | 12-mortgage-modelling |
| Huang--Stoll model | 10 | 05-decomposing-the-spread |
| Huber loss | 4 | 15-robust-statistics-and-heavy-tails |
| huge page | 13 | 03-memory-hierarchy-and-caches |
| Hull--White model | 6 | 07-short-rate-models |
| hurdle rate | 6 | 19-funding-margin-and-capital-adjustments |
| Hurst exponent | 4 | 17-linear-time-series |
| hybrid factor model | 7 | 24-risk-models |
| hybrid trading system | 14 | 07-programmable-hardware-ii-trading-designs |
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
| idempotency key | 14 | 19-cross-region-crypto-networks |
| idempotent processing | 13 | 24-resilience |
| identifiability | 4 | 24-numerical-optimisation-in-practice |
| identifier mapping | 7 | 04-universe-symbology-and-corporate-actions |
| idle state | 13 | 02-cpu-microarchitecture |
| IGMP snooping | 14 | 01-networking-for-trading |
| imbalance bar | 7 | 02-market-data-for-research |
| imbalance price | 3 | 06-power-markets-trading |
| imbalance volume | 3 | 06-power-markets-trading |
| imbalance-offsetting order | 11 | 16-auctions-and-the-close |
| IMM date | 2 | 08-short-term-interest-rate-futures |
| immediate-or-cancel order | 10 | 02-order-types-and-their-uses |
| impact curve | 10 | 11-the-empirics-of-price-impact |
| impact prefactor | 10 | 11-the-empirics-of-price-impact |
| impact reversion | 10 | 11-the-empirics-of-price-impact |
| impact tolerance | 14 | 28-disaster-recovery-and-regulatory-requirements |
| impermanent loss | 3 | 20-automated-market-makers |
| implementation shortfall | 7 | 19-simulation-versus-live |
| implementation-shortfall algorithm | 10 | 16-benchmark-algorithms |
| implicit continuous allocation | 14 | 26-power-commodities-and-betting-connectivity |
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
| important business service | 14 | 28-disaster-recovery-and-regulatory-requirements |
| impulse control | 4 | 10-optimal-stopping-and-impulse-control |
| impulse response function | 4 | 20-multivariate-series-and-cointegration |
| in the money | 1 | 23-option-contracts-and-exchanges |
| in-block priority rule | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| in-flight order | 13 | 21-order-gateway-and-order-management |
| in-kind transfer | 1 | 14-exchange-traded-funds |
| in-play betting | 3 | 27-prediction-and-betting-markets |
| in-sample | 7 | 20-overfitting |
| incast | 14 | 01-networking-for-trading |
| incentive programme | 1 | 30-getting-access-futures-options |
| incident commander | 15 | 28-observability-and-incident-response |
| Incoterms | 3 | 01-physical-commodity-markets |
| incremental aggregation | 15 | 18-real-time-risk |
| incremental channel | 13 | 16-protocols-ii-binary-exchange-protocols |
| incremental information coefficient | 7 | 12-alternative-and-text-data |
| incremental revaluation | 15 | 20-the-risk-grid |
| incremental XVA | 6 | 20-the-valuation-adjustment-desk |
| indefeasible right of use | 14 | 13-long-haul-fibre |
| independent amount | 6 | 17-counterparty-exposure |
| independent price verification | 6 | 27-pnl-explain-and-independent-price-verification |
| independent software vendor | 14 | 27-the-vendor-map |
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
| indicator decomposition | 18 | 11-probability-ii |
| indifference price | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| individual conditional expectation | 12 | 21-interpretability-and-model-governance |
| industry classification code | 17 | 01-a-map-of-the-industry |
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
| information barrier | 16 | 16-compliance-and-market-abuse |
| information chasing | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| information coefficient | 7 | 06-anatomy-of-a-predictor |
| information criterion | 4 | 17-linear-time-series |
| information leakage | 10 | 09-dark-pools-and-blocks |
| information ratio | 1 | 03-the-buy-side |
| information share | 10 | 08-fragmentation-and-routing |
| informed options trading | 8 | 15-options-implied-signals-for-stocks |
| informed trader | 10 | 04-why-there-is-a-spread |
| infrastructure as code | 15 | 26-cloud-against-on-premises |
| ingestion pipeline | 12 | 15-alternative-data-pipelines |
| inhomogeneous Poisson process | 4 | 07-point-processes-and-hawkes-processes |
| initial margin | 1 | 05-clearing-and-settlement |
| initial-margin model | 6 | 25-margin-models |
| initial-margin threshold | 6 | 25-margin-models |
| injected clock | 13 | 20-the-strategy-engine |
| injection season | 3 | 04-natural-gas-and-lng |
| inline XBRL | 17 | 11-reading-a-trading-firms-accounts |
| inlining | 13 | 07-cpp-for-latency-ii-compile-time |
| innovation | 4 | 19-state-space-models-and-the-kalman-filter |
| input journal | 13 | 23-logging-capture-and-replay |
| inside information | 16 | 16-compliance-and-market-abuse |
| insider dealing | 16 | 16-compliance-and-market-abuse |
| insider list | 16 | 16-compliance-and-market-abuse |
| insider threat | 15 | 29-security |
| instance lottery | 14 | 17-where-the-crypto-venues-live |
| instantaneous forward rate | 6 | 01-curve-construction |
| institutional salesperson | 17 | 23-structurer-sales-and-sales-trader |
| instruction pipeline | 13 | 02-cpu-microarchitecture |
| instructions per cycle | 13 | 02-cpu-microarchitecture |
| instrument lifecycle event | 15 | 06-reference-data-and-symbology-services |
| instrumentation point | 13 | 26-build-tick-to-trade-measured |
| instrumented principal component analysis | 12 | 09-cross-sectional-deep-models |
| insurance fund | 3 | 18-margin-liquidation-and-loss-allocation |
| integrated variance | 4 | 18-volatility-models |
| integration test | 15 | 27-testing-and-continuous-delivery |
| integrity scenario | 18 | 28-behavioural-and-fit |
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
| internal management | 17 | 08-asset-managers-pensions-sovereign-funds-and-insurers |
| internal models approach | 6 | 23-regulatory-capital-for-trading-books |
| internalisation | 1 | 10-retail-flow-and-wholesaling |
| internalisation rate | 11 | 23-retail-wholesaling |
| Internet Group Management Protocol | 14 | 01-networking-for-trading |
| internship | 17 | 28-career-paths-and-moves |
| interpolation locality | 6 | 01-curve-construction |
| interpretability | 12 | 21-interpretability-and-model-governance |
| interpreter overhead | 15 | 08-python-at-scale |
| interrupt affinity | 13 | 13-linux-tuning |
| interrupt coalescing | 14 | 03-network-cards-and-kernel-bypass |
| interview loop | 18 | 01-what-each-interview-tests-by-role |
| interview rubric | 18 | 01-what-each-interview-tests-by-role |
| intraday alpha | 8 | 14-intraday-machine-learned-alphas |
| intraday margin call | 1 | 20-margin |
| intraday market | 3 | 06-power-markets-trading |
| intraday mean reversion | 8 | 25-short-term-futures-strategies |
| intraday P\&L | 15 | 17-position-and-pnl-services |
| intraday return | 8 | 13-intraday-patterns |
| intraday seasonality | 7 | 05-stylised-facts-of-returns |
| intraday store | 15 | 04-a-tick-store-on-open-formats |
| intraday volume forecast | 10 | 16-benchmark-algorithms |
| intraday volume profile | 7 | 05-stylised-facts-of-returns |
| intrinsic spread | 2 | 24-credit-indices-and-tranches |
| intrinsic storage value | 6 | 16-commodity-and-energy-derivatives |
| intrinsic value | 1 | 23-option-contracts-and-exchanges |
| introducing broker | 16 | 17-regulators-and-licences |
| invariant method | 18 | 12-brainteasers-and-logic |
| invariant time-stamp counter | 13 | 05-measuring-latency |
| invention assignment clause | 16 | 11-intellectual-property-and-non-competes |
| inventory | 2 | 30-market-making-games |
| inventory bound | 11 | 04-extensions-of-the-inventory-framework |
| inventory P\&L | 7 | 23-measuring-market-making-and-execution |
| inventory penalty | 11 | 03-inventory-models |
| inventory-holding cost | 10 | 04-why-there-is-a-spread |
| inverse contract | 3 | 17-perpetual-futures |
| inverse option | 3 | 19-dated-futures-options-and-etfs |
| inverse transform sampling | 4 | 26-monte-carlo |
| inverted venue | 1 | 09-us-equity-market-structure |
| investment firm | 16 | 17-regulators-and-licences |
| investment grade | 2 | 21-corporate-bonds |
| invoice price | 2 | 06-bond-futures |
| ISDA master agreement | 2 | 28-getting-access-rates-credit |
| ISDA standard model | 6 | 13-reduced-form-credit |
| isolated margin | 3 | 18-margin-liquidation-and-loss-allocation |
| isolation forest | 12 | 20-clustering-regimes-and-anomaly-detection |
| isolation level | 15 | 25-databases-and-sql |
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
| job scheduler | 15 | 13-distributed-compute-and-schedulers |
| Johansen test | 4 | 20-multivariate-series-and-cointegration |
| jump chain | 4 | 08-markov-chains-and-queues |
| jump condition | 5 | 22-trees-and-finite-difference-pricers-in-practice |
| jump-diffusion | 4 | 06-jump-processes |
| jump-to-default risk | 6 | 13-reduced-form-credit |
| just-in-time compilation | 13 | 10-managed-and-functional-languages-on-the-desk |
| just-in-time liquidity | 3 | 20-automated-market-makers |
| K-factor requirement | 16 | 02-the-proprietary-market-making-firm |
| k-means | 12 | 20-clustering-regimes-and-anomaly-detection |
| Kalman filter | 4 | 19-state-space-models-and-the-kalman-filter |
| Kalman gain | 4 | 19-state-space-models-and-the-kalman-filter |
| Kalman smoother | 4 | 19-state-space-models-and-the-kalman-filter |
| Karush--Kuhn--Tucker conditions | 4 | 23-convex-optimisation |
| Kelly criterion | 2 | 29-thinking-in-expected-value |
| Kendall's tau | 4 | 15-robust-statistics-and-heavy-tails |
| kernel bypass | 13 | 13-linux-tuning |
| key risk indicator | 16 | 13-operations |
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
| labor condition application | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| Lagrangian | 4 | 23-convex-optimisation |
| language binding | 15 | 09-native-extensions |
| language model | 12 | 14-large-language-models-in-finance |
| language-model agent | 12 | 14-large-language-models-in-finance |
| large homogeneous pool | 6 | 15-portfolio-credit |
| large language model | 12 | 14-large-language-models-in-finance |
| large-in-scale waiver | 1 | 11-european-equity-market-structure |
| large-tick asset | 10 | 06-tick-size-queues-and-priority |
| lasso | 4 | 16-linear-models-under-stress |
| last look | 2 | 15-fx-spot-microstructure |
| last trading day | 3 | 02-crude-oil |
| late materialisation | 15 | 05-time-series-databases-and-the-alternatives |
| latency | 13 | 01-where-latency-comes-from |
| latency arbitrage | 11 | 09-latency-arbitrage-and-its-defence |
| latency arms race | 16 | 19-technology-strategy |
| latency attribution | 13 | 26-build-tick-to-trade-measured |
| latency budget | 13 | 01-where-latency-comes-from |
| latency corridor | 14 | 11-the-european-map |
| latency equalisation | 14 | 09-colocation-products-and-how-they-are-sold |
| latency floor | 14 | 10-the-north-american-map |
| latency histogram | 13 | 05-measuring-latency |
| latency model | 7 | 18-order-book-replay-simulation |
| latency race | 11 | 09-latency-arbitrage-and-its-defence |
| latency tier | 16 | 19-technology-strategy |
| latent Dirichlet allocation | 12 | 13-text-from-bag-of-words-to-embeddings |
| latent liquidity | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| latent order book | 10 | 13-metaorders-latent-liquidity-and-cross-impact |
| lateral hire | 17 | 28-career-paths-and-moves |
| law of one price | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| lay bet | 3 | 27-prediction-and-betting-markets |
| layer normalisation | 12 | 07-neural-networks-for-noisy-tabular-data |
| layer-1 fan-out | 14 | 02-switches-and-layer-1-devices |
| layer-1 multiplexer | 14 | 02-switches-and-layer-1-devices |
| layer-1 switch | 14 | 02-switches-and-layer-1-devices |
| layering | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| lazy evaluation | 15 | 10-dataframes |
| lazy recalculation | 15 | 19-pricing-library-architecture |
| LBMA Gold Price | 3 | 08-metals |
| lead market maker | 1 | 19-matching-algorithms-and-implied-spreads |
| lead--lag estimator | 7 | 10-cross-sectional-and-cross-asset-features |
| lead--lag relationship | 7 | 10-cross-sectional-and-cross-asset-features |
| leader schedule | 14 | 21-on-chain-connectivity |
| league table | 17 | 07-bank-markets-divisions |
| leakage audit | 12 | 03-validation |
| learning rate | 12 | 05-trees-and-boosting |
| least privilege | 15 | 29-security |
| leave-one-out contribution | 16 | 09-managing-researchers-traders-and-engineers |
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
| leverage exposure measure | 16 | 05-the-bank-markets-division |
| leverage function | 5 | 20-fx-derivatives |
| leverage ratio | 16 | 05-the-bank-markets-division |
| leverage rebalancing flow | 8 | 26-volatility-targeting-and-risk-managed-portfolios |
| leveraged ETF | 1 | 14-exchange-traded-funds |
| leveraged loan | 2 | 25-loans-clos-and-securitisation |
| Lewis formula | 5 | 24-fourier-pricing-and-calibration-engineering |
| liability-driven investment | 2 | 07-european-and-japanese-government-bonds |
| LIBOR market model | 6 | 08-forward-rate-and-market-models |
| library developer | 17 | 19-quant-developer |
| library quant | 17 | 18-bank-quant |
| likelihood function | 4 | 11-estimation |
| likelihood-ratio Greek | 5 | 23-monte-carlo-pricers-in-practice |
| likelihood-ratio test | 4 | 12-testing-and-multiple-testing |
| limit breach | 16 | 07-limits-and-capital-allocation |
| limit framework | 16 | 07-limits-and-capital-allocation |
| limit order | 10 | 01-the-limit-order-book |
| limit order book | 10 | 01-the-limit-order-book |
| limit up--limit down | 1 | 31-stress-case-studies |
| limit utilisation | 16 | 07-limits-and-capital-allocation |
| limit-hit continuation | 8 | 18-asia-specific-equity-strategies |
| limit-locked market | 3 | 09-agriculturals-and-softs |
| limit-on-close order | 1 | 13-auctions |
| limited liability partnership | 16 | 02-the-proprietary-market-making-firm |
| limited partner | 16 | 04-the-asset-manager-and-the-fund |
| limited price indexation | 6 | 11-inflation-derivatives |
| line arbitration | 13 | 16-protocols-ii-binary-exchange-protocols |
| line rate | 14 | 01-networking-for-trading |
| line search | 4 | 24-numerical-optimisation-in-practice |
| line-of-sight path | 14 | 14-long-haul-wireless |
| linear contract | 3 | 17-perpetual-futures |
| linear cost model | 7 | 16-vectorised-backtests |
| linear filter | 7 | 07-price-and-volume-features |
| linear probe | 12 | 10-representation-learning |
| linear programme | 4 | 23-convex-optimisation |
| linear shrinkage | 4 | 22-covariance-estimation-and-random-matrices |
| linear terminal swap-rate model | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| link availability | 14 | 14-long-haul-wireless |
| link budget | 14 | 14-long-haul-wireless |
| link-time optimisation | 13 | 08-cpp-for-latency-iii-the-compiler |
| liquefied natural gas | 3 | 04-natural-gas-and-lng |
| liquid staking token | 3 | 23-defi-credit-and-leverage |
| liquidation absorption | 11 | 24-crypto-high-frequency-trading-on-centralised-venues |
| liquidation bonus | 3 | 23-defi-credit-and-leverage |
| liquidation cascade | 3 | 18-margin-liquidation-and-loss-allocation |
| liquidation engine | 3 | 18-margin-liquidation-and-loss-allocation |
| liquidation price | 3 | 18-margin-liquidation-and-loss-allocation |
| liquidity aggregator | 10 | 21-execution-beyond-equities |
| liquidity buffer | 16 | 14-treasury-and-funding |
| liquidity constraint | 7 | 25-portfolio-construction-i |
| liquidity coverage ratio | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| liquidity drill | 16 | 27-crisis-management |
| liquidity filter | 7 | 04-universe-symbology-and-corporate-actions |
| liquidity horizon | 6 | 23-regulatory-capital-for-trading-books |
| liquidity mismatch | 16 | 04-the-asset-manager-and-the-fund |
| liquidity pool | 3 | 20-automated-market-makers |
| liquidity spiral | 1 | 31-stress-case-studies |
| liquidity tier | 2 | 15-fx-spot-microstructure |
| liquidity vault | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| liquidity-provider review | 2 | 27-getting-access-fx |
| lit service | 14 | 13-long-haul-fibre |
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
| lock-up period | 16 | 04-the-asset-manager-and-the-fund |
| locked market | 10 | 08-fragmentation-and-routing |
| loco London | 3 | 08-metals |
| log contract | 5 | 14-variance-swaps-and-volatility-derivatives |
| log-moneyness | 5 | 07-implied-volatility-and-its-surface |
| logic synthesis | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| logistic regression | 12 | 04-linear-and-regularised-baselines |
| lognormal volatility | 6 | 04-vanilla-rates-options |
| long format | 15 | 10-dataframes |
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
| low-latency engineer | 17 | 20-software-engineer |
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
| machine-learning design question | 18 | 19-machine-learning |
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
| makespan | 15 | 13-distributed-compute-and-schedulers |
| malus | 16 | 10-hiring-and-compensation |
| managed infrastructure | 14 | 15-buying-connectivity |
| managed money | 3 | 09-agriculturals-and-softs |
| management fee | 1 | 03-the-buy-side |
| mandate | 1 | 03-the-buy-side |
| Marchenko--Pastur law | 4 | 22-covariance-estimation-and-random-matrices |
| margin call | 1 | 06-financing |
| margin lock-up | 16 | 14-treasury-and-funding |
| margin optimisation | 16 | 14-treasury-and-funding |
| margin period of risk | 1 | 20-margin |
| margin spiral | 3 | 28-when-markets-break-together |
| margin valuation adjustment | 6 | 19-funding-margin-and-capital-adjustments |
| marginal fee | 11 | 17-rebates-inverted-venues-and-tiers |
| marginal tax rate | 17 | 15-pay-regulation-and-tax-by-location |
| marine fuel sulphur cap | 3 | 03-refined-products-and-cracks |
| mark price | 3 | 17-perpetual-futures |
| mark-out | 2 | 15-fx-spot-microstructure |
| mark-out curve | 7 | 23-measuring-market-making-and-execution |
| mark-to-market | 1 | 07-pnl-and-positions |
| market abuse | 16 | 16-compliance-and-market-abuse |
| market access rule | 11 | 27-risk-controls |
| market beta | 7 | 22-performance-measurement |
| market capitalisation | 1 | 08-shares-corporate-actions-indices |
| market concentration | 16 | 30-competition-and-the-future |
| market coupling | 3 | 05-power-markets-design |
| market data feed | 1 | 04-exchanges-brokers-venues |
| market fragmentation | 10 | 08-fragmentation-and-routing |
| market impact | 7 | 18-order-book-replay-simulation |
| market liquidity risk | 16 | 28-case-studies-i |
| market maker | 1 | 01-what-a-trading-firm-does |
| market object | 15 | 19-pricing-library-architecture |
| market order | 10 | 01-the-limit-order-book |
| market quality | 10 | 24-market-quality-and-regulation |
| market recap | 18 | 18-fixed-income-and-markets |
| market segment gateway | 14 | 23-futures-connectivity |
| market stability reserve | 3 | 07-emissions-and-environmental-markets |
| market time unit | 3 | 05-power-markets-design |
| market-based rate authorisation | 3 | 13-getting-access-commodities-and-power |
| market-by-order | 1 | 19-matching-algorithms-and-implied-spreads |
| market-by-price | 1 | 19-matching-algorithms-and-implied-spreads |
| market-data abstraction | 15 | 12-simulation-production-parity |
| market-data audit | 15 | 23-market-data-distribution-and-entitlements |
| market-data distribution platform | 15 | 23-market-data-distribution-and-entitlements |
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
| master--feeder structure | 16 | 04-the-asset-manager-and-the-fund |
| matching engine | 10 | 01-the-limit-order-book |
| matching tolerance | 15 | 22-post-trade-systems |
| material non-public information | 7 | 12-alternative-and-text-data |
| material risk taker | 16 | 10-hiring-and-compensation |
| materialisation | 12 | 24-data-and-feature-stores |
| maximal extractable value | 3 | 22-maximal-extractable-value |
| maximum drawdown | 7 | 22-performance-measurement |
| maximum likelihood estimator | 4 | 11-estimation |
| maximum transmission unit | 14 | 01-networking-for-trading |
| maximum-ICIR blend | 7 | 14-signal-combination |
| mean decrease in impurity | 12 | 06-feature-engineering-selection-and-importance |
| mean reversion | 4 | 04-stochastic-differential-equations |
| mean time between failures | 14 | 15-buying-connectivity |
| mean time to repair | 14 | 15-buying-connectivity |
| mean--variance optimisation | 7 | 25-portfolio-construction-i |
| mean-reversion speed filter | 8 | 03-residual-and-principal-component-stat-arb |
| measurement overhead | 13 | 05-measuring-latency |
| median absolute deviation | 4 | 15-robust-statistics-and-heavy-tails |
| median-employee pay | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| medium-frequency trading | 17 | 06-medium-frequency-proprietary-shops |
| meet-me room | 14 | 09-colocation-products-and-how-they-are-sold |
| member rate | 1 | 30-getting-access-futures-options |
| members' capital | 16 | 02-the-proprietary-market-making-firm |
| members' remuneration | 17 | 11-reading-a-trading-firms-accounts |
| membership prediction | 8 | 10-index-rebalancing |
| memorisation | 12 | 14-large-language-models-in-finance |
| memory coupon | 5 | 18-autocallables |
| memory locking | 13 | 13-linux-tuning |
| memory ordering | 13 | 11-lock-free-programming |
| memory-bound kernel | 15 | 14-accelerators-for-quantitative-work |
| memory-mapped dataset | 12 | 23-training-infrastructure |
| memory-mapped file | 15 | 04-a-tick-store-on-open-formats |
| mempool | 3 | 14-blockchains-for-traders |
| merger arbitrage | 8 | 11-merger-arbitrage |
| merit order | 3 | 05-power-markets-design |
| Merton fraction | 4 | 09-stochastic-control |
| Merton jump-diffusion model | 5 | 13-jumps-and-levy-models |
| Merton model | 6 | 14-structural-credit-models |
| message broker | 15 | 24-messaging-and-event-driven-architecture |
| message burst | 13 | 18-the-feed-handler |
| message gap | 13 | 16-protocols-ii-binary-exchange-protocols |
| message throttle | 11 | 10-the-quoting-engine |
| meta-labelling | 12 | 02-targets-labels-and-sample-weights |
| metaorder | 7 | 09-trade-flow-features |
| method of lines | 4 | 27-finite-difference-methods |
| method of moments | 4 | 11-estimation |
| method of simulated moments | 10 | 27-build-an-agent-based-market |
| metric | 15 | 28-observability-and-incident-response |
| metro circuit | 14 | 15-buying-connectivity |
| Metropolis--Hastings algorithm | 4 | 14-bayesian-methods |
| MEV relay | 3 | 22-maximal-extractable-value |
| micro contract | 1 | 22-index-and-single-stock-futures-worldwide |
| microbenchmark | 13 | 02-cpu-microarchitecture |
| microburst | 14 | 01-networking-for-trading |
| microprice | 7 | 08-order-book-features |
| microstructure noise | 4 | 21-high-frequency-econometrics |
| microwave link | 14 | 14-long-haul-wireless |
| mid price | 1 | 01-what-a-trading-firm-does |
| middle distillates | 3 | 03-refined-products-and-cracks |
| middle office | 16 | 13-operations |
| midpoint peg | 10 | 02-order-types-and-their-uses |
| midquote series | 7 | 02-market-data-for-research |
| millimetre-wave link | 14 | 14-long-haul-wireless |
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
| model validator | 17 | 18-bank-quant |
| modified duration | 2 | 03-government-bonds |
| momentum crash | 8 | 05-momentum |
| momentum ignition | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| momentum method | 4 | 24-numerical-optimisation-in-practice |
| money-market account | 4 | 05-girsanov-and-changes-of-numeraire |
| money-market fund | 2 | 02-money-markets |
| money-market yield | 2 | 02-money-markets |
| monorepo | 15 | 15-the-research-environment |
| monotone convex interpolation | 6 | 01-curve-construction |
| monotone cubic interpolation | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| monotonic constraint | 12 | 05-trees-and-boosting |
| monotonic deque | 18 | 21-algorithms-and-data-structures |
| Monte Carlo method | 4 | 26-monte-carlo |
| Monte Carlo value at risk | 6 | 21-market-risk-measures |
| month-end rebalancing | 2 | 17-fixings-and-flows |
| most-favoured-nation clause | 16 | 04-the-asset-manager-and-the-fund |
| moving-average crossover | 7 | 07-price-and-volume-features |
| moving-average process | 4 | 17-linear-time-series |
| moving-block bootstrap | 4 | 13-resampling |
| multi-armed bandit | 12 | 17-reinforcement-learning-foundations |
| multi-asset market making | 11 | 04-extensions-of-the-inventory-framework |
| multi-attribute value model | 17 | 30-choosing |
| multi-curve framework | 6 | 02-multi-curve-and-collateral-discounting |
| multi-factor authentication | 15 | 29-security |
| multi-manager platform | 1 | 01-what-a-trading-firm-does |
| multi-party computation | 3 | 24-the-crypto-trading-business |
| multi-period optimisation | 7 | 26-portfolio-construction-ii |
| multi-site matching | 14 | 24-fx-connectivity |
| multi-strategy book | 8 | 28-running-a-multi-strategy-book |
| multicast | 13 | 16-protocols-ii-binary-exchange-protocols |
| multicast group | 14 | 01-networking-for-trading |
| multicollinearity | 4 | 16-linear-models-under-stress |
| multilateral trading facility | 1 | 04-exchanges-brokers-venues |
| multilayer perceptron | 12 | 07-neural-networks-for-noisy-tabular-data |
| multilevel Monte Carlo | 4 | 26-monte-carlo |
| multiple testing | 4 | 12-testing-and-multiple-testing |
| multistart | 4 | 24-numerical-optimisation-in-practice |
| multivariate Hawkes process | 4 | 07-point-processes-and-hawkes-processes |
| mutual information | 4 | 29-games-auctions-and-information |
| n-gram | 12 | 13-text-from-bag-of-words-to-embeddings |
| Nagle's algorithm | 14 | 01-networking-for-trading |
| naked short sale | 1 | 16-stock-loan-and-short-selling |
| name limit | 7 | 25-portfolio-construction-i |
| named-entity recognition | 12 | 13-text-from-bag-of-words-to-embeddings |
| Nash equilibrium | 4 | 29-games-auctions-and-information |
| national best bid and offer | 1 | 09-us-equity-market-structure |
| native extension | 15 | 09-native-extensions |
| natural cubic spline | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| NAV trigger | 16 | 18-legal-documentation |
| nearest correlation matrix | 4 | 23-convex-optimisation |
| negative basis trade | 9 | 18-credit-relative-value |
| negative convexity | 2 | 12-mortgages-and-agencies |
| Nelson--Siegel curve | 6 | 01-curve-construction |
| nested cross-validation | 12 | 03-validation |
| Nesterov acceleration | 4 | 24-numerical-optimisation-in-practice |
| net asset value | 1 | 14-exchange-traded-funds |
| net basis | 2 | 06-bond-futures |
| net capital rule | 16 | 02-the-proprietary-market-making-firm |
| net capture | 1 | 01-what-a-trading-firm-does |
| net exposure | 1 | 07-pnl-and-positions |
| net interest income sensitivity | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| net open position limit | 2 | 27-getting-access-fx |
| net stable funding ratio | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| net trading revenue | 16 | 01-the-economics-of-a-trading-firm |
| netback | 3 | 01-physical-commodity-markets |
| netting risk | 16 | 03-the-multi-manager-platform |
| netting set | 6 | 17-counterparty-exposure |
| network interface card | 14 | 01-networking-for-trading |
| network load balancer | 14 | 18-private-connectivity-to-crypto-venues |
| network segmentation | 15 | 29-security |
| network tap | 14 | 02-switches-and-layer-1-devices |
| Network Time Protocol | 14 | 04-time-synchronisation |
| neural network | 12 | 07-neural-networks-for-noisy-tabular-data |
| neutralisation | 7 | 06-anatomy-of-a-predictor |
| new crop | 3 | 09-agriculturals-and-softs |
| new-issue concession | 2 | 21-corporate-bonds |
| new-product approval | 16 | 06-the-head-of-desks-job |
| news reaction window | 8 | 17-news-and-events |
| Newton's method | 4 | 24-numerical-optimisation-in-practice |
| no-dynamic-arbitrage condition | 10 | 12-transient-impact-and-propagator-models |
| no-touch option | 5 | 15-barriers-and-digitals |
| no-trade region | 4 | 10-optimal-stopping-and-impulse-control |
| noise trader | 10 | 04-why-there-is-a-spread |
| noisy neighbour | 14 | 16-trading-in-a-public-cloud |
| non-compete clause | 16 | 11-intellectual-property-and-non-competes |
| non-deliverable forward | 2 | 18-emerging-market-fx-and-ndfs |
| non-display fee | 1 | 29-getting-access-equities |
| non-execution risk | 10 | 17-child-order-placement |
| non-GAAP measure | 16 | 01-the-economics-of-a-trading-firm |
| non-maturity deposit | 6 | 24-liquidity-and-funding-risk-bank-treasury |
| non-modellable risk factor | 6 | 23-regulatory-capital-for-trading-books |
| non-solicitation clause | 16 | 11-intellectual-property-and-non-competes |
| non-synchronous trading | 4 | 21-high-frequency-econometrics |
| non-uniform grid | 4 | 27-finite-difference-methods |
| non-uniform memory access | 13 | 04-multi-socket-machines-and-interconnects |
| nonlinear least squares | 4 | 24-numerical-optimisation-in-practice |
| nonlinear shrinkage | 4 | 22-covariance-estimation-and-random-matrices |
| normal form | 15 | 25-databases-and-sql |
| normal SABR | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| normal volatility | 2 | 13-the-rates-options-market |
| normal-form game | 4 | 29-games-auctions-and-information |
| normalisation | 1 | 28-reading-market-data |
| northbound flow | 8 | 18-asia-specific-equity-strategies |
| notice period | 17 | 28-career-paths-and-moves |
| notional | 1 | 07-pnl-and-positions |
| notional turnover | 1 | 27-options-markets-europe-asia |
| novation | 1 | 05-clearing-and-settlement |
| Novikov's condition | 4 | 05-girsanov-and-changes-of-numeraire |
| nowcast | 8 | 16-alternative-data-strategies |
| null hypothesis | 4 | 12-testing-and-multiple-testing |
| NUMA node | 13 | 04-multi-socket-machines-and-interconnects |
| numeraire | 4 | 05-girsanov-and-changes-of-numeraire |
| numerical reasoning test | 18 | 04-online-assessments |
| Obizhaeva--Wang model | 10 | 12-transient-impact-and-propagator-models |
| object pool | 13 | 06-cpp-for-latency-i-memory |
| observability | 15 | 28-observability-and-incident-response |
| observer pattern | 15 | 19-pricing-library-architecture |
| odd lot | 1 | 09-us-equity-market-structure |
| odds | 2 | 29-thinking-in-expected-value |
| off-channel communication | 15 | 30-surveillance-and-compliance-technology |
| off-exchange settlement | 3 | 15-centralised-exchanges |
| off-heap memory | 13 | 10-managed-and-functional-languages-on-the-desk |
| off-policy evaluation | 12 | 17-reinforcement-learning-foundations |
| off-the-run | 2 | 04-the-treasury-market |
| offer letter | 18 | 07-offers-compensation-and-non-competes |
| official selling price | 3 | 02-crude-oil |
| offline store | 12 | 24-data-and-feature-stores |
| offshore market | 2 | 18-emerging-market-fx-and-ndfs |
| oil indexation | 3 | 04-natural-gas-and-lng |
| old crop | 3 | 09-agriculturals-and-softs |
| Omega ratio | 7 | 22-performance-measurement |
| on-call rotation | 15 | 28-observability-and-incident-response |
| on-chain order book | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| on-chain signal | 8 | 27-crypto-medium-frequency-strategies |
| on-demand capacity | 15 | 26-cloud-against-on-premises |
| on-the-run | 2 | 04-the-treasury-market |
| on-the-run premium | 9 | 13-supply-trades |
| one-touch option | 5 | 15-barriers-and-digitals |
| online analytical processing | 15 | 25-databases-and-sql |
| online assessment | 18 | 04-online-assessments |
| online learning | 12 | 12-online-learning-and-drift |
| online store | 12 | 24-data-and-feature-stores |
| online transaction processing | 15 | 25-databases-and-sql |
| onshore market | 2 | 18-emerging-market-fx-and-ndfs |
| open addressing | 13 | 19-the-order-book-builder |
| open interest | 1 | 18-futures-contracts-and-exchanges |
| open outcry | 17 | 02-proprietary-market-makers-and-high-frequency-firms |
| open-interest cap | 3 | 21-on-chain-order-books-and-perpetual-dexs |
| open-market operation | 2 | 01-central-banks-and-the-short-rate |
| opening range breakout | 8 | 25-short-term-futures-strategies |
| operating margin | 16 | 01-the-economics-of-a-trading-firm |
| operational due diligence | 16 | 25-launching-a-fund-and-raising-capital |
| operational loss event | 6 | 28-operational-risk-and-rogue-trading |
| operational resilience | 14 | 28-disaster-recovery-and-regulatory-requirements |
| operational risk | 6 | 28-operational-risk-and-rogue-trading |
| operator fusion | 12 | 26-low-latency-inference |
| opportunity cost | 7 | 23-measuring-market-making-and-execution |
| OPRA | 1 | 24-options-market-structure |
| optical amplifier | 14 | 13-long-haul-fibre |
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
| options market-making house | 17 | 03-the-options-market-making-houses |
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
| order template | 14 | 07-programmable-hardware-ii-trading-designs |
| order-book event | 10 | 01-the-limit-order-book |
| order-book replay | 7 | 18-order-book-replay-simulation |
| order-entry abstraction | 15 | 12-simulation-production-parity |
| order-entry latency | 7 | 18-order-book-replay-simulation |
| order-entry path | 14 | 20-api-engineering-for-crypto-venues |
| order-entry port | 14 | 22-equities-and-options-connectivity |
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
| out-of-band management network | 14 | 02-switches-and-layer-1-devices |
| out-of-core processing | 15 | 10-dataframes |
| out-of-order execution | 13 | 02-cpu-microarchitecture |
| out-of-sample | 7 | 20-overfitting |
| out-of-sample R-squared | 12 | 01-why-financial-machine-learning-is-different |
| outcome bias | 16 | 26-culture-and-decision-making |
| outcomes analysis | 6 | 26-model-risk-and-validation |
| output-prediction question | 18 | 22-cpp |
| outright forward | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| over-quoting | 11 | 15-futures-market-making |
| over-the-counter search model | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| overclocking | 14 | 08-servers |
| overcollateralisation test | 2 | 25-loans-clos-and-securitisation |
| overfitting | 12 | 01-why-financial-machine-learning-is-different |
| overnight benchmark rate | 2 | 01-central-banks-and-the-short-rate |
| overnight index swap | 2 | 09-interest-rate-swaps |
| overnight return | 8 | 13-intraday-patterns |
| overnight reversal | 8 | 02-short-term-reversal |
| overnight-rate future | 2 | 08-short-term-interest-rate-futures |
| overround | 3 | 27-prediction-and-betting-markets |
| oversubscription ratio | 14 | 01-networking-for-trading |
| own funds | 16 | 02-the-proprietary-market-making-firm |
| p-value | 4 | 12-testing-and-multiple-testing |
| P\&L attribution | 1 | 07-pnl-and-positions |
| P\&L attribution test | 6 | 23-regulatory-capital-for-trading-books |
| P\&L sign-off | 16 | 15-finance-product-control-and-tax |
| pack | 2 | 08-short-term-interest-rate-futures |
| packet capture | 14 | 05-capturing-and-monitoring-the-network |
| packet capture file | 14 | 05-capturing-and-monitoring-the-network |
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
| parameter store | 15 | 16-signal-serving-and-parameter-management |
| parameter sweep | 15 | 13-distributed-compute-and-schedulers |
| parametric portfolio policy | 12 | 22-from-prediction-to-portfolio |
| parametric value at risk | 6 | 21-market-risk-measures |
| parent order | 10 | 14-the-almgren-chriss-framework |
| pari passu clause | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| parity harness | 15 | 12-simulation-production-parity |
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
| partition key | 15 | 02-capturing-and-storing-tick-data |
| partitioned log | 15 | 24-messaging-and-event-driven-architecture |
| partitioning | 15 | 02-capturing-and-storing-tick-data |
| partnership share | 17 | 13-how-pay-works |
| pass-through | 2 | 12-mortgages-and-agencies |
| pass-through fee | 16 | 03-the-multi-manager-platform |
| passive fill probability | 7 | 18-order-book-replay-simulation |
| passive management | 1 | 03-the-buy-side |
| passporting | 16 | 17-regulators-and-licences |
| path asymmetry | 14 | 04-time-synchronisation |
| path inflation | 14 | 19-cross-region-crypto-networks |
| path-dependent volatility model | 5 | 12-rough-volatility-and-forward-variance-models |
| pathwise Greek | 5 | 23-monte-carlo-pricers-in-practice |
| pay band | 17 | 09-exchanges-brokers-vendors-and-regulators-as-employers |
| pay-as-bid auction | 4 | 29-games-auctions-and-information |
| payer swap | 2 | 09-interest-rate-swaps |
| payer swaption | 2 | 13-the-rates-options-market |
| payment for order flow | 1 | 10-retail-flow-and-wholesaling |
| payment netting | 2 | 20-settlement-risk |
| payment versus payment | 2 | 20-settlement-risk |
| payment waterfall | 2 | 25-loans-clos-and-securitisation |
| payoff script | 15 | 19-pricing-library-architecture |
| payoff scripting language | 15 | 19-pricing-library-architecture |
| payoff smoothing | 5 | 22-trees-and-finite-difference-pricers-in-practice |
| payout rate | 16 | 03-the-multi-manager-platform |
| PCI Express | 13 | 04-multi-socket-machines-and-interconnects |
| peak impact | 10 | 11-the-empirics-of-price-impact |
| peak resident memory | 15 | 08-python-at-scale |
| peaks over threshold | 4 | 15-robust-statistics-and-heavy-tails |
| peer group | 7 | 10-cross-sectional-and-cross-asset-features |
| peer-relative return | 7 | 10-cross-sectional-and-cross-asset-features |
| peer-universe comparison | 10 | 19-transaction-cost-analysis |
| pegged order | 10 | 02-order-types-and-their-uses |
| penetration fill | 7 | 17-event-driven-backtests |
| penny program | 1 | 24-options-market-structure |
| per-symbol resynchronisation | 14 | 20-api-engineering-for-crypto-venues |
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
| personal account dealing | 16 | 16-compliance-and-market-abuse |
| physical delivery | 1 | 21-basis-roll-and-delivery |
| physical market | 3 | 01-physical-commodity-markets |
| pillar | 6 | 01-curve-construction |
| Pillar 3 disclosure | 17 | 11-reading-a-trading-firms-accounts |
| pin risk | 1 | 23-option-contracts-and-exchanges |
| pinball loss | 12 | 11-probabilistic-models-and-uncertainty |
| pinging order | 10 | 09-dark-pools-and-blocks |
| pinning | 9 | 06-zero-day-options-and-dealer-gamma-flows |
| pip | 2 | 14-the-fx-market |
| pipeline stage | 7 | 29-build-a-research-workflow |
| place and route | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| placement group | 14 | 16-trading-in-a-public-cloud |
| placement report | 17 | 29-education-pipelines |
| platform team | 16 | 19-technology-strategy |
| pod | 8 | 28-running-a-multi-strategy-book |
| pod analyst | 17 | 22-portfolio-manager-and-pod-analyst |
| point of non-viability | 2 | 26-distressed-sovereign-and-bank-capital-credit |
| point of presence | 14 | 11-the-european-map |
| point process | 4 | 07-point-processes-and-hawkes-processes |
| point-in-time data | 7 | 03-point-in-time-data-and-the-biases |
| Poisson process | 4 | 06-jump-processes |
| policy | 12 | 17-reinforcement-learning-foundations |
| policy gradient | 12 | 17-reinforcement-learning-foundations |
| policy rate | 2 | 01-central-banks-and-the-short-rate |
| poll-mode driver | 14 | 03-network-cards-and-kernel-bypass |
| pooled panel model | 12 | 09-cross-sectional-deep-models |
| population stability index | 12 | 27-monitoring-and-retraining |
| port mirroring | 14 | 02-switches-and-layer-1-devices |
| portfolio manager | 17 | 22-portfolio-manager-and-pod-analyst |
| portfolio margining | 1 | 20-margin |
| portfolio trade | 2 | 22-how-bonds-trade |
| portfolio turnover | 7 | 16-vectorised-backtests |
| porting | 2 | 10-swap-clearing-and-the-ccp-basis |
| position | 1 | 07-pnl-and-positions |
| position limit | 1 | 27-options-markets-europe-asia |
| position service | 15 | 17-position-and-pnl-services |
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
| power density | 14 | 09-colocation-products-and-how-they-are-sold |
| power of a test | 4 | 12-testing-and-multiple-testing |
| power purchase agreement | 3 | 06-power-markets-trading |
| pre-announcement drift | 8 | 25-short-term-futures-strategies |
| pre-averaging estimator | 4 | 21-high-frequency-econometrics |
| pre-clearance | 16 | 16-compliance-and-market-abuse |
| pre-faulting | 13 | 06-cpp-for-latency-i-memory |
| pre-mortem | 16 | 26-culture-and-decision-making |
| pre-registration | 7 | 01-the-research-process |
| pre-release | 11 | 14-depositary-receipts-and-dual-listings |
| pre-trade cost estimate | 10 | 19-transaction-cost-analysis |
| pre-trade risk check | 11 | 27-risk-controls |
| pre-training | 12 | 10-representation-learning |
| Precision Time Protocol | 14 | 04-time-synchronisation |
| precision--recall curve | 12 | 20-clustering-regimes-and-anomaly-detection |
| preconditioner | 4 | 25-floating-point-and-numerical-linear-algebra |
| predicate pushdown | 15 | 03-columnar-formats |
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
| prevailing wage | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| price alignment interest | 6 | 02-multi-curve-and-collateral-discounting |
| price collar | 11 | 27-risk-controls |
| price differential | 3 | 01-physical-commodity-markets |
| price discovery | 10 | 08-fragmentation-and-routing |
| price improvement | 1 | 10-retail-flow-and-wholesaling |
| price level | 10 | 01-the-limit-order-book |
| price level index | 17 | 27-locations |
| price limit | 1 | 12-asian-and-emerging-equity-markets |
| price pressure | 8 | 09-flows |
| price-improvement auction | 1 | 24-options-market-structure |
| price-reporting agency | 3 | 01-physical-commodity-markets |
| price-time priority | 1 | 19-matching-algorithms-and-implied-spreads |
| pricing basket | 11 | 12-etf-market-making |
| pricing engine | 5 | 28-build-a-pricing-library |
| pricing period | 3 | 01-physical-commodity-markets |
| primary data centre | 14 | 28-disaster-recovery-and-regulatory-requirements |
| primary dealer | 2 | 04-the-treasury-market |
| primary key | 15 | 25-databases-and-sql |
| primary venue | 2 | 14-the-fx-market |
| primary--backup replication | 13 | 24-resilience |
| primary--secondary spread | 6 | 12-mortgage-modelling |
| prime broker | 1 | 06-financing |
| prime services | 1 | 02-the-sell-side |
| prime-brokerage agreement | 16 | 18-legal-documentation |
| prime-of-prime | 2 | 27-getting-access-fx |
| principal | 1 | 01-what-a-trading-firm-does |
| principal component analysis | 4 | 22-covariance-estimation-and-random-matrices |
| principal component regression | 12 | 04-linear-and-regularised-baselines |
| principal trading firm | 17 | 01-a-map-of-the-industry |
| principal-only strip | 6 | 12-mortgage-modelling |
| prior distribution | 4 | 14-bayesian-methods |
| priority fee | 3 | 14-blockchains-for-traders |
| priority gas auction | 3 | 22-maximal-extractable-value |
| priority inversion | 13 | 11-lock-free-programming |
| private endpoint | 14 | 18-private-connectivity-to-crypto-venues |
| private key | 3 | 14-blockchains-for-traders |
| private order flow | 3 | 22-maximal-extractable-value |
| private-value auction | 4 | 29-games-auctions-and-information |
| pro-forma index | 1 | 15-index-construction-and-rebalancing |
| pro-rata allocation | 1 | 19-matching-algorithms-and-implied-spreads |
| probability of backtest overfitting | 7 | 20-overfitting |
| probability of default | 6 | 13-reduced-form-credit |
| probability of informed trading | 10 | 04-why-there-is-a-spread |
| process-based parallelism | 15 | 08-python-at-scale |
| processing-spread trade | 9 | 21-commodity-spreads |
| procyclicality | 1 | 20-margin |
| product control | 6 | 27-pnl-explain-and-independent-price-verification |
| product controller | 17 | 24-risk-operations-product-control-and-compliance |
| product governance | 17 | 23-structurer-sales-and-sales-trader |
| product scope | 16 | 06-the-head-of-desks-job |
| product slate | 3 | 03-refined-products-and-cracks |
| product team | 16 | 19-technology-strategy |
| profile-guided optimisation | 13 | 08-cpp-for-latency-iii-the-compiler |
| profit factor | 7 | 22-performance-measurement |
| profit per head | 17 | 12-revenue-and-profit-across-the-industry |
| profit-maximising size | 7 | 28-capacity-decay-and-crowding |
| profitability factor | 8 | 06-value-quality-and-low-risk |
| project scorecard | 16 | 09-managing-researchers-traders-and-engineers |
| projection curve | 6 | 02-multi-curve-and-collateral-discounting |
| projection pushdown | 15 | 03-columnar-formats |
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
| protocol foundation | 17 | 10-crypto-native-firms |
| provenance record | 15 | 07-data-quality-and-lineage |
| proximal gradient method | 4 | 24-numerical-optimisation-in-practice |
| proximal operator | 4 | 24-numerical-optimisation-in-practice |
| proximity hosting | 14 | 09-colocation-products-and-how-they-are-sold |
| proxy credit spread | 6 | 20-the-valuation-adjustment-desk |
| prudent valuation | 6 | 27-pnl-explain-and-independent-price-verification |
| PSA benchmark | 2 | 12-mortgages-and-agencies |
| pseudo-random number generator | 4 | 26-monte-carlo |
| public cloud | 14 | 16-trading-in-a-public-cloud |
| publish--subscribe | 15 | 24-messaging-and-event-driven-architecture |
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
| quant developer | 16 | 21-engineering-organisation-design |
| quantile regression | 12 | 11-probabilistic-models-and-uncertainty |
| quantile spread | 7 | 06-anatomy-of-a-predictor |
| quantisation | 12 | 26-low-latency-inference |
| quantisation-aware training | 12 | 26-low-latency-inference |
| quantitative easing | 2 | 01-central-banks-and-the-short-rate |
| quantitative investment strategy | 9 | 27-quantitative-investment-strategies |
| quantitative researcher | 17 | 17-quant-researcher |
| quanto adjustment | 5 | 17-multi-asset-options |
| quanto contract | 3 | 17-perpetual-futures |
| quanto option | 5 | 17-multi-asset-options |
| quarantine | 15 | 07-data-quality-and-lineage |
| quasi-maximum likelihood | 4 | 11-estimation |
| quasi-Monte Carlo | 4 | 26-monte-carlo |
| quasi-Newton method | 4 | 24-numerical-optimisation-in-practice |
| quasi-variational inequality | 4 | 10-optimal-stopping-and-impulse-control |
| query optimiser | 15 | 10-dataframes |
| query plan | 15 | 25-databases-and-sql |
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
| quote timer | 14 | 25-fixed-income-and-rfq-platform-connectivity |
| quoted depth | 3 | 16-spot-markets |
| quoted spread | 10 | 05-decomposing-the-spread |
| quoting obligation | 1 | 24-options-market-structure |
| rack unit | 14 | 08-servers |
| Radon--Nikodym derivative | 4 | 01-probability-at-speed |
| rain fade | 14 | 14-long-haul-wireless |
| random end | 10 | 10-auction-mechanics-and-theory |
| random forest | 12 | 05-trees-and-boosting |
| randomisation unit | 7 | 21-live-experiments |
| randomised quasi-Monte Carlo | 4 | 26-monte-carlo |
| range-based volatility estimator | 7 | 07-price-and-volume-features |
| rank acceptability | 17 | 30-choosing |
| rank correlation | 4 | 15-robust-statistics-and-heavy-tails |
| rank day | 8 | 10-index-rebalancing |
| rank information coefficient | 7 | 06-anatomy-of-a-predictor |
| rank transform | 7 | 06-anatomy-of-a-predictor |
| Rannacher time-stepping | 4 | 27-finite-difference-methods |
| rate limit | 3 | 15-centralised-exchanges |
| ratio adjustment | 7 | 02-market-data-for-research |
| raw capture | 15 | 02-capturing-and-storing-tick-data |
| reactive simulation | 15 | 11-backtest-engine-architecture |
| real yield | 2 | 11-inflation-markets |
| real-time risk system | 15 | 18-real-time-risk |
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
| receive-side scaling | 14 | 03-network-cards-and-kernel-bypass |
| receiver swap | 2 | 09-interest-rate-swaps |
| receiver swaption | 2 | 13-the-rates-options-market |
| recombining tree | 5 | 02-the-binomial-model |
| reconciliation | 15 | 22-post-trade-systems |
| reconciliation break | 15 | 22-post-trade-systems |
| record date | 1 | 08-shares-corporate-actions-indices |
| record linkage | 12 | 15-alternative-data-pipelines |
| recovery latency | 13 | 18-the-feed-handler |
| recovery point objective | 14 | 28-disaster-recovery-and-regulatory-requirements |
| recovery rate | 2 | 21-corporate-bonds |
| recovery time objective | 14 | 28-disaster-recovery-and-regulatory-requirements |
| recruiting cycle | 18 | 02-the-process-by-firm-type |
| recurrent neural network | 12 | 08-sequence-models-on-order-books |
| recursive least squares | 12 | 12-online-learning-and-drift |
| recycling trade | 9 | 28-hedging-a-structured-products-book |
| red team | 16 | 26-culture-and-decision-making |
| redemption gate | 16 | 04-the-asset-manager-and-the-fund |
| redemption notice period | 16 | 04-the-asset-manager-and-the-fund |
| redenomination risk | 2 | 07-european-and-japanese-government-bonds |
| redistribution licence | 16 | 22-data-strategy-and-costs |
| reduced-form model | 6 | 13-reduced-form-credit |
| redundant feed lines | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| reference data | 1 | 28-reading-market-data |
| reference entity | 2 | 23-credit-default-swaps |
| reference index | 2 | 11-inflation-markets |
| reference price waiver | 1 | 11-european-equity-market-structure |
| reference pricer | 5 | 28-build-a-pricing-library |
| reference quarter | 2 | 08-short-term-interest-rate-futures |
| reference-data service | 15 | 06-reference-data-and-symbology-services |
| refinancing incentive | 6 | 12-mortgage-modelling |
| reflected Brownian motion | 4 | 10-optimal-stopping-and-impulse-control |
| refresh-time sampling | 4 | 21-high-frequency-econometrics |
| regime-switching model | 12 | 20-clustering-regimes-and-anomaly-detection |
| register map | 14 | 07-programmable-hardware-ii-trading-designs |
| register-transfer level | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| regularisation | 4 | 16-linear-models-under-stress |
| regularisation path | 12 | 04-linear-and-regularised-baselines |
| regulated market | 1 | 11-european-equity-market-structure |
| regulatory assets under management | 17 | 04-quantitative-hedge-funds-and-systematic-managers |
| regulatory perimeter | 16 | 17-regulators-and-licences |
| rehypothecation | 1 | 06-financing |
| Reid vapour pressure | 3 | 03-refined-products-and-cracks |
| reinforcement learning | 12 | 17-reinforcement-learning-foundations |
| reject rate | 2 | 15-fx-spot-microstructure |
| relational model | 15 | 25-databases-and-sql |
| relative limit price | 10 | 03-empirical-facts-of-order-books |
| relative risk aversion | 4 | 09-stochastic-control |
| relative tick size | 10 | 06-tick-size-queues-and-priority |
| release lock-up | 11 | 18-news-and-event-trading |
| release race | 11 | 18-news-and-event-trading |
| release train | 15 | 27-testing-and-continuous-delivery |
| REMIT | 3 | 13-getting-access-commodities-and-power |
| remote hands | 14 | 09-colocation-products-and-how-they-are-sold |
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
| request for proposal | 16 | 20-build-against-buy |
| request for quote | 2 | 22-how-bonds-trade |
| request for stream | 10 | 21-execution-beyond-equities |
| request weight | 3 | 15-centralised-exchanges |
| research case study | 18 | 20-research-case-studies-and-take-homes |
| research engineer | 17 | 19-quant-developer |
| research hypothesis | 7 | 01-the-research-process |
| research library | 15 | 15-the-research-environment |
| research log | 7 | 01-the-research-process |
| research portfolio | 16 | 09-managing-researchers-traders-and-engineers |
| research review | 7 | 01-the-research-process |
| research unbundling | 10 | 20-the-buy-side-trading-desk-and-its-brokers |
| resend request | 13 | 15-protocols-i-fix |
| reservation price | 11 | 03-inventory-models |
| reservation value | 16 | 23-commercial-relationships-with-venues-brokers-and-vendors |
| reserve price | 4 | 29-games-auctions-and-information |
| reserved capacity | 15 | 26-cloud-against-on-premises |
| reserves | 2 | 01-central-banks-and-the-short-rate |
| residual momentum | 8 | 05-momentum |
| residual return | 7 | 06-anatomy-of-a-predictor |
| residual reversal | 8 | 02-short-term-reversal |
| residual risk add-on | 6 | 23-regulatory-capital-for-trading-books |
| residual risk hedge | 9 | 25-the-central-risk-book |
| resolution source | 3 | 27-prediction-and-betting-markets |
| REST interface | 13 | 17-websocket-rest-tls-and-json-at-speed |
| restaking | 3 | 23-defi-credit-and-leverage |
| restart rule | 16 | 08-managing-a-book-through-drawdown |
| restatement | 7 | 03-point-in-time-data-and-the-biases |
| restricted list | 16 | 16-compliance-and-market-abuse |
| restricted stock unit | 17 | 13-how-pay-works |
| results store | 15 | 11-backtest-engine-architecture |
| retail liquidity programme | 11 | 23-retail-wholesaling |
| retention policy | 15 | 02-capturing-and-storing-tick-data |
| retention ratio | 16 | 02-the-proprietary-market-making-firm |
| retraining schedule | 12 | 12-online-learning-and-drift |
| retransmission request | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| retrieval-augmented generation | 12 | 14-large-language-models-in-finance |
| return feature | 7 | 07-price-and-volume-features |
| return offer | 17 | 28-career-paths-and-moves |
| return on equity | 16 | 01-the-economics-of-a-trading-firm |
| return seasonality | 8 | 23-seasonality-and-calendar-effects |
| return smoothing | 7 | 22-performance-measurement |
| revaluation grid | 6 | 29-build-a-risk-engine |
| revaluation-based attribution | 6 | 27-pnl-explain-and-independent-price-verification |
| revenue budget | 16 | 06-the-head-of-desks-job |
| revenue capture | 11 | 01-the-business-of-market-making |
| revenue per head | 17 | 12-revenue-and-profit-across-the-industry |
| revenue pool | 17 | 07-bank-markets-divisions |
| revenue-share agreement | 16 | 25-launching-a-fund-and-raising-capital |
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
| risk appetite | 16 | 06-the-head-of-desks-job |
| risk appetite statement | 16 | 06-the-head-of-desks-job |
| risk bid | 10 | 22-portfolio-trades-and-risk-bids |
| risk budgeting | 7 | 26-portfolio-construction-ii |
| risk committee | 16 | 12-the-risk-management-function |
| risk contribution | 7 | 26-portfolio-construction-ii |
| risk culture | 16 | 12-the-risk-management-function |
| risk data aggregation | 6 | 29-build-a-risk-engine |
| risk engine | 6 | 29-build-a-risk-engine |
| risk exception | 16 | 12-the-risk-management-function |
| risk factor | 6 | 21-market-risk-measures |
| risk gate | 13 | 22-pre-trade-risk-and-kill-switches |
| risk grid | 15 | 20-the-risk-grid |
| risk hierarchy | 6 | 29-build-a-risk-engine |
| risk ladder | 6 | 03-rates-risk |
| risk limit | 6 | 29-build-a-risk-engine |
| risk of ruin | 2 | 29-thinking-in-expected-value |
| risk parity | 7 | 26-portfolio-construction-ii |
| risk pooling | 9 | 25-the-central-risk-book |
| risk quant | 17 | 18-bank-quant |
| risk reversal | 2 | 19-the-fx-options-market |
| risk snapshot | 15 | 18-real-time-risk |
| risk trader | 17 | 16-trader |
| risk transfer price | 10 | 21-execution-beyond-equities |
| risk-adjusted return on capital | 16 | 07-limits-and-capital-allocation |
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
| role-based access control | 15 | 29-security |
| roll | 1 | 21-basis-roll-and-delivery |
| roll window | 3 | 10-forward-curves-storage-and-convenience-yield |
| roll yield | 3 | 10-forward-curves-storage-and-convenience-yield |
| Roll's estimator | 4 | 21-high-frequency-econometrics |
| rollback | 15 | 27-testing-and-continuous-delivery |
| rolling intrinsic | 6 | 16-commodity-and-energy-derivatives |
| rollup | 3 | 14-blockchains-for-traders |
| roofline model | 15 | 14-accelerators-for-quantitative-work |
| rotation-equivariant estimator | 4 | 22-covariance-estimation-and-random-matrices |
| rough Bergomi model | 5 | 12-rough-volatility-and-forward-variance-models |
| rough volatility | 5 | 12-rough-volatility-and-forward-variance-models |
| round lot | 1 | 09-us-equity-market-structure |
| round-the-clock trading | 16 | 30-competition-and-the-future |
| round-trip efficiency | 3 | 06-power-markets-trading |
| round-trip triangulation | 14 | 17-where-the-crypto-venues-live |
| route diversity | 14 | 15-buying-connectivity |
| route factor | 14 | 10-the-north-american-map |
| route index | 3 | 11-freight-weather-and-other-corners |
| route racing | 14 | 19-cross-region-crypto-networks |
| row group | 15 | 03-columnar-formats |
| row-oriented layout | 15 | 03-columnar-formats |
| RPC endpoint | 3 | 26-crypto-data-and-infrastructure |
| Rule 605 report | 1 | 10-retail-flow-and-wholesaling |
| Rule 606 report | 1 | 10-retail-flow-and-wholesaling |
| rule of 72 | 18 | 08-mental-arithmetic |
| run record | 12 | 25-experiment-tracking-and-reproducibility |
| run-length encoding | 15 | 03-columnar-formats |
| run-the-bank spending | 16 | 19-technology-strategy |
| run-to-completion processing | 13 | 20-the-strategy-engine |
| runbook | 15 | 28-observability-and-incident-response |
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
| sanity check | 18 | 05-phone-and-technical-screens |
| scanning range | 1 | 20-margin |
| scenario conditioning | 6 | 22-stress-testing-and-scenarios |
| scenario fan-out | 15 | 20-the-risk-grid |
| schedule nomination | 3 | 13-getting-access-commodities-and-power |
| schedule-based initial margin | 6 | 25-margin-models |
| schema evolution | 15 | 04-a-tick-store-on-open-formats |
| schema validation | 12 | 15-alternative-data-pipelines |
| schema version | 15 | 04-a-tick-store-on-open-formats |
| Schwartz--Smith model | 6 | 16-commodity-and-energy-derivatives |
| score function | 4 | 11-estimation |
| search friction | 10 | 23-request-for-quote-and-dealer-markets-in-theory |
| searcher | 3 | 22-maximal-extractable-value |
| secant method | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| second-order cone programme | 4 | 23-convex-optimisation |
| second-price auction | 4 | 29-games-auctions-and-information |
| secret rotation | 15 | 29-security |
| secrets management | 15 | 29-security |
| securities information processor | 1 | 09-us-equity-market-structure |
| securities lending | 1 | 06-financing |
| securities transaction tax | 1 | 12-asian-and-emerging-equity-markets |
| securitisation | 2 | 25-loans-clos-and-securitisation |
| security master | 7 | 04-universe-symbology-and-corporate-actions |
| seed investor | 16 | 25-launching-a-fund-and-raising-capital |
| segregation of duties | 6 | 28-operational-risk-and-rogue-trading |
| self-custody | 3 | 24-the-crypto-trading-business |
| self-financing strategy | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| self-regulatory organisation | 16 | 17-regulators-and-licences |
| self-supervised learning | 12 | 10-representation-learning |
| self-trade prevention | 10 | 26-build-a-matching-engine-and-exchange-simulator |
| sell side | 1 | 02-the-sell-side |
| semidefinite programme | 4 | 23-convex-optimisation |
| semimartingale | 4 | 06-jump-processes |
| senior manager function | 17 | 25-leadership-roles |
| seniority | 2 | 21-corporate-bonds |
| sensitivities-based method | 6 | 23-regulatory-capital-for-trading-books |
| sensitivity cache | 15 | 18-real-time-risk |
| sentiment index | 8 | 24-positioning-and-sentiment |
| sentiment score | 7 | 12-alternative-and-text-data |
| separately managed account | 16 | 04-the-asset-manager-and-the-fund |
| sequence lock | 13 | 12-queues-ring-buffers-and-shared-memory |
| sequence number | 1 | 28-reading-market-data |
| sequencer | 3 | 14-blockchains-for-traders |
| sequencer architecture | 13 | 24-resilience |
| sequential bootstrap | 12 | 02-targets-labels-and-sample-weights |
| sequential consistency | 13 | 11-lock-free-programming |
| sequential importance resampling | 4 | 19-state-space-models-and-the-kalman-filter |
| sequential test | 7 | 21-live-experiments |
| sequential-trade model | 10 | 04-why-there-is-a-spread |
| serialisation cost | 15 | 08-python-at-scale |
| serialisation delay | 14 | 01-networking-for-trading |
| service credit | 14 | 15-buying-connectivity |
| service owner | 16 | 21-engineering-organisation-design |
| service-level agreement | 14 | 15-buying-connectivity |
| service-level indicator | 15 | 28-observability-and-incident-response |
| service-level objective | 15 | 28-observability-and-incident-response |
| session resumption | 13 | 17-websocket-rest-tls-and-json-at-speed |
| set-associative cache | 13 | 03-memory-hierarchy-and-caches |
| settlement | 1 | 05-clearing-and-settlement |
| settlement cycle | 1 | 05-clearing-and-settlement |
| settlement discipline regime | 16 | 13-operations |
| settlement fail | 1 | 05-clearing-and-settlement |
| settlement instruction | 15 | 22-post-trade-systems |
| settlement limit | 2 | 27-getting-access-fx |
| settlement risk | 2 | 20-settlement-risk |
| settlement-date position | 15 | 17-position-and-pnl-services |
| shadow deployment | 12 | 27-monitoring-and-retraining |
| shadow price | 4 | 23-convex-optimisation |
| shadow trading | 7 | 19-simulation-versus-live |
| SHAP value | 12 | 06-feature-engineering-selection-and-importance |
| shape risk | 3 | 06-power-markets-trading |
| Shapley value | 12 | 06-feature-engineering-selection-and-importance |
| share | 1 | 08-shares-corporate-actions-indices |
| share class | 16 | 04-the-asset-manager-and-the-fund |
| shared order book | 14 | 26-power-commodities-and-betting-connectivity |
| shared responsibility model | 15 | 26-cloud-against-on-premises |
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
| shortfall penalty | 16 | 23-commercial-relationships-with-venues-brokers-and-vendors |
| shrinkage estimator | 4 | 14-bayesian-methods |
| side letter | 16 | 04-the-asset-manager-and-the-fund |
| side pocket | 16 | 04-the-asset-manager-and-the-fund |
| sign-on bonus | 17 | 13-how-pay-works |
| signal autocorrelation | 7 | 13-half-life-decay-and-stability |
| signal combination | 7 | 14-signal-combination |
| signal half-life | 7 | 13-half-life-decay-and-stability |
| signal service | 15 | 16-signal-serving-and-parameter-management |
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
| simulation--production parity | 15 | 12-simulation-production-parity |
| simulator calibration | 7 | 19-simulation-versus-live |
| simultaneous multithreading | 13 | 02-cpu-microarchitecture |
| single-dealer platform | 2 | 14-the-fx-market |
| single-producer single-consumer queue | 13 | 12-queues-ring-buffers-and-shared-memory |
| single-root I/O virtualisation | 14 | 16-trading-in-a-public-cloud |
| single-stock future | 1 | 22-index-and-single-stock-futures-worldwide |
| singular control | 4 | 10-optimal-stopping-and-impulse-control |
| singular value decomposition | 4 | 25-floating-point-and-numerical-linear-algebra |
| site reliability engineer | 17 | 20-software-engineer |
| size of a test | 4 | 12-testing-and-multiple-testing |
| skew trade | 9 | 03-skew-and-term-structure-relative-value |
| skilled-worker visa | 17 | 27-locations |
| skip period | 7 | 07-price-and-volume-features |
| skywave propagation | 14 | 14-long-haul-wireless |
| Slater's condition | 4 | 23-convex-optimisation |
| slippage attribution | 10 | 19-transaction-cost-analysis |
| slippage tolerance | 3 | 22-maximal-extractable-value |
| slope factor | 6 | 03-rates-risk |
| slow consumer | 13 | 12-queues-ring-buffers-and-shared-memory |
| slow diffusion | 8 | 22-cross-asset-lead-lag |
| small-buffer optimisation | 13 | 06-cpp-for-latency-i-memory |
| small-cell suppression | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| small-tick asset | 10 | 06-tick-size-queues-and-priority |
| smart contract | 3 | 14-blockchains-for-traders |
| smart order router | 10 | 18-smart-order-routing |
| SmartNIC | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
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
| soft limit | 16 | 07-limits-and-capital-allocation |
| softs | 3 | 09-agriculturals-and-softs |
| sort key | 15 | 04-a-tick-store-on-open-formats |
| Sortino ratio | 7 | 22-performance-measurement |
| sound abstraction | 13 | 09-rust-for-low-latency |
| sour crude | 3 | 02-crude-oil |
| source-code escrow | 16 | 20-build-against-buy |
| sovereign spread | 2 | 07-european-and-japanese-government-bonds |
| sovereign wealth fund | 17 | 08-asset-managers-pensions-sovereign-funds-and-insurers |
| span | 15 | 28-observability-and-incident-response |
| spark spread | 3 | 05-power-markets-design |
| Spearman's rank correlation | 4 | 15-robust-statistics-and-heavy-tails |
| special | 1 | 16-stock-loan-and-short-selling |
| special opening quotation | 1 | 21-basis-roll-and-delivery |
| special purpose acquisition company | 8 | 12-share-classes-holding-companies-closed-end-funds-spacs |
| special repo rate | 2 | 05-repo-and-specials |
| special-purpose vehicle | 2 | 25-loans-clos-and-securitisation |
| specialness | 2 | 05-repo-and-specials |
| specialty-occupation visa | 17 | 27-locations |
| specific return | 7 | 24-risk-models |
| specific risk | 7 | 24-risk-models |
| specified pool | 2 | 12-mortgages-and-agencies |
| spectral density | 4 | 17-linear-time-series |
| speculative execution | 15 | 13-distributed-compute-and-schedulers |
| speculator | 1 | 18-futures-contracts-and-exchanges |
| speed bump | 11 | 09-latency-arbitrage-and-its-defence |
| spiked covariance model | 4 | 22-covariance-estimation-and-random-matrices |
| spin-off | 1 | 08-shares-corporate-actions-indices |
| spin-out | 17 | 03-the-options-market-making-houses |
| split brain | 13 | 24-resilience |
| sponsored access | 1 | 04-exchanges-brokers-venues |
| sponsored member | 2 | 28-getting-access-rates-credit |
| sponsored repo | 2 | 05-repo-and-specials |
| sponsored-access risk layer | 14 | 22-equities-and-options-connectivity |
| spoofing | 9 | 29-manipulative-strategies-and-how-they-are-caught |
| spot capacity | 15 | 26-cloud-against-on-premises |
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
| staff costs | 17 | 11-reading-a-trading-firms-accounts |
| stage gate | 7 | 01-the-research-process |
| staged investment | 16 | 24-entering-a-new-market |
| staged rollout | 7 | 21-live-experiments |
| stake limiting | 11 | 26-prediction-and-sports-market-making |
| staking yield | 3 | 23-defi-credit-and-leverage |
| stale-book flag | 13 | 18-the-feed-handler |
| stale-quote sniping | 11 | 09-latency-arbitrage-and-its-defence |
| stamp duty | 1 | 12-asian-and-emerging-equity-markets |
| standard coupon | 2 | 23-credit-default-swaps |
| standard error | 4 | 11-estimation |
| standard initial margin model | 6 | 25-margin-models |
| Standard Occupational Classification | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| standard settlement instruction | 15 | 22-post-trade-systems |
| standardised approach for counterparty credit risk | 6 | 19-funding-margin-and-capital-adjustments |
| standardised unexpected earnings | 7 | 11-fundamental-analyst-and-event-features |
| standing facility | 2 | 01-central-banks-and-the-short-rate |
| STAR structure | 18 | 28-behavioural-and-fit |
| start-of-day position | 15 | 17-position-and-pnl-services |
| stat-arb book | 8 | 01-anatomy-of-a-stat-arb-book |
| state price | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| state-price density | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| state-space model | 4 | 19-state-space-models-and-the-kalman-filter |
| statement of responsibilities | 17 | 25-leadership-roles |
| static arbitrage | 5 | 07-implied-volatility-and-its-surface |
| static hedging | 5 | 15-barriers-and-digitals |
| static polymorphism | 13 | 07-cpp-for-latency-ii-compile-time |
| static price band | 10 | 25-circuit-breakers-and-halts |
| stationary bootstrap | 4 | 13-resampling |
| stationary distribution | 4 | 04-stochastic-differential-equations |
| stationary process | 4 | 17-linear-time-series |
| statistical arbitrage | 8 | 01-anatomy-of-a-stat-arb-book |
| statistical factor model | 7 | 24-risk-models |
| statutory accounts | 17 | 11-reading-a-trading-firms-accounts |
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
| stop-loss rule | 16 | 08-managing-a-book-through-drawdown |
| stop-the-world pause | 13 | 10-managed-and-functional-languages-on-the-desk |
| stopping region | 4 | 10-optimal-stopping-and-impulse-control |
| stopping time | 4 | 01-probability-at-speed |
| storage deal | 9 | 22-storage-transport-and-physical-optionality |
| storage tier | 15 | 02-capturing-and-storing-tick-data |
| storage-limit risk | 8 | 21-calendar-spreads-and-curve-trades |
| store-and-forward switching | 14 | 02-switches-and-layer-1-devices |
| straddle | 5 | 04-greeks-and-the-hedging-pnl |
| straggler | 15 | 13-distributed-compute-and-schedulers |
| straight-through processing | 15 | 21-trade-capture-and-booking |
| strangle | 2 | 19-the-fx-options-market |
| strategy capacity | 7 | 28-capacity-decay-and-crowding |
| strategy correlation | 8 | 28-running-a-multi-strategy-book |
| strategy host | 15 | 12-simulation-production-parity |
| strategy lifecycle | 11 | 28-pnl-analytics-and-the-strategy-lifecycle |
| strategy wrapper | 9 | 27-quantitative-investment-strategies |
| strategy-stealing argument | 18 | 12-brainteasers-and-logic |
| stratified sampling | 4 | 26-monte-carlo |
| Stratonovich integral | 4 | 03-ito-calculus |
| stream processing | 15 | 01-the-platform-map |
| streaming execution | 15 | 10-dataframes |
| streaming quote | 2 | 15-fx-spot-microstructure |
| streaming telemetry | 14 | 05-capturing-and-monitoring-the-network |
| stress capital buffer | 16 | 05-the-bank-markets-division |
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
| structured interview | 16 | 10-hiring-and-compensation |
| structured logging | 15 | 28-observability-and-incident-response |
| structured note | 5 | 19-the-structured-products-business |
| structured product | 5 | 19-the-structured-products-business |
| structurer | 17 | 23-structurer-sales-and-sales-trader |
| structuring margin | 5 | 19-the-structured-products-business |
| stub quote | 1 | 31-stress-case-studies |
| Student-t copula | 6 | 15-portfolio-credit |
| style factor | 7 | 24-risk-models |
| stylised fact | 7 | 05-stylised-facts-of-returns |
| sub-account | 3 | 15-centralised-exchanges |
| sub-portfolio manager | 17 | 22-portfolio-manager-and-pod-analyst |
| submartingale | 4 | 01-probability-at-speed |
| subnormal number | 4 | 25-floating-point-and-numerical-linear-algebra |
| subordinator | 4 | 06-jump-processes |
| substitution effect | 12 | 06-feature-engineering-selection-and-importance |
| summer--winter spread | 3 | 04-natural-gas-and-lng |
| super senior tranche | 6 | 15-portfolio-credit |
| super-replication price | 5 | 01-no-arbitrage-and-the-fundamental-theorems |
| superday | 18 | 06-the-final-round-and-trading-games |
| superior predictive ability test | 4 | 12-testing-and-multiple-testing |
| supermartingale | 4 | 01-probability-at-speed |
| supervised learning | 12 | 01-why-financial-machine-learning-is-different |
| supervisory stress test | 6 | 22-stress-testing-and-scenarios |
| supplemental liquidity provider | 1 | 29-getting-access-equities |
| supply trade | 9 | 13-supply-trades |
| surface SVI | 5 | 08-parametrising-the-surface |
| surrogate model | 12 | 19-deep-hedging-and-machine-learning-in-pricing |
| surveillance alert | 15 | 30-surveillance-and-compliance-technology |
| survival horizon | 16 | 14-treasury-and-funding |
| survival probability | 2 | 23-credit-default-swaps |
| survivorship bias | 7 | 03-point-in-time-data-and-the-biases |
| suspicious transaction and order report | 16 | 16-compliance-and-market-abuse |
| SVI parametrisation | 5 | 08-parametrising-the-surface |
| swap dealer | 16 | 17-regulators-and-licences |
| swap execution facility | 2 | 09-interest-rate-swaps |
| swap market model | 6 | 08-forward-rate-and-market-models |
| swap spread | 2 | 09-interest-rate-swaps |
| swap-spread trade | 9 | 12-swap-spread-and-asset-swap-trades |
| swaption | 2 | 13-the-rates-options-market |
| swaption matrix | 6 | 05-sabr-in-rates-and-the-volatility-cube |
| sweep line | 18 | 21-algorithms-and-data-structures |
| sweet crude | 3 | 02-crude-oil |
| swing contract | 3 | 12-commodity-options-and-structured-hedges |
| swing pricing | 16 | 04-the-asset-manager-and-the-fund |
| swing weighting | 17 | 30-choosing |
| switch option | 6 | 09-bermudans-and-callables |
| switching cost | 16 | 20-build-against-buy |
| switching price | 3 | 07-emissions-and-environmental-markets |
| symbol resolution | 15 | 06-reference-data-and-symbology-services |
| symbology | 1 | 28-reading-market-data |
| symmetric orthogonalisation | 7 | 14-signal-combination |
| symmetry argument | 18 | 10-probability-i |
| synchronised routing | 10 | 18-smart-order-routing |
| syndication | 2 | 07-european-and-japanese-government-bonds |
| synthetic cross | 11 | 21-fx-market-making |
| synthetic twin | 8 | 04-pairs-and-baskets |
| system management interrupt | 14 | 08-servers |
| system of record | 15 | 01-the-platform-map |
| system time | 15 | 25-databases-and-sql |
| system-design interview | 18 | 26-system-design |
| systematic internaliser | 1 | 11-european-equity-market-structure |
| systematic manager | 17 | 04-quantitative-hedge-funds-and-systematic-managers |
| systematic strategy index | 5 | 19-the-structured-products-business |
| T+0 restriction | 1 | 12-asian-and-emerging-equity-markets |
| tag-value encoding | 13 | 15-protocols-i-fix |
| tail dependence coefficient | 4 | 15-robust-statistics-and-heavy-tails |
| tail hedge | 9 | 07-tail-hedging-and-long-volatility |
| tail index | 4 | 15-robust-statistics-and-heavy-tails |
| tail latency | 13 | 01-where-latency-comes-from |
| take threshold | 11 | 07-short-horizon-alpha |
| take-home assignment | 18 | 20-research-case-studies-and-take-homes |
| take-or-pay clause | 3 | 12-commodity-options-and-structured-hedges |
| tape | 4 | 28-transforms-interpolation-and-algorithmic-differentiation |
| target leakage | 12 | 03-validation |
| target network | 12 | 18-reinforcement-learning-for-execution-and-market-making |
| target redemption forward | 5 | 20-fx-derivatives |
| target-close algorithm | 10 | 16-benchmark-algorithms |
| task granularity | 15 | 20-the-risk-grid |
| task graph | 15 | 13-distributed-compute-and-schedulers |
| tax drag | 16 | 15-finance-product-control-and-tax |
| tax residence | 17 | 15-pay-regulation-and-tax-by-location |
| Taylor effect | 7 | 05-stylised-facts-of-returns |
| TCP offload engine | 14 | 07-programmable-hardware-ii-trading-designs |
| team tenure | 17 | 05-multi-manager-platforms |
| team turnover rate | 17 | 05-multi-manager-platforms |
| technical interview | 18 | 01-what-each-interview-tests-by-role |
| technical screen | 18 | 05-phone-and-technical-screens |
| technology treadmill | 16 | 02-the-proprietary-market-making-firm |
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
| termination event | 16 | 18-legal-documentation |
| test pyramid | 15 | 27-testing-and-continuous-delivery |
| test set | 12 | 01-why-financial-machine-learning-is-different |
| testbench | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| theoretical value | 5 | 26-options-market-making-in-practice |
| theory of storage | 3 | 10-forward-curves-storage-and-convenience-yield |
| thermal design power | 14 | 08-servers |
| theta | 5 | 04-greeks-and-the-hedging-pnl |
| theta scheme | 4 | 27-finite-difference-methods |
| think-aloud protocol | 18 | 05-phone-and-technical-screens |
| thinning | 4 | 07-point-processes-and-hawkes-processes |
| thread divergence | 15 | 14-accelerators-for-quantitative-work |
| threat model | 15 | 29-security |
| three lines of defence | 6 | 26-model-risk-and-validation |
| three-month price | 3 | 08-metals |
| three-way collar | 3 | 12-commodity-options-and-structured-hedges |
| tick bar | 7 | 02-market-data-for-research |
| tick data | 15 | 02-capturing-and-storing-tick-data |
| tick rule | 7 | 09-trade-flow-features |
| tick size | 10 | 01-the-limit-order-book |
| tick store | 15 | 04-a-tick-store-on-open-formats |
| tick value | 1 | 18-futures-contracts-and-exchanges |
| tick-to-trade latency | 13 | 01-where-latency-comes-from |
| ticker change | 7 | 04-universe-symbology-and-corporate-actions |
| ticker plant | 14 | 27-the-vendor-map |
| tickless kernel | 13 | 13-linux-tuning |
| tier cliff | 11 | 17-rebates-inverted-venues-and-tiers |
| tier matching | 3 | 25-getting-access-crypto-venues |
| time bar | 7 | 02-market-data-for-research |
| time bucket | 15 | 05-time-series-databases-and-the-alternatives |
| time charter | 3 | 11-freight-weather-and-other-corners |
| time in force | 10 | 02-order-types-and-their-uses |
| time stop | 16 | 08-managing-a-book-through-drawdown |
| time to detect | 15 | 28-observability-and-incident-response |
| time to first trade | 16 | 24-entering-a-new-market |
| time to restore | 15 | 28-observability-and-incident-response |
| time-charter equivalent | 3 | 11-freight-weather-and-other-corners |
| time-decay weight | 12 | 02-targets-labels-and-sample-weights |
| time-series database | 15 | 05-time-series-databases-and-the-alternatives |
| time-series momentum | 8 | 19-trend-following |
| time-stamp counter | 13 | 02-cpu-microarchitecture |
| time-travel query | 15 | 25-databases-and-sql |
| timer wheel | 13 | 20-the-strategy-engine |
| timestamp trailer | 14 | 05-capturing-and-monitoring-the-network |
| timing adjustment | 6 | 06-convexity-adjustments-and-constant-maturity-products |
| timing closure | 14 | 06-programmable-hardware-i-architecture-and-toolchain |
| Title Transfer Facility | 3 | 04-natural-gas-and-lng |
| TLS handshake | 13 | 17-websocket-rest-tls-and-json-at-speed |
| to-be-announced trade | 2 | 12-mortgages-and-agencies |
| token | 3 | 14-blockchains-for-traders |
| token bucket | 13 | 21-order-gateway-and-order-management |
| token compensation | 17 | 10-crypto-native-firms |
| token market-making agreement | 3 | 24-the-crypto-trading-business |
| token unlock | 3 | 24-the-crypto-trading-business |
| token warrant | 17 | 10-crypto-native-firms |
| tokenisation | 12 | 13-text-from-bag-of-words-to-embeddings |
| tokenised fund | 16 | 30-competition-and-the-future |
| tom-next | 2 | 16-fx-swaps-forwards-and-the-cross-currency-basis |
| tool call | 12 | 14-large-language-models-in-finance |
| top-coding | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| top-order allocation | 1 | 19-matching-algorithms-and-implied-spreads |
| topic model | 12 | 13-text-from-bag-of-words-to-embeddings |
| total compensation | 17 | 13-how-pay-works |
| total cost of ownership | 16 | 20-build-against-buy |
| total implied variance | 5 | 07-implied-volatility-and-its-surface |
| total least squares | 4 | 16-linear-models-under-stress |
| total number of allowances in circulation | 3 | 07-emissions-and-environmental-markets |
| total return future | 1 | 22-index-and-single-stock-futures-worldwide |
| total return index | 1 | 08-shares-corporate-actions-indices |
| total return swap | 1 | 06-financing |
| touch fill | 7 | 17-event-driven-backtests |
| toxicity score | 11 | 06-adverse-selection-and-toxicity |
| traceability to UTC | 14 | 04-time-synchronisation |
| track record portability | 16 | 25-launching-a-fund-and-raising-capital |
| tracking error | 1 | 03-the-buy-side |
| tradable universe | 7 | 04-universe-symbology-and-corporate-actions |
| trade amendment | 15 | 21-trade-capture-and-booking |
| trade at settlement | 1 | 21-basis-roll-and-delivery |
| trade bust | 15 | 17-position-and-pnl-services |
| trade capture | 15 | 21-trade-capture-and-booking |
| trade compression | 2 | 09-interest-rate-swaps |
| trade condition | 1 | 28-reading-market-data |
| trade confirmation | 15 | 22-post-trade-systems |
| trade expression | 9 | 17-discretionary-macro |
| trade finance | 3 | 13-getting-access-commodities-and-power |
| trade lifecycle event | 15 | 21-trade-capture-and-booking |
| trade price impact | 10 | 05-decomposing-the-spread |
| trade reporting | 2 | 22-how-bonds-trade |
| trade secret | 16 | 11-intellectual-property-and-non-competes |
| trade sign | 7 | 09-trade-flow-features |
| trade surveillance system | 15 | 30-surveillance-and-compliance-technology |
| trade-date position | 15 | 17-position-and-pnl-services |
| trade-through | 1 | 09-us-equity-market-structure |
| trading arcade | 17 | 06-medium-frequency-proprietary-shops |
| trading book | 6 | 23-regulatory-capital-for-trading-books |
| trading game | 18 | 06-the-final-round-and-trading-games |
| trading halt | 8 | 17-news-and-events |
| trading pause | 10 | 25-circuit-breakers-and-halts |
| trading period | 8 | 04-pairs-and-baskets |
| trading trajectory | 10 | 14-the-almgren-chriss-framework |
| trading-system developer | 17 | 19-quant-developer |
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
| transaction charge | 14 | 26-power-commodities-and-betting-connectivity |
| transaction cost analysis | 7 | 23-measuring-market-making-and-execution |
| transaction propagation network | 14 | 21-on-chain-connectivity |
| transaction reporting | 15 | 30-surveillance-and-compliance-technology |
| transaction-triggered price manipulation | 10 | 12-transient-impact-and-propagator-models |
| transactional outbox | 15 | 24-messaging-and-event-driven-architecture |
| transfer coefficient | 7 | 15-from-signal-to-forecast |
| transfer latency | 3 | 16-spot-markets |
| transfer pricing | 16 | 15-finance-product-control-and-tax |
| transformer | 12 | 08-sequence-models-on-order-books |
| transient impact model | 10 | 12-transient-impact-and-propagator-models |
| transition management | 8 | 29-the-asset-managers-strategies |
| translation lookaside buffer | 13 | 03-memory-hierarchy-and-caches |
| transparent clock | 14 | 04-time-synchronisation |
| transport option | 9 | 22-storage-transport-and-physical-optionality |
| trapped assets | 16 | 27-crisis-management |
| travel rule | 3 | 24-the-crypto-trading-business |
| Treasury bill | 2 | 02-money-markets |
| trend following | 8 | 19-trend-following |
| tri-party repo | 2 | 05-repo-and-specials |
| trial count | 7 | 01-the-research-process |
| triangular arbitrage | 3 | 16-spot-markets |
| tridiagonal matrix algorithm | 4 | 25-floating-point-and-numerical-linear-algebra |
| trigger packet | 14 | 05-capturing-and-monitoring-the-network |
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
| two-pointer technique | 18 | 21-algorithms-and-data-structures |
| two-scales realised variance | 4 | 21-high-frequency-econometrics |
| UCITS | 16 | 04-the-asset-manager-and-the-fund |
| unallocated gold | 3 | 08-metals |
| unbiased estimator | 4 | 11-estimation |
| uncertainty set | 7 | 26-portfolio-construction-ii |
| uncertainty-zone model | 10 | 06-tick-size-queues-and-priority |
| uncleared margin rules | 2 | 10-swap-clearing-and-the-ccp-basis |
| uncrossing price | 1 | 13-auctions |
| undefined behaviour | 13 | 08-cpp-for-latency-iii-the-compiler |
| underwriting | 1 | 02-the-sell-side |
| unencumbered cash | 16 | 14-treasury-and-funding |
| unexplained P\&L | 6 | 27-pnl-explain-and-independent-price-verification |
| unicast dissemination | 14 | 12-the-asia-pacific-map |
| uniform integrability | 4 | 01-probability-at-speed |
| uniform-price auction | 2 | 04-the-treasury-market |
| unilateral irrevocable payment time | 2 | 20-settlement-risk |
| unique transaction identifier | 15 | 21-trade-capture-and-booking |
| unit in the last place | 4 | 25-floating-point-and-numerical-linear-algebra |
| unit of count | 15 | 23-market-data-distribution-and-entitlements |
| unit root | 4 | 17-linear-time-series |
| unit test | 15 | 27-testing-and-continuous-delivery |
| universe membership | 7 | 04-universe-symbology-and-corporate-actions |
| unrealised P\&L | 1 | 07-pnl-and-positions |
| unsupervised learning | 12 | 01-why-financial-machine-learning-is-different |
| unwind | 7 | 28-capacity-decay-and-crowding |
| upfront payment | 2 | 23-credit-default-swaps |
| uptick rule | 1 | 12-asian-and-emerging-equity-markets |
| uptime requirement | 3 | 25-getting-access-crypto-venues |
| upwind scheme | 4 | 27-finite-difference-methods |
| urgency | 10 | 14-the-almgren-chriss-framework |
| usage report | 15 | 23-market-data-distribution-and-entitlements |
| user-space network stack | 14 | 03-network-cards-and-kernel-bypass |
| utilisation | 1 | 16-stock-loan-and-short-selling |
| utility function | 4 | 09-stochastic-control |
| valid time | 7 | 03-point-in-time-data-and-the-biases |
| validation set | 12 | 01-why-financial-machine-learning-is-different |
| validator | 3 | 14-blockchains-for-traders |
| validity bitmap | 15 | 03-columnar-formats |
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
| vectorised query execution | 15 | 05-time-series-databases-and-the-alternatives |
| vega | 5 | 04-greeks-and-the-hedging-pnl |
| vega bucket | 5 | 26-options-market-making-in-practice |
| vega notional | 5 | 14-variance-swaps-and-volatility-derivatives |
| vega weighting | 5 | 24-fourier-pricing-and-calibration-engineering |
| velocity logic | 10 | 25-circuit-breakers-and-halts |
| vendor correction | 15 | 07-data-quality-and-lineage |
| vendor lock-in | 16 | 20-build-against-buy |
| venue clock skew | 14 | 20-api-engineering-for-crypto-venues |
| venue profile | 11 | 29-a-venue-playbook |
| venue ranking | 10 | 18-smart-order-routing |
| venue risk | 8 | 27-crypto-medium-frequency-strategies |
| vesting schedule | 16 | 10-hiring-and-compensation |
| virtual bid | 3 | 06-power-markets-trading |
| virtual private cloud | 14 | 18-private-connectivity-to-crypto-venues |
| virtual trading point | 3 | 04-natural-gas-and-lng |
| virtual-network peering | 14 | 18-private-connectivity-to-crypto-venues |
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
| volume commitment | 16 | 23-commercial-relationships-with-venues-brokers-and-vendors |
| volume participation cap | 7 | 17-event-driven-backtests |
| volume smile | 8 | 13-intraday-patterns |
| volume surprise | 7 | 07-price-and-volume-features |
| volume tier | 1 | 29-getting-access-equities |
| volume-driven cost | 16 | 01-the-economics-of-a-trading-firm |
| volume-weighted average price | 7 | 02-market-data-for-research |
| von Neumann stability analysis | 4 | 27-finite-difference-methods |
| voyage charter | 3 | 11-freight-weather-and-other-corners |
| VPIN | 7 | 09-trade-flow-features |
| VWAP algorithm | 10 | 16-benchmark-algorithms |
| VWAP slippage | 7 | 23-measuring-market-making-and-execution |
| wage level | 17 | 14-pay-levels-by-role-firm-type-and-seniority |
| wait-free | 13 | 11-lock-free-programming |
| walk-forward analysis | 7 | 20-overfitting |
| wall-crossing | 16 | 16-compliance-and-market-abuse |
| warehouse warrant | 3 | 08-metals |
| warm-up period | 13 | 10-managed-and-functional-languages-on-the-desk |
| WASDE report | 3 | 09-agriculturals-and-softs |
| wash trading | 3 | 16-spot-markets |
| wash-sale rule | 16 | 15-finance-product-control-and-tax |
| watch list | 16 | 16-compliance-and-market-abuse |
| wavelength service | 14 | 13-long-haul-fibre |
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
| what-if check | 15 | 18-real-time-risk |
| when-issued trading | 2 | 04-the-treasury-market |
| white noise | 4 | 17-linear-time-series |
| wholesaler | 1 | 10-retail-flow-and-wholesaling |
| wide format | 15 | 10-dataframes |
| width | 2 | 30-market-making-games |
| wildcard option | 2 | 06-bond-futures |
| win-probability model | 11 | 22-bond-and-etf-request-for-quote-market-making |
| window function | 15 | 10-dataframes |
| winner's curse | 2 | 30-market-making-games |
| winsorisation | 4 | 15-robust-statistics-and-heavy-tails |
| wire-to-wire latency | 13 | 01-where-latency-comes-from |
| withdrawal allow-list | 15 | 29-security |
| withholding tax | 1 | 17-delta-one-instruments |
| word embedding | 12 | 13-text-from-bag-of-words-to-embeddings |
| work stealing | 15 | 13-distributed-compute-and-schedulers |
| working set | 13 | 03-memory-hierarchy-and-caches |
| working-time opt-out | 17 | 26-hours-rhythm-and-intensity |
| worst-case exposure | 13 | 22-pre-trade-risk-and-kill-switches |
| worst-of option | 5 | 17-multi-asset-options |
| write-ahead log | 15 | 25-databases-and-sql |
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
| zero-copy networking | 14 | 03-network-cards-and-kernel-bypass |
| zero-cost abstraction | 13 | 09-rust-for-low-latency |
| zero-coupon inflation swap | 2 | 11-inflation-markets |
| zero-coupon rate | 2 | 03-government-bonds |
| zero-day option | 1 | 26-zero-day-options-and-retail-flow |
| zero-intelligence model | 10 | 01-the-limit-order-book |
| zero-sum game | 4 | 29-games-auctions-and-information |
| zero-trust architecture | 15 | 29-security |
| zone map | 15 | 03-columnar-formats |
| zone of possible agreement | 16 | 23-commercial-relationships-with-venues-brokers-and-vendors |

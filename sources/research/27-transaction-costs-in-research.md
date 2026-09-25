# 27. Transaction Costs in Research — brief and source ledger

## Brief

- **Hook.** A daily signal has a gross Sharpe ratio of 2.5. After costs it has 0.3. Rebuilt with the costs inside the optimiser and a slower signal, it has 1.1.
- **Sections.** Cost models; Estimating costs from your own fills; Costs inside the optimiser; Netting across strategies; Cost-aware signals.
- **Defines.** temporary impact, permanent impact, square-root impact law, percentage of volume, cost-aware optimisation, internal crossing, signal smoothing, break-even cost.
- **Uses (defined earlier).** bid--ask spread (B1.1), effective spread (B1.10), market impact (ch18), implementation shortfall (ch19), linear cost model (ch16), portfolio turnover (ch16), mean--variance optimisation (ch25), turnover penalty (ch25), aim portfolio (ch26), second-order cone programme (B4.23).
- **Tutorial.** Fit a square-root impact model to simulated fills, put spread and power-law impact inside firm.portcons, and compare naive, cost-penalised and smoothed-signal books by net Sharpe ratio against assets under management.
- **Build.** `firm.tcost`: cost model (spread, fees, square-root impact with fitted coefficients), power-cost terms for firm.portcons as cone constraints, netting engine for several strategies' trade lists with the savings allocated; Python.
- **Weekend problem.** From 2.5 to 0.3 — named result: the net Sharpe ratio against the signal-smoothing half-life, and the optimal smoothing.
- **Facts to verify.** Almgren, Thum, Hauptmann, Li 2005, direct estimation of equity market impact (Risk); Toth et al. 2011 anomalous price impact (Physical Review X); Frazzini, Israel, Moskowitz 2018, Trading costs (working paper); Kyle and Obizhaeva 2016 market microstructure invariance (Econometrica); Bouchaud, Bonart, Donier, Gould 2018, Trades, Quotes and Prices; Loeb 1983 trading cost (FAJ).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | B. Toth, Y. Lemperiere, C. Deremble, J. de Lataillade, J. Kockelkoren, J.-P. Bouchaud, "Anomalous Price Impact and the Critical Nature of Liquidity in Financial Markets", Physical Review X 1 (2011) 021006: a V-shaped average supply/demand profile vanishing at the current price; metaorders must be fragmented; the square-root impact law, with additional empirical support | Crossref metadata; arXiv 1105.1694 abstract | https://doi.org/10.1103/PhysRevX.1.021006 | 2026-09-25 | "explaining the 'square-root' impact law, for which we provide additional empirical support"; "large metaorders have to be fragmented in order to be digested by the liquidity funnel" | section 1; def. square-root impact law; omsources |
| F2 | R. Almgren, C. Thum, E. Hauptmann, H. Li, "Direct Estimation of Equity Market Impact" (Citigroup Global Quantitative Research, May 2005; Risk, 2005): almost 700,000 US stock orders executed by Citigroup equity trading desks, December 2001 to June 2003; coefficients depend on volatility, average daily volume and turnover; the square-root model for temporary impact as a function of trade rate is rejected in favour of a 3/5 power law | Paper PDF (University of Pennsylvania course mirror), pdftotext | https://www.cis.upenn.edu/~mkearns/finread/costestim.pdf | 2026-09-25 | "We reject the common square-root model for temporary impact as function of trade rate, in favor of a 3/5 power law across the range of order sizes considered"; "almost 700,000 US stock trade orders executed by Citigroup Equity Trading" | sections 1-2; def. temporary impact, permanent impact; exo 8; iq 1; omsources |
| F3 | A. S. Kyle, A. A. Obizhaeva, "Market Microstructure Invariance: Empirical Hypotheses", Econometrica 84(4) (2016) 1345-1404: the distributions of bets and transaction costs are constant across assets per unit of business time; empirical tests on 400,000+ portfolio transition orders support the hypotheses | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.3982/ECTA10486 | 2026-09-25 | "Empirical tests based on a data set of 400,000+ portfolio transition orders support the invariance hypotheses" | section 2; omsources |
| F4 | J.-P. Bouchaud, J. Bonart, J. Donier, M. Gould, Trades, Quotes and Prices, Cambridge University Press (2018): empirical facts and models of markets from order arrivals to stability, calibrated on Nasdaq data | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.1017/9781316659335 | 2026-09-25 | "all models are calibrated and evaluated using recent data from Nasdaq" | section 1; omsources |

## EXCLUDED

- Frazzini, Israel and Moskowitz (2018), Trading Costs: no abstract reachable (SSRN refuses scripts, no metadata
  abstract); not cited.
- Loeb (1983): bibliographic metadata only; not cited.
- The cost law, the fills and the books are simulated; every estimate and Sharpe ratio is computed and tested.


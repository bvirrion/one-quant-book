# 3. Residual and Principal-Component Stat Arb — brief and source ledger

## Brief

- **Hook.** Regress each stock's returns on its industry ETF and trade the residual when it drifts two standard deviations from its mean: the method is public, the parameters are everything, and the published version's returns faded after 2002.
- **Sections.** Residuals against factors or principal components; The residual as an Ornstein--Uhlenbeck process: the s-score; Entry, exit and the mean-reversion speed filter; Eigenportfolios and their stability; Where the returns went.
- **Defines.** s-score, eigenportfolio, mean-reversion speed filter.
- **Uses (defined earlier).** Ornstein--Uhlenbeck process (B4.4), principal component analysis (B4.22), statistical factor model (B7.24), specific return (B7.24), half-life (B4.4), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** ETF-residual s-score strategy; principal-component residual strategy; industry-neutral residual book; volume-conditioned residual strategy.
- **Tutorial.** Fit 60-day OU models to residuals against the chapter 24 factors and against 15 principal components on firm.synthmkt, trade s-scores with Avellaneda and Lee's thresholds, and measure the effect of the mean-reversion-speed filter and of the planted reversal's strength.
- **Build.** `firm.residarb`: rolling residual extraction (factor model or PCA eigenportfolios), OU fit by AR(1) regression, s-scores with thresholds and a speed filter, and the book; Python.
- **Weekend problem.** The public method — named result: the Sharpe ratio of the s-score strategy with and without the speed filter, and its sensitivity to the entry threshold.
- **Facts to verify.** Avellaneda and Lee 2010 (Quantitative Finance); Pole 2007, Statistical Arbitrage (Wiley); Khandani and Lo 2011 (as B7.28).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Avellaneda, J.-H. Lee, "Statistical arbitrage in the US equities market", Quantitative Finance 10(7) (2010) 761-782: residuals of stock returns against PCA factors or sector ETFs modelled as mean-reverting; after transaction costs PCA strategies had an average annual Sharpe ratio of 1.44 over 1997-2007, much stronger before 2003 and 0.9 in 2003-2007; ETF strategies 1.1 over 1997-2007 with a similar degradation after 2002; ETF strategies using volume information 1.51 in 2003-2007; results consistent with Khandani and Lo's unwinding theory for August 2007 | Crossref metadata; the authors' working-paper PDF (version of 15 June 2009), abstract | https://doi.org/10.1080/14697680903124632 ; https://math.nyu.edu/~avellane/AvellanedaLeeStatArb20090616.pdf | 2026-09-25 | abstract: "PCA-based strategies have an average annual Sharpe ratio of 1.44 over the period 1997 to 2007"; "During 2003-2007, the average Sharpe ratio of PCA-based strategies was only 0.9"; "ETF strategies which use volume information achieve a Sharpe ratio of 1.51 from 2003 to 2007" | hook; section 5; strat:s1:residual-and-principal-component-stat-arb:etf; strat:s1:residual-and-principal-component-stat-arb:pca; strat:s1:residual-and-principal-component-stat-arb:volume; omsources |
| F2 | Avellaneda and Lee's method (working-paper PDF): 60-day estimation window; cumulative residual fitted as an AR(1), kappa = -log(b) x 252, m = a / (1 - b), sigma_eq = sqrt(var(zeta) / (1 - b^2)); s-score (X - m) / sigma_eq, with centred means; stocks kept only with mean-reversion time below half the window, kappa > 252/30 = 8.4 (0 < b < 0.9672); open at s < -1.25 (buy) or s > 1.25 (sell), close longs at s > -0.50 and shorts at s < 0.75, cutoffs chosen on 2000-2004; slippage of 5 basis points per trade (10 round trip); bang-bang positions of a fixed fraction of equity, "2+2" leverage; eigenportfolio weights v_i / sigma_i from the correlation matrix of the last 252 days, 15 factors or enough to explain 55% of the variance; trading time: returns scaled by average over current volume (10-day average) | the working-paper PDF, sections 4-5 and appendix | https://math.nyu.edu/~avellane/AvellanedaLeeStatArb20090616.pdf | 2026-09-25 | "We selected stocks with mean-reversion times less than 1/2 period (kappa > 252/30 = 8.4)"; "sbo = sso = 1.25, sbc = 0.75 and ssc = 0.50"; "a slippage/transaction cost of 0.05% or 5 basis points per trade"; "we found that centered means work better"; "This all-or-nothing strategy ... turns out to outperform making continuous portfolio adjustments, probably due to model mis-specification"; footnote 13: "we can use 90 days to estimate the regression and 60 days to estimate the process" | sections 1-3; tutorial; strat:s1:residual-and-principal-component-stat-arb:etf; strat:s1:residual-and-principal-component-stat-arb:pca; strat:s1:residual-and-principal-component-stat-arb:industry |
| F3 | A. E. Khandani, A. W. Lo (2011): as Book 7 chapter 28, F1 | as Book 7 | https://doi.org/10.1016/j.finmar.2010.07.005 | 2026-09-25 | as Book 7 | section 5; omsources |
| F4 | A. Pole, Statistical Arbitrage, Wiley (print ISBN 978-0-470-13844-1; online edition 2012) | Crossref metadata | https://doi.org/10.1002/9781119197072 | 2026-09-25 | Crossref: title, author (Andrew Pole), publisher, ISBNs | omsources |

## EXCLUDED

- Pole (2007), the book's content: only its metadata accessed; further reading.
- Avellaneda and Lee's detailed results tables beyond the abstract and the method: the chapter quotes the method and the abstract's numbers only.
- Every number about the synthetic market is computed on firm.synthmkt (with the planted mean-reverting level, MarketConfig.ou_share) and tested.


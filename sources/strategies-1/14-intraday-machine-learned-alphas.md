# 14. Intraday Machine-Learned Alphas — brief and source ledger

## Brief

- **Hook.** A gradient-boosted model on order-book features predicts the next thirty seconds with an R-squared of one per cent; that is enough to pay the spread only if execution is part of the model.
- **Sections.** Targets and horizons; Features from the book and the tape; Models and their validation; Coupling the alpha to execution.
- **Defines.** intraday alpha, prediction horizon, execution coupling.
- **Uses (defined earlier).** order-flow imbalance (B7.8), microprice (B7.8), purging (B7.20), embargo (B7.20), mark-out curve (B7.23), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** book-imbalance alpha; trade-flow alpha; cross-asset lead alpha; alpha-driven execution.
- **Tutorial.** Train linear and tree models on firm.tape order-book features for 5-, 30- and 120-second mid returns with purged cross-validation, then trade them through the chapter 18 replay with and without passive execution.
- **Build.** `firm.intraml`: feature matrices from firm.lobfeat and firm.tradeflow, horizon targets, purged walk-forward training (ridge and a small gradient-boosted tree ensemble in NumPy), and alpha-driven order placement; Python.
- **Weekend problem.** One per cent is a lot — named result: out-of-sample R-squared by horizon and the P&L per share after the spread, aggressive against passive.
- **Facts to verify.** Cont, Kukanov, Stoikov 2014 (J. Financial Econometrics); Kolm, Turiel, Westray 2023, Deep order flow imbalance (Mathematical Finance); Sirignano and Cont 2019 universal features of price formation (Quantitative Finance); Friedman 2001 gradient boosting (Annals of Statistics).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Cont, A. Kukanov, S. Stoikov, "The price impact of order book events", Journal of Financial Econometrics 12(1) (2014) 47-88: as Book 7 chapter 8, F1 (over short intervals price changes are mainly driven by order-flow imbalance; linear relation with slope inversely proportional to depth) | as Book 7 | http://arxiv.org/abs/1011.6402 | 2026-09-25 | as Book 7 | section 2; strat:s1:intraday-machine-learned-alphas:book; omsources |
| F2 | P. N. Kolm, J. Turiel, N. Westray, "Deep order flow imbalance: extracting alpha at multiple horizons from the limit order book", Mathematical Finance 33(4) (2023) 1044-1081: deep learning forecasts of high-frequency returns at multiple horizons for 115 Nasdaq stocks; models trained on stationary order-flow inputs outperform most models trained on raw order books; the effective horizon of stock-specific forecasts is about two average price changes | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/mafi.12413 | 2026-09-25 | abstract: "models trained on order flow significantly outperform most models trained directly on order books"; "the effective horizon of stock specific forecasts is approximately two average price changes" | hook; section 1; section 3; strat:s1:intraday-machine-learned-alphas:flow; omsources |
| F3 | J. Sirignano, R. Cont, "Universal features of price formation in financial markets: perspectives from deep learning", Quantitative Finance 19(9) (2019) 1449-1459: deep learning on billions of US equity quotes and trades finds a universal, stationary price-formation mechanism; a model trained on all stocks outperforms asset-specific models out of sample, including on stocks not in the training sample; longer price and order-flow history improves forecasts | Crossref metadata; arXiv abstract 1803.06917 | https://doi.org/10.1080/14697688.2019.1622295 ; https://arxiv.org/abs/1803.06917 | 2026-09-25 | abstract: "evidence for the existence of a universal and stationary price formation mechanism"; "The universal model --- trained on data from all stocks --- outperforms ... asset-specific linear and nonlinear models" | section 3; omsources |
| F4 | J. H. Friedman, "Greedy function approximation: a gradient boosting machine", Annals of Statistics 29(5) (2001) | Crossref metadata | https://doi.org/10.1214/aos/1013203451 | 2026-09-25 | Crossref: author, title, journal, volume, issue, year | section 3; omsources |

## EXCLUDED

- Published R-squared values of intraday return forecasts: not quoted (abstracts give none); the chapter reports its own out-of-sample numbers on the synthetic tape.
- Named firms' intraday alpha desks: none named.


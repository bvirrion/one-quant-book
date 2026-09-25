# 27. Quantitative Investment Strategies — brief and source ledger

## Brief

- **Hook.** A bank can package a carry or momentum strategy as an index, license it, and sell swaps on it; the backtest that sells it is written before the index goes live, and its returns after launch are lower.
- **Sections.** Rules-based indices as products; Wrappers and fees; Hedging the index; Live against backtest.
- **Defines.** quantitative investment strategy, index backtest decay, strategy wrapper.
- **Uses (defined earlier).** systematic strategy index (B5.19), backtest overfitting (B7.20), deflated Sharpe ratio (B4.12), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** risk-premia index swap; volatility-carry index; multi-asset risk-premia basket; defensive overlay index.
- **Tutorial.** Design twenty candidate indices on the synthetic markets, select the best backtests as a bank's product team would, and measure the live decay against the deflated Sharpe ratio's prediction.
- **Build.** `firm.qis`: index rulebooks, backtest selection, fee and hedging costs, and live-versus-backtest comparison; Python.
- **Weekend problem.** Written before launch — named result: the gap between the selected indices' backtest and live Sharpe ratios.
- **Facts to verify.** Suhonen, Lennkh, Perez 2017 quantifying backtest overfitting in alternative beta strategies (JPM); Vatanen and Suhonen or equivalent.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. Suhonen, M. Lennkh, F. Perez, "Quantifying backtest overfitting in alternative beta strategies", Journal of Portfolio Management 43(2) (2017) 90-104: 215 alternative-beta trading strategies developed and promoted by global investment banks; median 73% deterioration in Sharpe ratios between backtested and live periods; the reduction for the most complex strategies exceeds that of the simplest by over 30 percentage points; risk-factor exposures reasonably robust in equity volatility and FX carry, weak in equity value | Crossref metadata; OpenAlex abstract | https://doi.org/10.3905/jpm.2017.43.2.090 | 2026-09-25 | abstract: "The authors report a median 73% deterioration in Sharpe ratios between backtested and live performance periods for the strategies" | hook; sections 1 and 4; strat:s2:quantitative-investment-strategies:rp; exercise 5; solutions; omsources |
| F2 | D. H. Bailey, M. Lopez de Prado, "The deflated Sharpe ratio: correcting for selection bias, backtest overfitting, and non-normality", Journal of Portfolio Management 40(5) (2014) 94-107 (as in Books 4 and 7) | Crossref record | https://doi.org/10.3905/jpm.2014.40.5.094 | 2026-09-25 | vol 40(5), pp 94-107 | section 4; solutions; omsources |
| F3 | R. D. McLean, J. Pontiff, "Does academic research destroy stock return predictability?", Journal of Finance 71(1) (2016) 5-32: 97 predictors; portfolio returns 26% lower out of sample and 58% lower post-publication (as in Book 7) | Crossref record with abstract | https://doi.org/10.1111/jofi.12365 | 2026-09-25 | "Portfolio returns are 26% lower out-of-sample and 58% lower post-publication" | section 4; solutions; omsources |

## EXCLUDED

- Live and backtest records of named banks' indices, index fees and swap spreads: not fetched; the fees (0.5%), rebalancing leakage (0.2%) and the distribution of true Sharpe ratios (mean 0.10, sd 0.15, calibrated so the median decay is near Suhonen et al.'s 73%) are the chapter's planted choices.
- Vatanen and Suhonen: not fetched; not cited.
- Named banks' QIS franchises: no citable primary source; no firm named.

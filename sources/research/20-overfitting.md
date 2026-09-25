# 20. Overfitting — brief and source ledger

## Brief

- **Hook.** A thousand parameter settings of a trend-following system are backtested on twenty years of data. The best has an in-sample Sharpe ratio of 1.8; over the next five years it earns nothing.
- **Sections.** Selection under many trials; The probability of backtest overfitting; Purged and embargoed cross-validation; Walk-forward analysis; Practical defences.
- **Defines.** backtest overfitting, in-sample, out-of-sample, walk-forward analysis, minimum backtest length, probability of backtest overfitting, combinatorially symmetric cross-validation, label overlap, purging, embargo, combinatorial purged cross-validation.
- **Uses (defined earlier).** deflated Sharpe ratio (B4.12), multiple testing (B4.12), data snooping (B4.12), cross-validation (B4.16), bootstrap (B4.13), Sharpe ratio (B4.11), trial count (ch1), holdout set (ch1), research log (ch1), vectorised backtest (ch16).
- **Tutorial.** Estimate the probability of backtest overfitting by CSCV for a thousand trend systems on noise and on data with a planted trend, and compare purged, embargoed and naive cross-validation scores for an overlapping-label model.
- **Build.** `firm.overfit`: CSCV and PBO, purged k-fold with embargo, combinatorial purged cross-validation paths, minimum backtest length, walk-forward splitter; Python.
- **Weekend problem.** One thousand trend systems — named result: the PBO of the search and the deflated out-of-sample expectation of the chosen system.
- **Facts to verify.** Bailey, Borwein, Lopez de Prado, Zhu 2017, the probability of backtest overfitting (J. Computational Finance); Bailey et al. 2014 minimum backtest length (Notices AMS); Lopez de Prado 2018, Advances in Financial Machine Learning (purging, embargo, CPCV); Harvey and Liu 2015, Backtesting (JPM) Sharpe haircut; Pardo 2008, The evaluation and optimization of trading strategies (walk-forward).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. H. Bailey, J. M. Borwein, M. Lopez de Prado, Q. J. Zhu, "The probability of backtest overfitting", J. Computational Finance (2016): standard techniques against regression overfitting such as hold-out are unreliable for investment backtests; a framework for the probability of backtest overfitting (PBO), estimated by combinatorially symmetric cross-validation (CSCV) | OpenAlex record with abstract; SSRN abstract 2326253 via Crossref | https://doi.org/10.21314/jcf.2016.322 | 2026-09-25 | "We propose a general framework to assess the probability of backtest overfitting (PBO)"; "we call these implementations combinatorially symmetric cross-validation (CSCV)" | section 2; def. PBO, CSCV; omsources |
| F2 | C. R. Harvey, Y. Liu, "Backtesting", J. Portfolio Management 42(1) (2015) 13-28: a statistical framework that accounts for multiple tests; a haircut for any reported Sharpe ratio and a profit hurdle | OpenAlex record with abstract; SSRN abstract 2345489 via Crossref | https://doi.org/10.3905/jpm.2015.42.1.013 | 2026-09-25 | "They propose a method to determine the appropriate haircut for any given reported Sharpe ratio" | section 3; pb 18; omsources |
| F3 | Purging removes from the training set all observations whose labels overlapped in time with the test labels; embargoing removes the training observations that immediately follow a test observation; combinatorial purged cross-validation uses k - p training folds and p > 1 test folds and recombines several test paths; after M. Lopez de Prado, Advances in Financial Machine Learning (2018) | skfolio source, CombinatorialPurgedCV docstring (reference [1] Lopez de Prado 2018) | https://github.com/skfolio/skfolio/blob/main/src/skfolio/model_selection/_combinatorial.py | 2026-09-25 | "Purging consists of removing from the training set all observations whose labels overlapped in time with those labels included in the testing set"; "Embargoing consists of removing from the training set all observations that immediately follow an observation in the testing set" | section 4; def. purging, embargo, CPCV; omsources |
| F4 | R. Arnott, C. R. Harvey, H. Markowitz (2019): as chapter 16, F2 | as chapter 16 | https://doi.org/10.3905/jfds.2019.1.064 | 2026-09-25 | as chapter 16 | section 6; omsources |

## EXCLUDED

- Bailey et al. (2014, Notices AMS) on the minimum backtest length: the article refused scripted access (chapter 1); the chapter derives its own bound (Proposition) and does not attribute the formula.
- Lopez de Prado (2018), the book itself, not accessed; the definitions rest on skfolio's documentation, which cites it.
- Pardo (2008) on walk-forward analysis: not fetched; not cited.
- All Sharpe ratios, PBOs, slopes, cross-validation scores and minimum backtest lengths are computed on synthetic data and tested.

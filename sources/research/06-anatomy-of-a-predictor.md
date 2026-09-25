# 6. Anatomy of a Predictor — brief and source ledger

## Brief

- **Hook.** Two researchers report the information coefficient of the same signal: 0.05 and 0.01. One used raw five-day returns and z-scores across the whole market; the other sector-neutral residual returns.
- **Sections.** The target; Normalisation; Neutralisation; The information coefficient and its standard error; The predictor card.
- **Defines.** predictor, prediction target, forecast horizon, residual return, cross-sectional z-score, rank transform, neutralisation, information coefficient, rank information coefficient, IC information ratio, quantile spread, predictor card.
- **Uses (defined earlier).** Spearman's rank correlation (B4.15), winsorisation (B4.15), HAC estimator (B4.11), standard error (B4.11), Fama--MacBeth regression (B4.16), factor model (B4.22), Sharpe ratio (B4.11), synthmkt (ch5).
- **Tutorial.** On firm.synthmkt, measure a planted signal's IC, rank IC and ICIR raw, normalised and neutralised, with the overlapping-target correction, and fill in its predictor card.
- **Build.** `firm.predictor`: normalisers, neutralisation by cross-sectional regression, IC engine (by date, pooled, rank, quantile spreads, Newey--West t-statistics for overlapping targets) and the PredictorCard record every later predictor fills; Python.
- **Weekend problem.** Two ICs for one signal — named result: the ratio of the naive to the HAC-corrected t-statistic of the IC for overlapping 20-day targets, and the IC lost or gained by neutralisation.
- **Facts to verify.** Grinold and Kahn 2000, Active Portfolio Management (2nd ed.); Qian, Hua, Sorensen 2007, Quantitative Equity Portfolio Management; Newey and West 1987 (Econometrica); Fama and MacBeth 1973 (JPE).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | N. Jegadeesh, "Evidence of predictable behavior of security returns", J. Finance 45(3) (1990) 881-898: negative first-order serial correlation in monthly stock returns, highly significant; positive at longer lags, strong at twelve months | Crossref abstract | https://doi.org/10.1111/j.1540-6261.1990.tb05110.x | 2026-09-24 | "The negative first-order serial correlation in monthly stock returns is highly significant" | pred card reversal; omsources |
| F2 | B. N. Lehmann, "Fads, martingales, and market efficiency", Quarterly J. Economics 105(1) (1990) 1-28 | Crossref record | https://doi.org/10.2307/2937816 | 2026-09-24 | bibliographic record only | pred card reversal; omsources |
| F3 | W. K. Newey and K. D. West, "A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix", Econometrica 55(3) (1987) 703-708 | Crossref record | https://doi.org/10.2307/1913610 | 2026-09-24 | vol 55(3), from p. 703 | prop. overlap; omsources |
| F4 | R. C. Grinold and R. N. Kahn, Active Portfolio Management, 2nd ed., McGraw-Hill, 2000 | publisher record (ISBN 978-0-07-024882-3) | https://www.mheducation.com/highered/product/active-portfolio-management-quantitative-approach-producing-superior-returns-controlling-risk-grinold-kahn/M9780070248823.html | 2026-09-24 | bibliographic record only | omsources |
| F5 | E. E. Qian, R. H. Hua, E. H. Sorensen, Quantitative Equity Portfolio Management, Chapman and Hall/CRC, 2007 | publisher record (ISBN 978-1-58488-558-1) | https://www.routledge.com/Quantitative-Equity-Portfolio-Management-Modern-Techniques-and-Applications/Qian-Hua-Sorensen/p/book/9781584885580 | 2026-09-24 | bibliographic record only | omsources |

## EXCLUDED

- Fama and MacBeth (1973), planned: the chapter does not use their regression; Book 4 ch. 16 owns it.
- All ICs, t-statistics, variance shares and the card's statistics are computed on firm.synthmkt and tested, not sourced.

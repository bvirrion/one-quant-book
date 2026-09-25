# 7. Price and Volume Features — brief and source ledger

## Brief

- **Hook.** A momentum signal built on the last twelve months of returns earns less than one that skips the most recent month: the last month reverses.
- **Sections.** Returns at many scales; Volatility and range; Volume and liquidity; Technical families as linear filters; Predictor cards.
- **Defines.** return feature, skip period, range-based volatility estimator, Parkinson estimator, Garman--Klass estimator, Yang--Zhang estimator, volume surprise, Amihud illiquidity, turnover ratio, moving-average crossover, linear filter.
- **Uses (defined earlier).** realised variance (B4.18), EWMA volatility (B4.18), half-life (B4.4), predictor (ch6), information coefficient (ch6), predictor card (ch6), bar (ch2), look-ahead bias (ch3).
- **Tutorial.** Compute the bar-feature family on firm.synthmkt, verify that no feature reads the future (a perturbation test), and draw the IC of each feature against horizon.
- **Build.** `firm.features`: vectorised, point-in-time-safe bar-feature library (returns at scales with skips, range estimators, volume surprise, Amihud, filters) with a leakage test that perturbs future data; Python.
- **Weekend problem.** The range-estimator race — named result: the variance efficiency of the Parkinson, Garman--Klass, Rogers--Satchell and Yang--Zhang estimators relative to close-to-close, with and without drift and opening jumps.
- **Facts to verify.** Parkinson 1980 (J. Business); Garman and Klass 1980 (J. Business); Rogers and Satchell 1991 (Annals of Applied Probability); Yang and Zhang 2000 (J. Business); Amihud 2002 (J. Financial Markets); Jegadeesh 1990 (JF); Jegadeesh and Titman 1993 (JF); De Bondt and Thaler 1985 (JF); Gervais, Kaniel, Mingelgrin 2001 high-volume return premium (JF); Brock, Lakonishok, LeBaron 1992 technical rules (JF).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Kenneth French data library momentum factor Mom: six value-weight portfolios formed on size and prior (2-12) returns | Kenneth R. French Data Library, "Momentum Factor (Mom)" description | https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html | 2026-09-24 | "We use six value-weight portfolios formed on size and prior (2-12) returns to construct Mom" | hook |
| F2 | N. Jegadeesh, J. Finance 45(3) (1990) 881-898: negative first-order serial correlation of monthly stock returns, highly significant | Crossref abstract (chapter 6 ledger F1) | https://doi.org/10.1111/j.1540-6261.1990.tb05110.x | 2026-09-24 | "The negative first-order serial correlation in monthly stock returns is highly significant" | hook; section 1; card |
| F3 | N. Jegadeesh and S. Titman, J. Finance 48(1) (1993) 65-91: buying past winners and selling past losers generates significant positive returns over 3- to 12-month holding periods | Crossref abstract | https://doi.org/10.1111/j.1540-6261.1993.tb04702.x | 2026-09-24 | "generate significant positive returns over 3- to 12-month holding periods" | section 1; card |
| F4 | W. F. M. De Bondt and R. Thaler, "Does the stock market overreact?", J. Finance 40(3) (1985) 793-805 | Crossref record | https://doi.org/10.1111/j.1540-6261.1985.tb05004.x | 2026-09-24 | bibliographic record only | section 1 |
| F5 | M. Parkinson, J. Business 53(1) (1980) 61-65; M. B. Garman and M. J. Klass, J. Business 53(1) (1980) 67-78; L. C. G. Rogers and S. E. Satchell, Annals of Applied Probability 1(4) (1991); D. Yang and Q. Zhang, J. Business 73(3) (2000) 477-492 | Crossref records | https://doi.org/10.1086/296071 | 2026-09-24 | bibliographic records; the formulas and the constant k = 0.34/(1.34 + (n+1)/(n-1)) are implemented and tested in firm.features (unbiasedness on simulated Brownian days) | section 2 |
| F6 | Y. Amihud, "Illiquidity and stock returns: cross-section and time-series effects", J. Financial Markets 5(1) (2002) 31-56 | Crossref record | https://doi.org/10.1016/s1386-4181(01)00024-6 | 2026-09-24 | bibliographic record; the measure is defined in the text | section 3 |
| F7 | S. Gervais, R. Kaniel, D. H. Mingelgrin, "The high-volume return premium", J. Finance 56(3) (2001) 877-919: stocks with unusually high volume over a day or a week tend to appreciate over the following month | Crossref abstract | https://doi.org/10.1111/0022-1082.00349 | 2026-09-24 | "stocks experiencing unusually high (low) trading volume over a day or a week tend to appreciate (depreciate) over the course of the following month" | section 3; card |
| F8 | W. Brock, J. Lakonishok, B. LeBaron, J. Finance 47(5) (1992) 1731-1764: moving-average and trading-range-break rules on the Dow Jones index 1897-1986; strong support for the technical strategies | Crossref abstract | https://doi.org/10.1111/j.1540-6261.1992.tb04681.x | 2026-09-24 | "utilizing the Dow Jones Index from 1897 to 1986"; "Overall, our results provide strong support for the technical strategies" | section 4 |

## EXCLUDED

- Claims about the size of the liquidity premium (Amihud) and of technical-rule profits after costs: not stated.
- All ICs, efficiencies and biases are computed and tested, not sourced.

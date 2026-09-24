# 8. Forward-Rate and Market Models — brief and source ledger

## Brief

- **Hook.** In 1997 three papers showed that the formula traders had used for caps for twenty years was the exact price in a consistent model of the whole curve.
- **Sections.** The Heath--Jarrow--Morton framework and its drift; The market model; Drifts under the spot and terminal measures; Calibrating to caps and swaptions: Rebonato's formula; Correlation and factor reduction.
- **Defines.** Heath--Jarrow--Morton framework, HJM drift condition, LIBOR market model, swap market model, spot measure, terminal measure, Rebonato's formula, forward-rate correlation.
- **Uses (defined earlier).** Girsanov theorem (B4.5), numeraire (B4.5), forward measure (B4.5), annuity measure (B4.5), Monte Carlo (B4.26), principal component analysis (B4.22), instantaneous forward rate (ch1), caplet volatility (ch4), swaption matrix (ch5), level factor (ch3).
- **Tutorial.** Simulate a lognormal market model under the spot measure with a predictor-corrector drift, check that caplets reprice, and compare Rebonato's approximation with Monte Carlo swaption prices.
- **Build.** `firm.lmm`: market-model Monte Carlo (spot and terminal measures), volatility and correlation parametrisations, swaption calibration.
- **Weekend problem.** The correlation you cannot see — named result: two correlation parametrisations that fit the same swaption matrix and the price gap they leave on a CMS spread option.
- **Facts to verify.** Heath, Jarrow, Morton 1992 Econometrica; Brace, Gatarek, Musiela 1997; Jamshidian 1997; Miltersen, Sandmann, Sondermann 1997; Rebonato 2002 (textbook).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Heath, Jarrow and Morton (Econometrica, January 1992) take the initial forward curve as given and restrict its stochastic dynamics by no arbitrage | D. Heath, R. Jarrow, A. Morton, "Bond pricing and the term structure of interest rates: a new methodology for contingent claims valuation", Econometrica 60(1), 77-105, 1992 | https://ideas.repec.org/a/ecm/emetrp/v60y1992i1p77-105.html | 2026-09-24 | abstract | def:rc:forward-rate-and-market-models:hjm, omsources |
| F2 | Brace, Gatarek and Musiela (1997): lognormal-type volatility in HJM, positive market forward rates; the basis of the LIBOR market model | A. Brace, D. Gatarek, M. Musiela, "The market model of interest rate dynamics", Mathematical Finance 7, 127-155, 1997 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1467-9965.00028 | 2026-09-24 | abstract | hook, def:rc:forward-rate-and-market-models:lmm, omsources |
| F3 | Jamshidian (1997): pricing and hedging of LIBOR and swap derivatives by arbitrage, with LIBOR and swap market models and their measures | F. Jamshidian, "LIBOR and swap market models and measures", Finance and Stochastics 1, 293-330, 1997 | https://link.springer.com/article/10.1007/s007800050026 | 2026-09-24 | abstract | hook, def:rc:forward-rate-and-market-models:smm, omsources |
| F4 | Miltersen, Sandmann and Sondermann (Journal of Finance, March 1997): closed-form caps and floors with lognormal interest rates | K. Miltersen, K. Sandmann, D. Sondermann, "Closed form solutions for term structure derivatives with log-normal interest rates", Journal of Finance 52(1), 409-430, 1997 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1997.tb03823.x | 2026-09-24 | abstract | hook, omsources |

## EXCLUDED

- Rebonato's textbook as the origin of the formula: cited in omsources as a book; no dated claim. Caplet volatilities (70 bp normal) and the abcd parameters are illustrative; forwards from chapter 2's illustrative euro curve. Re-checked 2026-09-24: no factual claim to restore.


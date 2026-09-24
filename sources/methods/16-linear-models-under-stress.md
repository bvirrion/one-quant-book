# 16. Linear Models under Stress — brief and source ledger

## Brief

- **Hook.** A factor model regresses a stock's returns on five factors, two of which move together with correlation 0.97; between two adjacent months the two betas flip sign and double in size while the fitted returns barely change.
- **Sections.** The geometry of least squares; Collinearity; Ridge, lasso and elastic net; Weighted and errors-in-variables regression; Cross-sectional regressions over time, and panels.
- **Defines.** ordinary least squares, hat matrix, multicollinearity, variance inflation factor, regularisation, ridge regression, lasso, elastic net, cross-validation, weighted least squares, generalised least squares, errors-in-variables, attenuation bias, total least squares, Fama--MacBeth regression, clustered standard errors, panel data, fixed effects.
- **Uses (defined earlier).** estimator, unbiased estimator, standard error, sandwich variance, HAC estimator, shrinkage estimator, tracking error.
- **Results (named theorems, not terms).** Gauss-Markov theorem; Frisch-Waugh-Lovell theorem; ridge as shrinkage along the singular directions; attenuation factor var(x)/(var(x)+var(noise)); Fama-MacBeth standard errors and their serial-correlation problem.
- **Tutorial.** Fit ridge, lasso and elastic net to predict a return from thirty correlated synthetic predictors with time-ordered cross-validation; plot the regularisation paths; then estimate a hedge ratio from a noisy regressor and watch it shrink.
- **Build.** `firm.linreg`: least squares with robust, clustered and HAC standard errors; ridge through the SVD; lasso and elastic net by coordinate descent; time-ordered cross-validation splitter with a purge gap; Fama-MacBeth; Python.
- **Weekend problem.** The hedge ratio that shrank — a bond hedged with a future using stale daily prices; named result: the attenuation factor of the least-squares hedge ratio, the corrected ratio, and the residual risk each leaves.
- **Facts to verify.** Legendre 1805 / Gauss 1809 least squares; Frisch and Waugh 1933 (Econometrica); Lovell 1963 (JASA); Hoerl and Kennard 1970 (Technometrics) ridge; Tibshirani 1996 (JRSS B) lasso; Zou and Hastie 2005 (JRSS B) elastic net; Friedman, Hastie and Tibshirani 2010 (J. Statistical Software) coordinate descent; Fama and MacBeth 1973 (Journal of Political Economy); Petersen 2009 (Review of Financial Studies) clustered standard errors.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Frisch and F. V. Waugh, "Partial time regressions as compared with individual trends", Econometrica 1(4) (1933), from p. 387 | Crossref record | https://doi.org/10.2307/1907330 | 2026-09-24 | vol 1(4), p 387 | thm FWL; omsources |
| F2 | M. C. Lovell, "Seasonal adjustment of economic time series and multiple regression analysis", JASA 58(304) (1963), 993-1010 | Crossref record | https://doi.org/10.1080/01621459.1963.10480682 | 2026-09-24 | vol 58(304), pp 993-1010 | thm FWL; omsources |
| F3 | A. E. Hoerl and R. W. Kennard, "Ridge regression: biased estimation for nonorthogonal problems", Technometrics 12(1) (1970), 55-67 | Crossref record | https://doi.org/10.1080/00401706.1970.10488634 | 2026-09-24 | vol 12(1), pp 55-67 | def ridge; omsources |
| F4 | R. Tibshirani, "Regression shrinkage and selection via the lasso", JRSS B 58(1) (1996), 267-288 | Crossref record | https://doi.org/10.1111/j.2517-6161.1996.tb02080.x | 2026-09-24 | vol 58(1), pp 267-288 | def lasso; omsources |
| F5 | H. Zou and T. Hastie, "Regularization and variable selection via the elastic net", JRSS B 67(2) (2005), 301-320 | Crossref record | https://doi.org/10.1111/j.1467-9868.2005.00503.x | 2026-09-24 | vol 67(2), pp 301-320 | def elastic net; omsources |
| F6 | J. Friedman, T. Hastie and R. Tibshirani, "Regularization paths for generalized linear models via coordinate descent", Journal of Statistical Software 33(1) (2010) | Crossref record | https://doi.org/10.18637/jss.v033.i01 | 2026-09-24 | vol 33(1), 2010 | section 3 (coordinate descent); omsources |
| F7 | E. F. Fama and J. D. MacBeth, "Risk, return, and equilibrium: empirical tests", Journal of Political Economy 81(3) (1973), 607-636 | Crossref record | https://doi.org/10.1086/260061 | 2026-09-24 | vol 81(3), pp 607-636 | def Fama-MacBeth; omsources |
| F8 | M. A. Petersen, "Estimating standard errors in finance panel data sets: comparing approaches", Review of Financial Studies 22(1) (2009), 435-480 | Crossref record (online 2008) | https://doi.org/10.1093/rfs/hhn053 | 2026-09-24 | vol 22(1), pp 435-480 | section 5; omsources |
| F9 | R. Roll, "A simple implicit measure of the effective bid-ask spread in an efficient market", Journal of Finance 39(4) (1984), 1127-1139 | Crossref record | https://doi.org/10.1111/j.1540-6261.1984.tb03897.x | 2026-09-24 | vol 39(4), pp 1127-1139 | section 4 (hedge correction); omsources |

## EXCLUDED

- Legendre 1805 / Gauss 1809 (planned): not cited by name.
- The factor model, the thirty predictors, the bond/future hedge (h 0.85, level error 0.14, 500 days) and the panel are simulations, not market facts.


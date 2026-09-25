# 14. Signal Combination — brief and source ledger

## Brief

- **Hook.** Forty signals each have an IC near 0.02. Their equal-weighted blend has 0.05; a regression-fitted blend has 0.08 in sample and 0.03 afterwards.
- **Sections.** The geometry of a linear blend; Weights from estimates; Regularised combination; Stacking; Orthogonalisation.
- **Defines.** signal combination, composite signal, equal-weight blend, IC-weighted blend, maximum-ICIR blend, stacking, orthogonalisation, symmetric orthogonalisation, forecast combination puzzle.
- **Uses (defined earlier).** ridge regression (B4.16), lasso (B4.16), cross-validation (B4.16), shrinkage estimator (B4.14), covariance matrix (B4.22), principal component analysis (B4.22), information coefficient (ch6), IC information ratio (ch6), predictor (ch6).
- **Tutorial.** Combine forty planted signals of firm.synthmkt by equal weights, IC weights, ridge and the maximum-ICIR rule; compare in-sample and out-of-sample IC and find the shrinkage that wins.
- **Build.** `firm.combine`: blenders (equal, IC-weighted, maximum-ICIR with shrinkage of the signal covariance, ridge and lasso on panels, stacking with time-ordered folds) and orthogonalisers (sequential, symmetric, residualise on a book); Python.
- **Weekend problem.** Forty weak signals — named result: the out-of-sample IC of the best blend against equal weights, and the shrinkage intensity that maximises it.
- **Facts to verify.** Timmermann 2006, Forecast combinations (Handbook of Economic Forecasting); Stock and Watson 2004 (J. Forecasting); Smith and Wallis 2009 forecast combination puzzle (OBES); Wolpert 1992 stacked generalisation (Neural Networks); Breiman 1996 stacked regressions (Machine Learning); Lowdin 1950 symmetric orthogonalisation (J. Chemical Physics); Klein and Chow 2013 orthogonalized factors (QREF).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. H. Stock, M. W. Watson, "Combination forecasts of output growth in a seven-country data set", J. Forecasting 23(6) (2004) 405-430: quarterly data 1959-1999, up to 73 predictors per country; individual forecasts unstable; the most successful combination forecasts, like the mean, are the least sensitive to the recent performance of the individual forecasts | Crossref record with abstract | https://doi.org/10.1002/for.928 | 2026-09-24 | "the most successful combination forecasts, like the mean, are the least sensitive to the recent performance of the individual forecasts" | hook; def. puzzle; card; iq 2; omsources |
| F2 | J. Smith, K. F. Wallis, "A simple explanation of the forecast combination puzzle", Oxford Bulletin of Economics and Statistics 71(3) (2009) 331-355: simple combinations repeatedly outperform sophisticated weighted combinations; the explanation lies in the finite-sample error in estimating the combining weights | Crossref record with abstract | https://doi.org/10.1111/j.1468-0084.2008.00541.x | 2026-09-24 | "simple combinations of point forecasts are repeatedly found to outperform sophisticated weighted combinations"; "The explanation lies in the effect of finite-sample error in estimating the combining weights" | section 3; def. puzzle; pb 12; iq 2; omsources |
| F3 | L. Breiman, "Stacked regressions", Machine Learning 24 (1996) 49-64: linear combinations of predictors with coefficients from cross-validation data and least squares under non-negativity constraints; the idea originated with Wolpert (1992) | the paper (Berkeley technical report 367, the published version's text), pdftotext | https://statistics.berkeley.edu/sites/default/files/tech-reports/367.pdf | 2026-09-24 | "The idea is to use cross-validation data and least squares under non-negativity constraints to determine the coefficients in the combination"; "The idea of stacking originated with Wolpert (1992)" | def. stacking; omsources |
| F4 | D. H. Wolpert, "Stacked generalization", Neural Networks 5(2) (1992) 241-259 | Crossref record; attribution via Breiman (F3) | https://doi.org/10.1016/s0893-6080(05)80023-1 | 2026-09-24 | bibliographic record; Breiman's credit | def. stacking; omsources |
| F5 | P.-O. Lowdin, "On the non-orthogonality problem connected with the use of atomic wave functions in the theory of molecules and crystals", J. Chemical Physics 18(3) (1950) 365-375: overlapping atomic orbitals replaced by orthonormalized functions | OpenAlex record with abstract; Crossref record | https://doi.org/10.1063/1.1747632 | 2026-09-24 | "The problem is simply solved by considering the orthonormalized functions ... as the real atomic orbitals" | def. symmetric orthogonalisation; omsources |

## EXCLUDED

- Timmermann (2006), Handbook of Economic Forecasting chapter: record found, no abstract; not cited.
- Klein and Chow (2013), orthogonalized factors: record found, no abstract; not cited.
- The two worlds, all ICs, shrinkage optima and orthogonalisation results are planted or computed and tested.

# 4. Linear and Regularised Baselines — brief and source ledger

## Brief

- **Hook.** A team spends a quarter on a deep model for the cross-section of returns; the model it must beat, a ridge regression on ranked characteristics fitted in a second, turns out to be within one standard error of it.
- **Sections.** The model to beat; Regularised regression on ranked features; Dimension reduction: principal-component and partial least squares; Classification baselines; Why the baseline often wins.
- **Defines.** baseline model, regularisation path, principal component regression, partial least squares, logistic regression, basis expansion.
- **Uses (defined earlier).** ordinary least squares (B4.16), ridge regression (B4.16), lasso (B4.16), elastic net (B4.16), regularisation (B4.16), principal component analysis (B4.22), rank transform (B7.6), cross-sectional z-score (B7.6), winsorisation (B4.15), Fama--MacBeth regression (B4.16), out-of-sample R-squared (ch1), hyperparameter search (ch3), purging (B7.20), embargo (B7.20), label overlap (B7.20), walk-forward analysis (B7.20), combinatorial purged cross-validation (B7.20), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** On a firm.synthmkt panel with forty ranked characteristics and a planted, mildly nonlinear alpha, fit OLS, ridge, lasso, elastic net, principal-component regression and partial least squares with purged cross-validation along their regularisation paths, and report out-of-sample R-squared, IC and a long-short Sharpe ratio; this is the harness every later chapter's model plugs into. Data: synthetic.
- **Build.** `firm.mlbase`: the model harness -- a fit/predict protocol, cross-sectional preprocessing (rank, winsorise, neutralise), pooled and per-date fits, regularisation paths, and the standard report (out-of-sample R-squared, IC with HAC t, long-short Sharpe ratio after firm.vecbt costs); Python on scikit-learn.
- **Weekend problem.** The model to beat -- named result: ridge's out-of-sample R-squared and IC against the best nonlinear model of the book, and the panel size at which the nonlinear model overtakes it.
- **Facts to verify.** Gu, Kelly and Xiu 2020 (RFS): OLS-3, elastic net, PCR and PLS results; Welch and Goyal 2008 a comprehensive look at the empirical performance of equity premium prediction (RFS); Kelly, Malamud and Zhou 2024 the virtue of complexity in return prediction (JF); Wold 1966 / de Jong 1993 partial least squares (SIMPLS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | S. Gu, B. Kelly, D. Xiu (2020): monthly out-of-sample stock-level R-squared OLS-3 0.16%, PLS 0.27%, PCR 0.26%, ENet 0.11%, NN3 0.40% (Table 1); equal-weighted long-short decile Sharpe ratio 2.45 for the best network (NN4), 1.35 value-weighted; the linear OLS-3 model 0.61 (value-weighted) and 0.83 (equal-weighted) | NBER WP 25398 PDF, Table 1 and section 3.4 | https://www.nber.org/system/files/working_papers/w25398/w25398.pdf | 2026-09-25 | "strategy earns an annualized out-of-sample Sharpe ratio of 1.35 (value-weighted) and 2.45 (equal-weighted)"; "model delivers Sharpe ratios of 0.61 and 0.83, respectively" | section 1; section 3; omsources |
| F2 | I. Welch, A. Goyal, "A comprehensive look at the empirical performance of equity premium prediction", RFS 21(4) 2008: suggested predictors of the equity premium predicted poorly in and out of sample | OpenAlex record with abstract | https://doi.org/10.1093/rfs/hhm014 | 2026-09-25 | "these models have predicted poorly both in-sample (IS) and out-of-sample (OOS) for 30 years now" | omsources |
| F3 | B. Kelly, S. Malamud, K. Zhou, "The virtue of complexity in return prediction", Journal of Finance 79(1) 2024 (NBER WP 30217): complex models with more parameters than observations can predict better than simple ones | Crossref record of the JF article; NBER abstract via OpenAlex | https://doi.org/10.1111/jofi.13298 ; https://doi.org/10.3386/w30217 | 2026-09-25 | "we theoretically prove that simple models severely understate return predictability compared to 'complex' models in which the number of parameters exceeds the number of observations" | section 5; build stretch; omsources |
| F4 | S. de Jong, "SIMPLS: an alternative approach to partial least squares regression", Chemometrics and Intelligent Laboratory Systems 18 (1993) | Crossref/OpenAlex record | https://doi.org/10.1016/0169-7439(93)85002-x | 2026-09-25 | title, journal and year as registered | def. PLS; omsources |
| F5 | A. E. Hoerl, R. W. Kennard, "Ridge regression: biased estimation for nonorthogonal problems", Technometrics 12(1) 1970 | Crossref/OpenAlex record | https://doi.org/10.1080/00401706.1970.10488634 | 2026-09-25 | title, journal and year as registered | omsources |

## EXCLUDED

- Every R-squared, IC, Sharpe ratio, turnover and chosen parameter is computed on firm.mlsynth (synthetic, with factor risk) and tested in code/ml/04-.../tests/test_solutions.py.
- The planted factor volatility (2% monthly) was chosen so that decile Sharpe ratios land near Gu, Kelly and Xiu's equal-weighted range (F1); without it the same models report 3.7-5.7.

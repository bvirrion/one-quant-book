# 14. Statistics — brief and source ledger

## Brief

- **Hook.** 'Explain a p-value to a trader.' The candidate says 'the probability that the strategy does not work.' The interviewer writes one word in the margin and asks the next question, which is the same question about a Sharpe ratio of 2 measured over nine months.
- **Sections.** Estimation: bias, variance and the standard error of what you report; Regression and its pathologies: collinearity, omitted variables, errors in variables and outliers; Testing: what a p-value is and is not, power, and many tests; The questions behind the question: turning a desk claim into a test.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** estimator (B4.11), unbiased estimator (B4.11), standard error (B4.11), Sharpe ratio (B4.11), maximum likelihood estimator (B4.11), bootstrap (B4.13), ordinary least squares (B4.16), multicollinearity (B4.16), attenuation bias (B4.16), ridge regression (B4.16), hypothesis test (B4.12), null hypothesis (B4.12), p-value (B4.12), power of a test (B4.12), multiple testing (B4.12), false discovery rate (B4.12), deflated Sharpe ratio (B4.12), sanity check (ch5).
- **Question bank.** 13 questions, 4/5/4. Families: the p-value and its misreadings; the standard error of a Sharpe ratio from a short track record (numeric); regression puzzles (regressing y on x and x on y, the slopes' product; adding a variable that flips a sign; noise in the regressor); the best of many backtests (expected maximum Sharpe under the null, numeric); power and sample size for a signal (numeric); correlation from two regressions; a bootstrap question on dependent data; 'is this coin fair?' with a stopping rule. Roles: researcher 7, trader 3, mle 2, risk 2. Firms: systematic fund 5, market maker 3, multi-manager fund 2, bank 1, any 3.
- **Facts to verify.** none external: all answers derived; method sources Lo 2002 (Financial Analysts Journal) for the Sharpe ratio's standard error and Bailey and Lopez de Prado 2014 (pointers to Book 4 ch. 11-12 ledgers); Wasserstein and Lazar 2016, the ASA statement on p-values.
- **Data.** Figures: none planned (one small table of the expected best Sharpe ratio by number of trials may appear). Code: iv_stats.py (closed forms checked by simulation over many seeds; regression puzzles with numpy on generated data; the expected maximum of k normals by numerical integration).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Lo, The statistics of Sharpe ratios, FAJ 58(4), 36-52, 2002: standard error of the Sharpe ratio for i.i.d. returns sqrt((1 + SR^2/2)/T) | Crossref (pointer: ledger interviews/02 F8) | https://api.crossref.org/works/10.2469/faj.v58.n4.2453 | 2026-09-29 | title, journal, volume, issue, pages | section 1; omsources |
| F2 | Wasserstein and Lazar, The ASA statement on p-values: context, process, and purpose, The American Statistician 70(2), 129-133, 2016 | Crossref | https://api.crossref.org/works/10.1080/00031305.2016.1154108 | 2026-09-29 | title, journal, volume, issue, pages | section 3; omsources |
| F3 | Lindley and Phillips, Inference for a Bernoulli process (a Bayesian view), The American Statistician 30(3), 112-119, 1976 | Crossref | https://api.crossref.org/works/10.1080/00031305.1976.10479154 | 2026-09-29 | title, journal, volume, issue, pages | section 3; omsources |

## EXCLUDED


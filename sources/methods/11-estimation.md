# 11. Estimation — brief and source ledger

## Brief

- **Hook.** A researcher estimates a strategy's mean daily return at 4 basis points with a standard error of 1.2, a t-statistic of 3.3; a colleague recomputes the standard error allowing for autocorrelation and changing volatility and gets 2.3, and the t-statistic falls to 1.7.
- **Sections.** Maximum likelihood; M-estimators and the method of moments; Asymptotics and the delta method; Sandwich variances.
- **Defines.** estimator, unbiased estimator, consistent estimator, standard error, likelihood function, maximum likelihood estimator, score function, Fisher information, Kullback--Leibler divergence, quasi-maximum likelihood, M-estimator, method of moments, generalised method of moments, delta method, sandwich variance, HAC estimator, Sharpe ratio.
- **Uses (defined earlier).** variance, information ratio, realised volatility, central limit theorem (result), martingale.
- **Results (named theorems, not terms).** consistency and asymptotic normality of the MLE (sketch); Cramér-Rao bound; the MLE of a misspecified model converges to the Kullback-Leibler projection; standard error of the Sharpe ratio under iid and serially correlated returns (Lo 2002); Newey-West estimator is positive semidefinite.
- **Tutorial.** Estimate the Sharpe ratio of a simulated daily strategy with autocorrelated, volatility-clustered returns; compare the iid standard error, Lo's formula, the Newey-West estimator and a Monte Carlo truth over many seeds.
- **Build.** `firm.estim`: estimation toolkit (generic maximum likelihood with numerical Hessian and outer-product-of-gradients, sandwich and Newey-West covariances with automatic bandwidth, delta-method helper, Sharpe ratio with HAC standard error); Python.
- **Weekend problem.** The t-statistic that halved — named result: the HAC t-statistic of the strategy whose naive t-statistic is 3.3, decomposed into the autocorrelation and the heteroskedasticity corrections.
- **Facts to verify.** Fisher 1922 (Phil. Trans. Royal Society A) foundations of theoretical statistics; Huber 1967 (Berkeley Symposium) behaviour of ML under nonstandard conditions; White 1980 and 1982 (Econometrica); Newey and West 1987 (Econometrica); Andrews 1991 (Econometrica) bandwidth; Hansen 1982 (Econometrica) GMM; Lo 2002 (Financial Analysts Journal) statistics of Sharpe ratios; Sharpe 1966 / 1994 (Journal of Portfolio Management) definition of the Sharpe ratio; Kullback and Leibler 1951.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | P. J. Huber, "The behavior of maximum likelihood estimates under nonstandard conditions", Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability, vol. 1 (1967), 221-233: ML consistency and asymptotic normality without assuming the true law is in the model | Project Euclid record | https://projecteuclid.org/ebooks/berkeley-symposium-on-mathematical-statistics-and-probability/Proceedings-of-the-Fifth-Berkeley-Symposium-on-Mathematical-Statistics-and/chapter/The-behavior-of-maximum-likelihood-estimates-under-nonstandard-conditions/bsmsp/1200512988 | 2026-09-24 | "it is not assumed that the true distribution underlying the observations belongs to the parametric family" | §2 (sandwich, Huber-White); omsources |
| F2 | H. White, "Maximum likelihood estimation of misspecified models", Econometrica 50(1) (1982), 1-25: the QMLE converges to a well-defined limit; standard tests invalid under misspecification | Econometric Society record | https://www.econometricsociety.org/publications/econometrica/1982/01/01/maximum-likelihood-estimation-misspecified-models | 2026-09-24 | Econometrica 50(1), 1-25 | §2 (KL projection, sandwich); omsources |
| F3 | W. K. Newey and K. D. West, "A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix", Econometrica 55(3) (1987), 703-708 | Econometric Society record; EconPapers | https://www.econometricsociety.org/publications/econometrica/1987/05/01/notes-and-comments-simple-positive-semi-definite | 2026-09-24 | "positive semi-definite by construction" | §5 (HAC); omsources |
| F4 | L. P. Hansen, "Large sample properties of generalized method of moments estimators", Econometrica 50(4) (1982), 1029-1054: GMM, efficient weight = inverse long-run variance of the moment conditions | Econometric Society record | https://www.econometricsociety.org/publications/econometrica/1982/07/01/large-sample-properties-generalized-method-moments-estimators | 2026-09-24 | Econometrica 50, 1029-1054 | §3 (GMM); omsources |
| F5 | A. W. Lo, "The statistics of Sharpe ratios", Financial Analysts Journal 58(4) (2002), 36-52: estimation error of Sharpe ratios under iid and serially correlated returns | CFA Institute research record | https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios | 2026-09-24 | FAJ 58(4), 36-52; monthly Sharpe ratios cannot be annualised by sqrt(12) under serial correlation | §4 (Sharpe ratio se); omsources |
| F6 | G. Casella and R. L. Berger, Statistical Inference, 2nd ed., Duxbury, 2002 (ISBN 0-534-24312-6) | Cengage product page | https://www.cengage.com/c/statistical-inference-2e-casella-berger/9780534243128/ | 2026-09-24 | 2nd edition, ISBN 9780534243128 | §1 (MLE asymptotics, Cramér-Rao); omsources |
| F7 | D. W. K. Andrews, "Heteroskedasticity and autocorrelation consistent covariance matrix estimation" (automatic bandwidth selection), Cowles Foundation Discussion Paper 877, published Econometrica 59 (1991) | Cowles Foundation PDF | https://cowles.yale.edu/sites/default/files/2022-08/d0877.pdf | 2026-09-24 | title and author on the discussion paper | build Stretch field |

## EXCLUDED

- Fisher 1922, White 1980, Sharpe 1966/1994, Kullback-Leibler 1951 (planned): not cited by name in the text.
- The strategy parameters (mean 4 bp, sd 42 bp, 5-day holding) are illustrative, not market facts.


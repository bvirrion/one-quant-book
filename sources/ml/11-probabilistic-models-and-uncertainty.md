# 11. Probabilistic Models and Uncertainty — brief and source ledger

## Brief

- **Hook.** Two forecasts both say a stock will rise 5 basis points; one is sure of it and one is guessing. A book that sizes both trades the same has thrown away half of what the models know.
- **Sections.** Predictive distributions and proper scoring rules; Quantile and distributional losses; Two kinds of uncertainty; Conformal prediction; Using uncertainty in sizing.
- **Defines.** predictive distribution, proper scoring rule, pinball loss, quantile regression, continuous ranked probability score, mixture density network, aleatoric uncertainty, epistemic uncertainty, conformal prediction.
- **Uses (defined earlier).** maximum likelihood estimator (B4.11), QLIKE loss (B4.18), coverage probability (B4.13), exchangeability (B4.13), posterior predictive distribution (B4.14), Kelly criterion (B2.29), fractional Kelly (B2.29), forecast calibration (B7.15), calibration curve (B7.15), deep ensemble (ch7), gradient boosting (ch5), multilayer perceptron (ch7), Adam (ch7), early stopping (ch5), stochastic gradient descent (B4.24), reverse mode (B4.28), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** On firm.tape features with a heteroskedastic target, fit LightGBM quantile models, a Gaussian and a mixture-density network, and a deep ensemble; score them with the pinball loss and the CRPS; wrap them in split and adaptive conformal intervals and measure coverage under drift; size trades by mean over variance and compare with sizing by the mean alone. Data: synthetic.
- **Build.** `firm.uncert`: quantile and distributional heads, pinball loss and CRPS, calibration of intervals, split and adaptive conformal prediction, ensemble decomposition of uncertainty, and a sizing rule from the predictive distribution; Python.
- **Weekend problem.** Sizing by doubt -- named result: the Sharpe ratio gain of variance-scaled sizing over sizing by the mean alone, and conformal coverage against its nominal 90 % after a planted regime change.
- **Facts to verify.** Koenker and Bassett 1978 regression quantiles (Econometrica); Gneiting and Raftery 2007 strictly proper scoring rules (JASA); Bishop 1994 mixture density networks (Aston tech. report); Vovk, Gammerman and Shafer 2005 Algorithmic Learning in a Random World; Gibbs and Candes 2021 adaptive conformal inference under distribution shift (NeurIPS); Kendall and Gal 2017 what uncertainties do we need? (NeurIPS); Angelopoulos and Bates 2023 conformal prediction: a gentle introduction (FnT ML).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | T. Gneiting, A. E. Raftery, "Strictly proper scoring rules, prediction, and estimation", JASA 102(477) 2007 (propriety; CRPS and its quantile-integral form) | Crossref/OpenAlex record | https://doi.org/10.1198/016214506000001437 | 2026-09-25 | title, journal and year as registered | def. proper scoring rule, CRPS; exo 8; omsources |
| F2 | R. Koenker, G. Bassett, "Regression quantiles", Econometrica 46(1) 1978 | Crossref/OpenAlex record | https://doi.org/10.2307/1913643 | 2026-09-25 | title, journal and year as registered | def. quantile regression; omsources |
| F3 | C. M. Bishop, "Mixture density networks", Aston University technical report NCRG/94/004 (1994): networks outputting the parameters of a conditional mixture to model the full conditional distribution | Aston Publications Explorer record with abstract | https://publications.aston.ac.uk/id/eprint/373/ | 2026-09-25 | "For problems involving the prediction of continuous variables, however, the conditional averages provide only a very limited description of the properties of the target variables" | def. mixture density network; omsources |
| F4 | V. Vovk, A. Gammerman, G. Shafer, Algorithmic Learning in a Random World, Springer (2005; 2nd ed. 2022) | Crossref record (2nd ed.) | https://doi.org/10.1007/978-3-031-06649-8 | 2026-09-25 | title as registered (2022 edition) | def. conformal prediction; omsources |
| F5 | I. Gibbs, E. Candes, "Adaptive conformal inference under distribution shift", NeurIPS 2021 (arXiv 2106.00170): prediction sets online when the data-generating distribution varies over time | arXiv abstract | https://arxiv.org/abs/2106.00170 | 2026-09-25 | "We develop methods for forming prediction sets in an online setting where the data generating distribution is allowed to vary over time in an unknown fashion" | def. conformal prediction (adaptive); omsources |
| F6 | A. Kendall, Y. Gal, "What uncertainties do we need in Bayesian deep learning for computer vision?", NeurIPS 2017 (arXiv 1703.04977): aleatoric uncertainty is noise inherent in the observations; epistemic uncertainty can be explained away given enough data | arXiv abstract | https://arxiv.org/abs/1703.04977 | 2026-09-25 | "Aleatoric uncertainty captures noise inherent in the observations. On the other hand, epistemic uncertainty accounts for uncertainty in the model -- uncertainty which can be explained away given enough data" | def. aleatoric and epistemic uncertainty; omsources |

## EXCLUDED

- Every score, coverage and Sharpe ratio is computed on firm.mlsynth.series (synthetic, with a planted volatility regime) and tested in code/ml/11-.../tests/test_solutions.py. The hook's 80 and 250 basis points are an illustration, reused in exercise 3.
- Angelopoulos and Bates (2023), planned, not cited.

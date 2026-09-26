# 2. Targets, Labels and Sample Weights — brief and source ledger

## Brief

- **Hook.** A classifier trained on whether a stock is up after ten days scores well, and a trader asks what it does when the stock hits its stop-loss on day three: the label the model learned is not the trade the desk will do.
- **Sections.** Fixed-horizon labels and their flaws; Barrier labels and meta-labelling; Overlap, concurrency and uniqueness; Sample weights and the sequential bootstrap.
- **Defines.** fixed-horizon label, triple-barrier label, meta-labelling, label concurrency, average uniqueness, sequential bootstrap, sample weight, time-decay weight.
- **Uses (defined earlier).** label overlap (B7.20), bar (B7.2), dollar bar (B7.2), volume bar (B7.2), residual return (B7.6), bootstrap (B4.13), effective sample size (B4.14), supervised learning (ch1), training set (ch1), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** On firm.tape sessions sampled into volume bars, build fixed-horizon and triple-barrier labels with volatility-scaled barriers, measure label concurrency and average uniqueness, and compare bagged trees trained with plain, uniqueness-weighted and sequential-bootstrap sampling on purged folds; meta-label a simple primary signal. Data: synthetic (firm.tape seeds).
- **Build.** `firm.labeling`: fixed-horizon and triple-barrier labels with event times, meta-labels, concurrency and average uniqueness, sample weights (uniqueness, return attribution, time decay), the sequential bootstrap; Python.
- **Weekend problem.** Five hundred overlapping days -- named result: the effective number of observations against the nominal one, and the out-of-sample gain of uniqueness weighting over plain bagging, with its spread over seeds.
- **Facts to verify.** Lopez de Prado 2018 ch. 3-4 labelling, uniqueness and the sequential bootstrap; Breiman 1996 bagging predictors (Machine Learning); Joubert 2022 meta-labeling: theory and framework (JFDS) or equivalent published source on meta-labelling.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. Lopez de Prado, Advances in Financial Machine Learning, Wiley 2018 (chapters 3-4: triple-barrier labels, meta-labelling, concurrency and average uniqueness, the sequential bootstrap) | book review in Quantitative Finance (OpenAlex); the book itself not accessed | https://doi.org/10.1080/14697688.2019.1703030 | 2026-09-25 | review of the book as registered; the methods are stated in the chapter as definitions and derived or computed here | def. triple-barrier label, meta-labelling, uniqueness, sequential bootstrap; omsources |
| F2 | J. F. Joubert, "Meta-labeling: theory and framework", Journal of Financial Data Science 4(3) 2022: meta-labelling is an ML layer on top of a primary strategy to size positions and filter false positives | OpenAlex record with abstract | https://doi.org/10.3905/jfds.2022.1.098 | 2026-09-25 | "Meta-labeling is a machine learning (ML) layer that sits on top of a base primary strategy to help size positions, filter out false-positive signals, and improve metrics such as the Sharpe ratio and maximum drawdown" | def. meta-labelling; omsources |
| F3 | L. Breiman, "Bagging predictors", Machine Learning 24 (1996) | Crossref/OpenAlex record | https://doi.org/10.1007/bf00058655 | 2026-09-25 | title, author, journal and year as registered | section 4; omsources |

## EXCLUDED

- Every share, uniqueness, t-statistic, AUC and per-trade figure is computed on firm.mlsynth.series (synthetic) and tested in code/ml/02-.../tests/test_solutions.py.
- The planned "volume bars on firm.tape" data were replaced by daily bars of firm.mlsynth.series: ten years of 20 assets gives the overlap structure in a second, where tape sessions would take minutes.

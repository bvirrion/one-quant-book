# 3. Validation — brief and source ledger

## Brief

- **Hook.** A research team's model scores an information coefficient of 0.08 in cross-validation and 0.01 in its first month live. The post-mortem finds three leaks, none of them in the model: a normalisation fitted on the whole sample, a fundamental joined by period end, and folds that shared overlapping labels.
- **Sections.** What validation estimates; Splits that respect time; Choosing hyperparameters without fooling yourself; Leakage hunting.
- **Defines.** model selection, hyperparameter search, nested cross-validation, target leakage, train--test contamination, adversarial validation, leakage audit.
- **Uses (defined earlier).** look-ahead bias (B7.3), point-in-time data (B7.3), as-of join (B7.3), survivorship bias (B7.3), probability of backtest overfitting (B7.20), trial count (B7.1), deflated Sharpe ratio (B4.12), multiple testing (B4.12), hyperparameter (ch1), validation set (ch1), generalisation error (ch1), purging (B7.20), embargo (B7.20), label overlap (B7.20), walk-forward analysis (B7.20), combinatorial purged cross-validation (B7.20), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Wrap firm.overfit's purged k-fold, CPCV and walk-forward splits as scikit-learn splitters; plant five leaks in a firm.synthmkt pipeline (full-sample scaling, period-end fundamental join, overlapping labels in shuffled folds, a target-encoded feature, a survivor-only universe), measure the out-of-sample R-squared each one fakes, and catch each with a detector; compare flat and nested hyperparameter search. Data: synthetic.
- **Build.** `firm.cvsplit`: scikit-learn-compatible PurgedKFold, CPCVSplit and WalkForwardSplit on label spans (built on firm.overfit), nested cross-validation, and leak detectors (adversarial validation, shifted-target canary, full-sample-statistic scan, fold-overlap check); Python.
- **Weekend problem.** Five leaks -- named result: the out-of-sample R-squared each leak fakes on a target of pure noise, and which detector catches it.
- **Facts to verify.** Varma and Simon 2006 bias in error estimation when using cross-validation for model selection (BMC Bioinformatics); Cawley and Talbot 2010 on over-fitting in model selection (JMLR); Kaufman, Rosset, Perlich and Stitelman 2012 leakage in data mining (ACM TKDD); Bergstra and Bengio 2012 random search for hyper-parameter optimization (JMLR); scikit-learn TimeSeriesSplit documentation; Arnott, Harvey and Markowitz 2019 a backtesting protocol in the era of machine learning (JFDS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | S. Varma, R. Simon, "Bias in error estimation when using cross-validation for model selection", BMC Bioinformatics 7 (2006) 91: the CV error estimate of the classifier chosen by minimising CV error is biased | OpenAlex record with abstract | https://doi.org/10.1186/1471-2105-7-91 | 2026-09-25 | "We have evaluated the validity of using the CV error estimate of the optimized classifier as an estimate of the true error expected on independent data" | section 3; omsources |
| F2 | G. C. Cawley, N. L. C. Talbot, "On over-fitting in model selection and subsequent selection bias in performance evaluation", JMLR 11 (2010) | JMLR page with abstract | https://jmlr.org/papers/v11/cawley10a.html | 2026-09-25 | "Model selection strategies for machine learning algorithms typically involve the numerical optimisation of an appropriate model selection criterion, often based on an estimator of generalisation performance, such as k-fold cross-validation" | section 3; omsources |
| F3 | S. Kaufman, S. Rosset, C. Perlich, O. Stitelman, "Leakage in data mining: formulation, detection, and avoidance", ACM TKDD 6(4) 2012: leakage called one of the top ten data mining mistakes | OpenAlex record with abstract | https://doi.org/10.1145/2382577.2382579 | 2026-09-25 | "Deemed 'one of the top ten data mining mistakes', leakage is the introduction of information about the data mining target that should not be legitimately available to mine from" | section 4; omsources |
| F4 | J. Bergstra, Y. Bengio, "Random search for hyper-parameter optimization", JMLR 13 (2012): randomly chosen trials are more efficient than grid trials | JMLR page with abstract | https://jmlr.org/papers/v13/bergstra12a.html | 2026-09-25 | "This paper shows empirically and theoretically that randomly chosen trials are more efficient for hyper-parameter optimization than trials on a grid" | def. hyperparameter search; omsources |

## EXCLUDED

- Every R-squared, count, AUC and detector statistic is computed on firm.mlsynth (synthetic, ceiling zero) and tested in code/ml/03-validation/tests/test_solutions.py; the hook is the chapter's own period-end join.
- Arnott, Harvey and Markowitz (2019) and the scikit-learn TimeSeriesSplit documentation were planned; not cited (Book 7 ch. 20 covers the protocol; the chapter uses its own splitters).

# 5. Trees and Boosting — brief and source ledger

## Brief

- **Hook.** The most common model in a quantitative researcher's notebook is a gradient-boosted ensemble of shallow trees; its most common failure is a tuning search that picks, out of two hundred configurations, the one that fitted the validation noise best.
- **Sections.** Trees; Bagging and random forests; Gradient boosting; Regularisation, early stopping and monotonic constraints; Tuning under noise.
- **Defines.** decision tree, bagging, random forest, out-of-bag error, gradient boosting, learning rate, early stopping, monotonic constraint.
- **Uses (defined earlier).** regularisation (B4.16), Huber loss (B4.15), baseline model (ch4), hyperparameter search (ch3), nested cross-validation (ch3), sample weight (ch2), probability of backtest overfitting (B7.20), purging (B7.20), embargo (B7.20), label overlap (B7.20), walk-forward analysis (B7.20), combinatorial purged cross-validation (B7.20), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Fit scikit-learn trees and forests and LightGBM (deterministic mode) to firm.tape order-book features and to the Chapter 4 panel; compare with firm.intraml's NumPy boosting; add monotonic constraints where the sign is known; run a 200-configuration random search and measure how much of the best configuration's validation score is noise by re-scoring it on fresh seeds. Data: synthetic.
- **Build.** `firm.gbdt`: LightGBM wrapper with purged early stopping, monotonic constraints from a feature specification, deterministic settings, seed ensembles, plateau selection instead of argmax, and export of the fitted trees to JSON for Chapter 26's compiler; Python.
- **Weekend problem.** Tuning in the fog -- named result: the standard deviation of the cross-validation score across seeds against the score gain from tuning, and the share of the 200 configurations indistinguishable from the defaults.
- **Facts to verify.** Breiman 2001 random forests (Machine Learning); Friedman 2001 greedy function approximation: a gradient boosting machine (Annals of Statistics); Ke et al. 2017 LightGBM (NeurIPS); Chen and Guestrin 2016 XGBoost (KDD); Grinsztajn, Oyallon and Varoquaux 2022 why do tree-based models still outperform deep learning on tabular data? (NeurIPS); LightGBM documentation: deterministic, monotone_constraints.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | L. Breiman, "Random forests", Machine Learning 45 (2001) | Crossref/OpenAlex record | https://doi.org/10.1023/a:1010933404324 | 2026-09-25 | title, author, journal and year as registered | def. random forest; omsources |
| F2 | J. H. Friedman, "Greedy function approximation: a gradient boosting machine", Annals of Statistics 29(5) 2001: boosting as steepest descent in function space | OpenAlex record with abstract | https://doi.org/10.1214/aos/1013203451 | 2026-09-25 | "A connection is made between stagewise additive expansions and steepest-descent minimization. A general gradient descent 'boosting' paradigm is developed for additive expansions based on any fitting criterion" | def. gradient boosting; prop.; omsources |
| F3 | G. Ke et al., "LightGBM: a highly efficient gradient boosting decision tree", NeurIPS 30 (2017) | NeurIPS proceedings page (title) | https://papers.nips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html | 2026-09-25 | page title "LightGBM: A Highly Efficient Gradient Boosting Decision Tree" | section 3; omsources |
| F4 | LightGBM parameters: monotone_constraints (1 increasing, -1 decreasing, 0 none, all features in order); deterministic=true ensures stable results with the same data and parameters on CPU | LightGBM documentation, Parameters | https://lightgbm.readthedocs.io/en/latest/Parameters.html | 2026-09-25 | "used for constraints of monotonic features 1 means increasing, -1 means decreasing, 0 means non-constraint"; "setting this to true should ensure the stable results when using the same data and the same parameters" | def. monotonic constraint; build |
| F5 | T. Chen, C. Guestrin, "XGBoost: a scalable tree boosting system", KDD 2016 | OpenAlex record | https://doi.org/10.1145/2939672.2939785 | 2026-09-25 | "Tree boosting is a highly effective and widely used machine learning method" | omsources |
| F6 | L. Grinsztajn, E. Oyallon, G. Varoquaux, "Why do tree-based models still outperform deep learning on typical tabular data?", NeurIPS Datasets and Benchmarks 2022 | Crossref record | https://doi.org/10.52202/068431-0037 | 2026-09-25 | title and authors as registered | omsources |

## EXCLUDED

- Every R-squared, tree count, seed spread and violation share is computed on firm.mlsynth (synthetic, with factor risk) or firm.tape and tested in code/ml/05-.../tests/test_solutions.py. The tree schematic's leaf values are illustrative and labelled so.
- The brief's 200-configuration search was cut to 20 configurations to keep the chapter's tests under a minute on a shared machine.

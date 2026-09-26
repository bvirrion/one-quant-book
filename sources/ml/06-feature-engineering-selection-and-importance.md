# 6. Feature Engineering, Selection and Importance — brief and source ledger

## Brief

- **Hook.** Two features in a model are the same order-book imbalance measured at two depths; the impurity importance ranks both at the bottom, the permutation importance calls both useless, and deleting either changes nothing -- deleting both halves the model's IC.
- **Sections.** Transformations that respect the data; Feature selection and stability selection; Importance: impurity, permutation, Shapley; Substitution and clustered importance; When importance lies.
- **Defines.** feature engineering, feature selection, stability selection, mean decrease in impurity, permutation importance, Shapley value, SHAP value, substitution effect, clustered feature importance.
- **Uses (defined earlier).** fractional differencing (B4.17), winsorisation (B4.15), rank transform (B7.6), return feature (B7.7), lasso (B4.16), false discovery rate (B4.12), permutation test (B4.13), decision tree (ch5), gradient boosting (ch5), random forest (ch5), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Plant features with known roles (true, correlated twin, noise, leaky) in a firm.mlsynth task and in firm.tape features; rank them by impurity, permutation, drop-column and SHAP importance (LightGBM's pred_contrib), with and without clustering the twins; run stability selection with the lasso and with boosting and measure its false-selection rate. Data: synthetic.
- **Build.** `firm.featimp`: stationary transforms, impurity, permutation (single and clustered) and drop-column importances under purged folds, TreeSHAP attributions through LightGBM, correlation clustering of features, stability selection with a false-selection bound; Python.
- **Weekend problem.** Which feature mattered? -- named result: the rank of the true features under each importance method, and the false-selection rate of stability selection at a threshold of 0.6.
- **Facts to verify.** Breiman 2001 permutation importance; Strobl, Boulesteix, Zeileis and Hothorn 2007 bias in random forest variable importance (BMC Bioinformatics); Lundberg and Lee 2017 a unified approach to interpreting model predictions (NeurIPS); Lundberg et al. 2020 from local explanations to global understanding (Nature Machine Intelligence); Meinshausen and Buhlmann 2010 stability selection (JRSS B); Lopez de Prado 2020 Machine Learning for Asset Managers (clustered importance); Shapley 1953.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | N. Meinshausen, P. Buhlmann, "Stability selection", JRSS B 72(4) 2010: subsampling combined with selection algorithms, with finite-sample control of false selections (the bound q^2/((2 pi_thr - 1) p) under exchangeability) | OpenAlex record with abstract | https://doi.org/10.1111/j.1467-9868.2010.00740.x | 2026-09-25 | "We introduce stability selection. It is based on subsampling in combination with (high dimensional) selection algorithms" | def. stability selection; thm.; omsources |
| F2 | S. Lundberg, S.-I. Lee, "A unified approach to interpreting model predictions", NeurIPS 2017 (SHAP) | arXiv abstract | https://arxiv.org/abs/1705.07874 | 2026-09-25 | "Understanding why a model makes a certain prediction can be as crucial as the prediction's accuracy" | def. SHAP value; omsources |
| F3 | S. Lundberg et al., "From local explanations to global understanding with explainable AI for trees", Nature Machine Intelligence 2 (2020) (TreeSHAP) | Crossref/OpenAlex record | https://doi.org/10.1038/s42256-019-0138-9 | 2026-09-25 | title and journal as registered | def. SHAP value (TreeSHAP); omsources |
| F4 | C. Strobl, A.-L. Boulesteix, A. Zeileis, T. Hothorn, "Bias in random forest variable importance measures", BMC Bioinformatics 8 (2007) 25 | OpenAlex record with abstract | https://doi.org/10.1186/1471-2105-8-25 | 2026-09-25 | "Variable importance measures for random forests have been receiving increased attention as a means of variable selection" | section 3; omsources |
| F5 | M. Lopez de Prado, Machine Learning for Asset Managers, Cambridge University Press 2020 (clustered feature importance) | OpenAlex record with abstract | https://doi.org/10.1017/9781108883658 | 2026-09-25 | "Successful investment strategies are specific implementations of general theories" | def. clustered feature importance; omsources |
| F6 | L. S. Shapley, "A value for n-person games", Contributions to the Theory of Games II (1953) 307-317 | Crossref record | https://doi.org/10.1515/9781400881970-018 | 2026-09-25 | title, author and year as registered | def. Shapley value; omsources |

## EXCLUDED

- Every importance, rank, frequency and R-squared is computed on a synthetic task with planted roles and tested in code/ml/06-.../tests/test_solutions.py. The hook's two copies are that task's x1 and x1b, not an order-book feature (the brief's order-book framing was dropped: the planted task shows substitution exactly).

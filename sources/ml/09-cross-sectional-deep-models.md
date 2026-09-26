# 9. Cross-Sectional Deep Models — brief and source ledger

## Brief

- **Hook.** A statistical factor model extracts five factors from a thousand stocks' returns and says nothing about a stock listed yesterday; a model whose betas are functions of the stock's characteristics prices it on its first day.
- **Sections.** Panels, pooling and permutation invariance; Embeddings for identifiers and categories; Learned factor models: instrumented PCA and conditional autoencoders; Evaluating a learned factor model.
- **Defines.** entity embedding, pooled panel model, permutation-invariant network, instrumented principal component analysis, autoencoder, conditional autoencoder.
- **Uses (defined earlier).** factor model (B4.22), statistical factor model (B7.24), factor exposure (B7.24), style factor (B7.24), principal component analysis (B4.22), panel data (B4.16), residual return (B7.6), multilayer perceptron (ch7), Adam (ch7), early stopping (ch5), stochastic gradient descent (B4.24), reverse mode (B4.28), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Give firm.synthmkt names betas that are nonlinear functions of their characteristics (planted, with a controlled share of variance); fit PCA, instrumented PCA and a conditional autoencoder with K = 1 to 5 factors on training years; report total and predictive R-squared out of sample; add industry embeddings. Data: synthetic.
- **Build.** `firm.xsnet`: pooled panel datasets with per-date batching, entity embeddings, instrumented PCA by alternating least squares, a conditional autoencoder in PyTorch, and total and predictive R-squared; Python.
- **Weekend problem.** Factors that learn -- named result: out-of-sample total and predictive R-squared of PCA, IPCA and the conditional autoencoder at three factors, and the share of the planted nonlinearity each recovers.
- **Facts to verify.** Kelly, Pruitt and Su 2019 characteristics are covariances: IPCA (JFE); Gu, Kelly and Xiu 2021 autoencoder asset pricing models (J. Econometrics); Guo and Berkhahn 2016 entity embeddings of categorical variables (arXiv); Chen, Pelger and Zhu 2024 deep learning in asset pricing (Management Science); Zaheer et al. 2017 deep sets (NeurIPS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | B. Kelly, S. Pruitt, Y. Su, "Characteristics are covariances: a unified model of risk and return", JFE 134(3) 2019: IPCA allows latent factors and time-varying loadings by introducing observable characteristics that instrument for the unobservable dynamic loadings | OpenAlex records (JFE; NBER WP 24540 with abstract) | https://doi.org/10.1016/j.jfineco.2019.05.001 ; https://doi.org/10.3386/w24540 | 2026-09-25 | "Our method, Instrumented Principal Components Analysis (IPCA), allows for latent factors and time-varying loadings by introducing observable characteristics that instrument for the unobservable dynamic loadings" | def. IPCA; omsources |
| F2 | S. Gu, B. Kelly, D. Xiu, "Autoencoder asset pricing models", Journal of Econometrics 222(1) 2021 | Crossref/OpenAlex record | https://doi.org/10.1016/j.jeconom.2020.07.009 | 2026-09-25 | title, journal, volume 222, issue 1, 2021 as registered in Crossref | def. conditional autoencoder; omsources |
| F3 | L. Chen, M. Pelger, J. Zhu, "Deep learning in asset pricing", Management Science (2024): deep networks estimate an asset pricing model using the no-arbitrage condition as criterion | OpenAlex record with abstract | https://doi.org/10.1287/mnsc.2023.4695 | 2026-09-25 | "The key innovations are to use the fundamental no-arbitrage condition as criterion function"; Crossref: volume 70, issue 2, 2024 | build stretch; omsources |
| F4 | C. Guo, F. Berkhahn, "Entity embeddings of categorical variables", arXiv 1604.06737 (2016) | arXiv record (title) | https://arxiv.org/abs/1604.06737 | 2026-09-25 | title as registered | def. entity embedding; omsources |
| F5 | M. Zaheer et al., "Deep sets", NeurIPS 2017: models for tasks defined on sets, invariant to permutations | arXiv abstract | https://arxiv.org/abs/1703.06114 | 2026-09-25 | "we consider objective functions defined on sets that are invariant to permutations" | def. permutation-invariant network; omsources |

## EXCLUDED

- Every R-squared and correlation is computed on firm.mlsynth.factor_panel (synthetic) and tested in code/ml/09-.../tests/test_solutions.py.

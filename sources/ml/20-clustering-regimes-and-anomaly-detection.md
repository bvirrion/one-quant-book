# 20. Clustering, Regimes and Anomaly Detection — brief and source ledger

## Brief

- **Hook.** A risk dashboard shows the market in a ``calm'' regime on the Friday before a crash; the regime model was right about Friday and could not have been right about Monday, and the question is what it was for.
- **Sections.** Clustering assets and days; Regime models; Filtering against smoothing: what a regime model knows in real time; Anomaly detection; Surveillance detectors.
- **Defines.** clustering, k-means, hierarchical clustering, hidden Markov model, regime-switching model, Viterbi algorithm, anomaly detection, isolation forest, precision--recall curve.
- **Uses (defined earlier).** Markov chain (B4.8), expectation--maximisation algorithm (B4.19), Kalman smoother (B4.19), hierarchical risk parity (B7.26), volatility regime adjustment (B7.24), industry factor (B7.24), spoofing (B9.29), layering (B9.29), marking the close (B9.29), look-ahead bias (B7.3), autoencoder (ch9), unsupervised learning (ch1).
- **Tutorial.** Cluster firm.synthmkt names by return correlation and recover the planted industries; fit a two- and three-state hidden Markov model to index returns with planted regimes, and compare filtered with smoothed probabilities and a volatility threshold as trading signals; score an isolation forest and an autoencoder against Book 9's firm.surveil detectors on account-days with planted episodes and legitimate look-alikes. Data: synthetic.
- **Build.** `firm.regimes`: correlation clustering (k-means and hierarchical, with a stability score), a Gaussian hidden Markov model by EM with forward filtering and Viterbi decoding, regime-conditioned statistics computed on filtered probabilities only, isolation-forest and reconstruction-error anomaly scores, and TPR at fixed FPR through firm.surveil; Python on scikit-learn.
- **Weekend problem.** Which regime are we in? -- named result: the filtered regime's accuracy and detection delay against the smoothed one, and the anomaly detectors' precision at a fixed false-positive rate against the rule-based detectors.
- **Facts to verify.** Hamilton 1989 a new approach to the economic analysis of nonstationary time series (Econometrica); Ang and Timmermann 2012 regime changes and financial markets (Annual Review of Financial Economics); Rabiner 1989 a tutorial on hidden Markov models (Proc. IEEE); Liu, Ting and Zhou 2008 isolation forest (ICDM); Lloyd 1982 least squares quantization in PCM (k-means); Mantegna 1999 hierarchical structure in financial markets (EPJ B); Davis and Goadrich 2006 the relationship between precision-recall and ROC curves (ICML).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. D. Hamilton, "A new approach to the economic analysis of nonstationary time series and the business cycle", Econometrica 57(2) 1989 (Markov-switching model) | Crossref/OpenAlex record | https://doi.org/10.2307/1912559 | 2026-09-26 | title, venue and year as registered | def. regime-switching model; omsources |
| F2 | A. Ang, A. Timmermann, "Regime changes and financial markets", Annual Review of Financial Economics 4 2012 | Crossref/OpenAlex record | https://doi.org/10.1146/annurev-financial-110311-101808 | 2026-09-26 | title, venue and year as registered | def. regime-switching model; omsources |
| F3 | L. R. Rabiner, "A tutorial on hidden Markov models and selected applications in speech recognition", Proceedings of the IEEE 77(2) 1989 | Crossref/OpenAlex record | https://doi.org/10.1109/5.18626 | 2026-09-26 | title, venue and year as registered | def. hidden Markov model; omsources |
| F4 | F. T. Liu, K. M. Ting, Z.-H. Zhou, "Isolation forest", IEEE ICDM 2008 | Crossref/OpenAlex record | https://doi.org/10.1109/ICDM.2008.17 | 2026-09-26 | title, venue and year as registered | def. isolation forest; omsources |
| F5 | S. P. Lloyd, "Least squares quantization in PCM", IEEE Transactions on Information Theory 28(2) 1982 (k-means; the registry lists the first name incorrectly) | Crossref/OpenAlex record | https://doi.org/10.1109/TIT.1982.1056489 | 2026-09-26 | title, venue and year as registered | def. k-means; omsources |
| F6 | R. N. Mantegna, "Hierarchical structure in financial markets", European Physical Journal B 11 1999 (correlation distance) | Crossref/OpenAlex record | https://doi.org/10.1007/s100510050929 | 2026-09-26 | title, venue and year as registered | def. hierarchical clustering; omsources |
| F7 | J. Davis, M. Goadrich, "The relationship between precision-recall and ROC curves", ICML 2006 | Crossref/OpenAlex record | https://doi.org/10.1145/1143844.1143874 | 2026-09-26 | title, venue and year as registered | def. precision-recall curve; omsources |

## EXCLUDED

- Every clustering index, regime estimate, delay, Sharpe ratio and detector score is computed on firm.synthmkt names, a planted two-state regime series and Book 9's firm.surveil account-days, tested in code/ml/20-clustering-regimes-and-anomaly-detection/tests/test_solutions.py. The hook's Friday and Monday are an illustration of the measured filtered and smoothed probabilities.

# 24. Data and Feature Stores — brief and source ledger

## Brief

- **Hook.** A model's live IC is half its backtest's; the cause is a thirty-second volume feature computed from the end of each second in research and from the arrival of each message in production.
- **Sections.** The same feature twice: offline and online; Point-in-time correctness in the store; Freshness and materialisation; Testing for skew.
- **Defines.** feature store, offline store, online store, feature definition, materialisation, feature freshness, training--serving skew.
- **Uses (defined earlier).** point-in-time data (B7.3), as-of join (B7.3), knowledge time (B7.3), valid time (B7.3), bitemporal data (B7.3), data snapshot (B7.29), order-flow imbalance (B7.8), microprice (B7.8), look-ahead bias (B7.3), target leakage (ch3), prediction target (B7.6), forecast horizon (B7.6), information coefficient (B7.6), in-sample (B7.20), out-of-sample (B7.20), cross-validation (B4.16).
- **Tutorial.** Declare a dozen order-book features once, compute them offline over firm.tape history and online through Book 7's streaming firm.lobfeat engine, and prove equality at every decision time; inject three kinds of skew (window alignment, rounding, a late-arriving input) and catch each with a parity test; measure what one-event misalignment costs the Chapter 8 model. Data: synthetic.
- **Build.** `firm.featstore`: feature definitions as data (inputs, window, clock, version), an offline store on firm.pit with point-in-time retrieval, an online store fed by a streaming engine, materialisation jobs, freshness checks and a parity test between the two; Python.
- **Weekend problem.** Same features twice -- named result: the IC and P&L lost to a one-event window misalignment, and the parity test's detection rate for each planted skew.
- **Facts to verify.** Sculley et al. 2015 hidden technical debt in machine learning systems (NeurIPS); Hermann and Del Balso 2017 meet Michelangelo: Uber's machine learning platform (Uber engineering blog); Feast open-source feature store documentation (point-in-time joins); Polyzotis, Roy, Whang and Zinkevich 2018 data lifecycle challenges in production machine learning (SIGMOD Record); Breck et al. 2019 data validation for machine learning (MLSys).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. Sculley et al., "Hidden technical debt in machine learning systems", NeurIPS 28 2015: ML-specific risk factors include boundary erosion, entanglement, hidden feedback loops, undeclared consumers, data dependencies, configuration issues, changes in the external world | NeurIPS proceedings page | https://papers.nips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html | 2026-09-26 | abstract: "boundary erosion, entanglement, hidden feedback loops, undeclared consumers, data dependencies, configuration issues, changes in the external world" | def. feature store; omsources |
| F2 | J. Hermann, M. Del Balso, "Meet Michelangelo: Uber's machine learning platform", Uber engineering blog, 5 September 2017: a centralised Feature Store; the same DSL expressions applied at training and prediction time | Uber engineering blog | https://www.uber.com/blog/michelangelo-machine-learning-platform/ | 2026-09-26 | "the same expressions are applied at training time and at prediction time to help guarantee that the same final set of features is generated" | def. feature store; omsources |
| F3 | N. Polyzotis, S. Roy, S. E. Whang, M. Zinkevich, "Data lifecycle challenges in production machine learning: a survey", SIGMOD Record 47(2) 2018 | Crossref/OpenAlex record | https://doi.org/10.1145/3299887.3299891 | 2026-09-26 | title, journal, year as registered | omsources |

## EXCLUDED

- Every mismatch share, detection rate, IC and P&L is computed on firm.tape sessions through firm.lobfeat and firm.featstore, tested in code/ml/24-data-and-feature-stores/tests/test_solutions.py. The hook's model is the chapter's own.
- Breck et al. 2019 (data validation for machine learning, MLSys): no registry record retrieved; not cited.
- Feast documentation (point-in-time joins): not cited; the point-in-time join is Book 7 chapter 3's and the chapter's own code.
- The brief's "measure what one-event misalignment costs the chapter 8 model": measured on a ridge forecast of the one-second and five-second mid change on the chapter's twelve features instead, so that the store's features and the model share one pipeline.

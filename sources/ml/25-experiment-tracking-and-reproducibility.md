# 25. Experiment Tracking and Reproducibility — brief and source ledger

## Brief

- **Hook.** A regulator asks a firm to show the model that traded on a given morning, the data it was trained on and every alternative it was chosen over; the firm can name the model, and it takes three weeks to retrain something close to it.
- **Sections.** What must be recorded; Versioning data, code and models; The registry and the audit trail; Reproducing a model, and when bitwise is too much.
- **Defines.** experiment tracker, run record, data versioning, model artefact, model registry, model lineage, audit trail.
- **Uses (defined earlier).** content-addressed storage (B7.29), data snapshot (B7.29), environment lock (B7.29), pipeline stage (B7.29), reproducible result (B7.29), research log (B7.1), trial count (B7.1), deflated Sharpe ratio (B4.12), bitwise reproducibility (B4.25), training checkpoint (ch23), hyperparameter search (ch3).
- **Tutorial.** Track two hundred Chapter 5 tuning runs (parameters, metrics, data and code hashes, seeds, environment) in a file-backed tracker; register the champion with its lineage and reproduce it bitwise from the registry alone; delete one field at a time and see which absence breaks reproduction; take the trial count from the tracker into the deflated Sharpe ratio. Data: synthetic.
- **Build.** `firm.exptrack`: a file-backed experiment tracker (runs, parameters, metrics, artefacts by content hash), a model registry with stages and lineage to data snapshots and code, reproduction from a registry entry, and an append-only audit trail; Python on firm.workflow and firm.researchlog.
- **Weekend problem.** Reproduce the March model -- named result: the number of runs behind the champion and its deflated Sharpe ratio, and the field whose absence made reproduction fail.
- **Facts to verify.** Zaharia et al. 2018 accelerating the machine learning lifecycle with MLflow (IEEE Data Engineering Bulletin); DVC documentation (data versioning); Pineau et al. 2021 improving reproducibility in machine learning research (JMLR); Commission Delegated Regulation (EU) 2017/589 (RTS 6) record-keeping for algorithmic trading (dated); SEC Rule 17a-4 electronic recordkeeping (dated); Gundersen and Kjensmo 2018 state of the art: reproducibility in AI (AAAI).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Commission Delegated Regulation (EU) 2017/589 of 19 July 2016 (RTS 6): Article 5(7) records of any material change to algorithmic trading software (when, who made it, who approved it, its nature); Article 28 records kept five years | EUR-Lex | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0589 | 2026-09-26 | Art. 5(7): "shall keep records of any material change made to the software used for algorithmic trading, allowing it to determine: (a) when a change was made; (b) the person that has made the change; (c) the person that has approved the change; (d) the nature of the change"; Art. 28: "kept for five years" | dat:ml:experiment-tracking-and-reproducibility:rts6; omsources |
| F2 | J. Pineau et al., "Improving reproducibility in machine learning research (a report from the NeurIPS 2019 reproducibility program)", arXiv:2003.12206 2020 | arXiv API | https://arxiv.org/abs/2003.12206 | 2026-09-26 | title and abstract | omsources |
| F3 | O. E. Gundersen, S. Kjensmo, "State of the art: reproducibility in artificial intelligence", AAAI 2018 | Crossref/OpenAlex record | https://doi.org/10.1609/aaai.v32i1.11503 | 2026-09-26 | title, venue, year as registered | omsources |

## EXCLUDED

- Every Sharpe ratio, deflated Sharpe ratio and reproduction result is the chapter's own study on a synthetic panel, tested in code/ml/25-experiment-tracking-and-reproducibility/tests/test_solutions.py. The hook's regulator request and three weeks are an illustration.
- Zaharia et al. 2018 (MLflow, IEEE Data Engineering Bulletin): no registry record retrieved; not cited.
- DVC documentation and SEC Rule 17a-4 (planned dated fact): not cited; the dated box uses the EU's RTS 6, verified on EUR-Lex.

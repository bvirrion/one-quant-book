# 28. The Machine-Learning Team — brief and source ledger

## Brief

- **Hook.** A model that took a researcher three weeks took the firm five months to trade; nothing in it was hard, and every handoff between the people who built it was a queue.
- **Sections.** Roles: researcher, engineer, platform; How work moves: the handoff; What the platform owns; Measuring the pipeline.
- **Defines.** machine-learning engineer, machine-learning platform, model owner, handoff specification.
- **Uses (defined earlier).** research review (B7.1), stage gate (B7.1), kill criterion (B7.1), M/M/1 queue (B4.8), model validation (B6.26), three lines of defence (B6.26), model registry (ch25), model card (ch21), model monitoring (ch27), feature store (ch24), model artefact (ch25).
- **Tutorial.** Validate a model handoff package (artefact, feature specification, test vectors, latency budget, monitoring specification, model card) against a schema in continuous integration; simulate a research-to-production pipeline as a network of queues with rework and measure lead time and where models die. Data: synthetic.
- **Build.** `firm.modelpkg`: the handoff specification as a schema, a validator that runs the package's test vectors against firm.mlinfer and its feature specification against firm.featstore, and a pipeline simulator on Book 4's queueing tools; Python.
- **Weekend problem.** Who owns the model? -- named result: the pipeline's median lead time and the share of models lost at each gate, and the lead-time saving from removing one handoff.
- **Facts to verify.** Amershi et al. 2019 software engineering for machine learning: a case study (ICSE-SEIP); Zinkevich 2017 rules of machine learning (Google, public); Sculley et al. 2015; public descriptions of machine-learning roles and team structure by trading firms (firm blogs or talks; each with a source, else unnamed); Kreuzberger, Kuhl and Hirschl 2023 machine learning operations (MLOps): overview (IEEE Access).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | S. Amershi, A. Begel, C. Bird, R. DeLine, H. Gall, E. Kamar, N. Nagappan, B. Nushi, T. Zimmermann, "Software engineering for machine learning: a case study", ICSE-SEIP 2019: study of software teams at Microsoft; model customisation and reuse require skills different from those typically found in software teams; AI components are more difficult to handle as distinct modules | OpenAlex record (abstract) | https://doi.org/10.1109/icse-seip.2019.00042 | 2026-09-26 | abstract: "model customization and model reuse require very different skills than are typically found in software teams"; "AI components are more difficult to handle as distinct modules than traditional software components" | sec. roles; omsources |
| F2 | D. Kreuzberger, N. Kühl, S. Hirschl, "Machine learning operations (MLOps): overview, definition, and architecture", IEEE Access 2023: mixed-method research (literature review, tool review, expert interviews); roles R1-R7: business stakeholder, solution architect, data scientist, data engineer, software engineer, DevOps engineer, ML engineer/MLOps engineer (combines several roles) | OpenAlex record; arXiv:2205.02302 full text, sec. 4.3 Roles | https://doi.org/10.1109/access.2023.3262138 | 2026-09-26 | abstract: "a literature review, a tool review, and expert interviews"; sec. 4.3 lists R1 to R7 as named; R7 "combines aspects of several roles" | def. machine-learning engineer; sec. roles; omsources |
| F3 | M. Zinkevich, "Rules of Machine Learning: Best Practices for ML Engineering", Google for Developers: Rule #4 "Keep the first model simple and get the infrastructure right"; Rule #32 "Re-use code between your training pipeline and your serving pipeline whenever possible" | Google for Developers page | https://developers.google.com/machine-learning/guides/rules-of-ml | 2026-09-26 | page text, rules #4 and #32 verbatim | sec. handoff; sec. platform; omsources |
| F4 | J. D. C. Little, "A proof for the queuing formula L = lambda W", Operations Research 9(3) 1961 | OpenAlex/Crossref record | https://doi.org/10.1287/opre.9.3.383 | 2026-09-26 | title, journal, year; abstract defines L, lambda, W | sec. measuring the pipeline; omsources |
| F5 | D. Sculley et al., "Hidden technical debt in machine learning systems", NeurIPS 28 2015: risk factors include undeclared consumers and data dependencies | NeurIPS proceedings page | https://papers.nips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html | 2026-09-26 | abstract: "undeclared consumers, data dependencies" (same source as ch. 24 F1) | sec. platform; omsources |

## EXCLUDED

- Public descriptions of machine-learning roles and team structure by named trading firms: not used; the chapter names no firm, and its roles come from Kreuzberger et al. (F2) and the series' own components.
- Hook (three weeks of research, five months to trade): an illustrative scenario reproduced by the chapter's simulated pipeline (median 20.4 weeks), not a reported case.
- Pipeline parameters (arrival rate, team sizes, service times, kill and rework probabilities): chosen for illustration, not measured at any firm; the text says so by presenting them as the chapter's pipeline.

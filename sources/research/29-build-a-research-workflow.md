# 29. Build: a Research Workflow — brief and source ledger

## Brief

- **Hook.** A result from eighteen months ago cannot be reproduced: the vendor revised its history, the code moved on, and nobody kept the random seed.
- **Sections.** Reproducibility; Review; Build: the pipeline from raw data to a reviewed result.
- **Defines.** reproducible result, data snapshot, content-addressed storage, pipeline stage, environment lock, review checklist.
- **Uses (defined earlier).** bitwise reproducibility (B4.25), research log (ch1), trial count (ch1), point-in-time data (ch3), predictor card (ch6), fidelity level (ch16), research review (ch1).
- **Tutorial.** Run the book's reference study end to end through firm.workflow (synthmkt snapshot, point-in-time store, universe, features, cards, blend, forecast, portfolio, level-1 and level-2 backtests, tear sheet, log entry), change one input and watch which stages recompute.
- **Build.** `firm.workflow`: pipeline runner over a DAG of cached, content-hashed stages with a manifest (inputs, code hashes, seeds, environment), bit-for-bit reproduction check, and registration of each run in firm.researchlog; Python.
- **Weekend problem.** The result that could not be reproduced — named result: the stages invalidated by a vendor revision, and the manifest diff that proves the reproduction.
- **Facts to verify.** Peng 2011, Reproducible research in computational science (Science); Sandve, Nekrutenko, Taylor, Hovig 2013, ten simple rules for reproducible computational research (PLoS Computational Biology); Git object model (content-addressed storage) documentation; Arnott, Harvey, Markowitz 2019 (JFDS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. D. Peng, "Reproducible Research in Computational Science", Science 334(6060) (2011) 1226-1227: reproducibility as a minimum standard for judging scientific claims when full independent replication is not possible | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.1126/science.1213847 | 2026-09-25 | "Reproducibility has the potential to serve as a minimum standard for judging scientific claims when full independent replication of a study is not possible" | section 1; def. reproducible result; omsources |
| F2 | G. K. Sandve, A. Nekrutenko, J. Taylor, E. Hovig, "Ten Simple Rules for Reproducible Computational Research", PLoS Computational Biology 9(10) (2013) e1003285: rule 1 for every result keep track of how it was produced; 2 avoid manual data manipulation; 3 archive the exact versions of external programs; 4 version-control all custom scripts; 5 record all intermediate results; 6 for analyses with randomness note the random seeds; 7 store raw data behind plots; 8 hierarchical analysis output; 9 connect textual statements to underlying results; 10 provide public access to scripts, runs and results | PLoS article page (open access), rule headings | https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285 | 2026-09-25 | "Rule 1: For Every Result, Keep Track of How It Was Produced"; "Rule 6: For Analyses That Include Randomness, Note Underlying Random Seeds"; "Rule 9: Connect Textual Statements to Underlying Results" | section 1; review checklist; exo 4; iq 2; omsources |
| F3 | Git is a content-addressable filesystem: at its core a key-value data store that returns a key for any content inserted; the key is the SHA-1 hash of the content plus a header | Pro Git book, 2nd edition, section 10.2 Git Internals - Git Objects | https://git-scm.com/book/en/v2/Git-Internals-Git-Objects | 2026-09-25 | "Git is a content-addressable filesystem"; "at the core of Git is a simple key-value data store"; "This is the SHA-1 hash - a checksum of the content you're storing plus a header" | section 1; def. content-addressed storage; omsources |
| F4 | R. Arnott, C. R. Harvey, H. Markowitz (2019): as chapter 16, F2 | as chapter 16 | https://doi.org/10.3905/jfds.2019.1.064 | 2026-09-25 | as chapter 16 | section 2; omsources |

## EXCLUDED

- Practices of named firms' research platforms: no public source fetched; none is named.
- The pipeline, its scenarios and the reference study are the book's own; every number is computed and tested.


# 29. The Asset Manager's Strategies — brief and source ledger

## Brief

- **Hook.** An index fund charging three basis points tracks its benchmark to within one basis point a year; its manager's craft is invisible when it works.
- **Sections.** Indexing: replication and sampling; Factor products; Benchmark-relative management; Transition management.
- **Defines.** full replication, sampled replication, factor product, transition management.
- **Uses (defined earlier).** tracking error (B1.3), information ratio (B1.3), index fund (ch10), implementation shortfall (B7.19).
- **Tutorial.** Replicate a cap-weighted index of firm.synthmkt fully and by sampling with a risk-model optimiser, measure tracking error and costs, build a factor product, and plan a portfolio transition that minimises shortfall.
- **Build.** `firm.assetmgr`: index replication (full and sampled via firm.portcons), tracking-error budgeting, factor-product construction and a transition planner; Python.
- **Weekend problem.** Invisible craft — named result: the tracking error of sampled replication against the number of names held, and the transition's shortfall.
- **Facts to verify.** Frino and Gallagher 2001 tracking S&P 500 index funds (J. Portfolio Management); SEC Form N-1A tracking disclosures (dated); Grinold and Kahn 2000 Active Portfolio Management (McGraw-Hill).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. Frino, D. R. Gallagher, "Tracking S&P 500 index funds", Journal of Portfolio Management 28(1) (2001) 44-55: the index is a paper portfolio and duplicating it without cost is not achievable; tracking error in index fund performance is unavoidable because of market frictions; the extent and variation of tracking error over time for S&P 500 index mutual funds; S&P 500 index funds on average outperformed active funds after expenses over the sample period | Crossref metadata; OpenAlex abstract | https://doi.org/10.3905/jpm.2001.319822 | 2026-09-25 | abstract: "tracking error in index fund performance is unavoidable because of market frictions"; "S&P 500 index funds, on average, outperformed active funds after expenses over the sample period" | hook; section 1; strat:s1:the-asset-managers-strategies:index; omsources |
| F2 | A. Frino, D. R. Gallagher, T. N. Oetomo, "The index tracking strategies of passive and enhanced index equity funds", Australian Journal of Management 30(1) (2005) 23-55: passive funds benefit from less rigid rebalancing; around index revisions enhanced index funds rebalance earlier and more patiently, with higher returns and lower trading costs; when passive funds deviate from the benchmark they tend to overweight more liquid, larger and better-performing stocks | Crossref metadata; OpenAlex abstract | https://doi.org/10.1177/031289620503000103 | 2026-09-25 | abstract: "passive funds benefit from employing less rigid rebalancing and investment strategies"; "enhanced index funds commence portfolio rebalancing earlier than index funds, and employ more patient trading strategies" | section 1; section 4; strat:s1:the-asset-managers-strategies:enhanced; omsources |
| F3 | R. C. Grinold and R. N. Kahn, Active Portfolio Management, 2nd ed., McGraw-Hill, 2000 (as Book 7 chapter 6 F4) | publisher record (ISBN 978-0-07-024882-3) | https://www.mheducation.com/highered/product/active-portfolio-management-quantitative-approach-producing-superior-returns-controlling-risk-grinold-kahn/M9780070248823.html | 2026-09-24 | bibliographic record only | section 3; omsources |

## EXCLUDED

- SEC Form N-1A tracking disclosures (brief, dated): not fetched; the chapter makes no statement about disclosure rules, and has no dated box.
- The hook's "three basis points ... within one basis point a year": no source for a specific fund; rewritten around Frino and Gallagher.
- Named index providers, fund managers and fees: none.
- The truth-based risk model, the fund size, costs and impact parameters are the chapter's own choices.

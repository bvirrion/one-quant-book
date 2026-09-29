# 30. Choosing — brief and source ledger

## Brief

- **Hook.** Four offers -- a bank quant role, a market maker's trading role, an analyst seat at a platform and a technology firm's engineering job -- differ in expected pay, in its spread, in hours, in city and in what the next five years teach. No single number ranks them; a person's weights do, and the useful question is how far those weights can move before the choice changes.
- **Sections.** The attributes that differ across firm types; Pay risk as a certainty equivalent; Temperament, skills and the work itself; A multi-attribute framework and its sensitivity; Revisiting the decision.
- **Defines.** multi-attribute value model, swing weighting, dominated alternative, rank acceptability.
- **Uses (defined earlier).** certainty equivalent (B4.9), relative risk aversion (B4.9), utility function (B4.9), Kelly criterion (B2.29), decision journal (B16.26), outcome bias (B16.26), pre-mortem (B16.26), total compensation (ch13), disposable pay after housing (ch27), coverage requirement (ch26).
- **Tutorial.** Compare four offers with firm.careerdec: attribute values from the earlier chapters' tools (firm.payoffer certainty equivalents, firm.locations disposable pay, firm.workload hours, firm.careerpath five-year value), swing weights, dominance screening, and rank acceptability under weights sampled uniformly on the simplex (stochastic multicriteria acceptability analysis). End state: a rank-acceptability chart and the weight regions where each offer wins.
- **Build.** `firm.careerdec`: attribute scaling, a multi-attribute value model, swing weighting, dominance screening, rank-acceptability indices by weight sampling, and a report of the weights that flip the choice; Python; wraps firm.payoffer, firm.aftertax, firm.locations, firm.workload and firm.careerpath.
- **Weekend problem.** Four offers -- named result: each offer's first-rank acceptability index under uniform weights, and the smallest change in the weight on pay risk that changes the preferred offer.
- **Facts to verify.** Keeney and Raiffa (1976), Decisions with Multiple Objectives; von Winterfeldt and Edwards (1986) on swing weights; Lahdelma, Hokkanen and Salminen (1998), SMAA, European Journal of Operational Research; pointer Book 4 ch. 9 and Book 16 ch. 26.
- **Data.** Outputs of the earlier chapters' tools; labelled illustrative attribute inputs.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Keeney, R. L. and H. Raiffa, Decisions with Multiple Objectives: Preferences and Value Tradeoffs (Wiley, 1976; Cambridge University Press reissue, 1993) | Crossref record of the Cambridge reissue | https://doi.org/10.1017/cbo9781139174084 | 2026-09-29 | title, publisher, date | definition (multi-attribute value model); omsources |
| F2 | von Winterfeldt, D. and W. Edwards, Decision Analysis and Behavioral Research (Cambridge University Press, 1986), 604 pp. | Crossref record of a review in Psychometrika (1989) | https://doi.org/10.1007/bf02294530 | 2026-09-29 | title, publisher, year, pages | definition (swing weighting); omsources |
| F3 | Lahdelma, R., J. Hokkanen and P. Salminen (1998), 'SMAA - Stochastic multiobjective acceptability analysis', European Journal of Operational Research 106(1), 137-143 | Crossref | https://api.crossref.org/works/10.1016/S0377-2217(97)00163-X | 2026-09-29 | title, journal, volume, issue, pages, authors | definition (rank acceptability); method |

## EXCLUDED

- Survey evidence on what quants value in a job (hours, pay, learning): none found from a public, documented source; the chapter's weights and judgements are the reader's, and its values illustrative.

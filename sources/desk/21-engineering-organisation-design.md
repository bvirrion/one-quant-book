# 21. Engineering Organisation Design — brief and source ledger

## Brief

- **Hook.** In 1968 a programmer observed that organisations design systems that copy their own communication structure. A trading firm that splits its engineers by asset class ends up with three order gateways, three risk checks and three on-call rotas, whether or not it wanted them.
- **Sections.** Embedded against central teams; The quant developer and other hybrid roles; Ownership: every service has an owner; On-call and its cost; Measuring an engineering organisation.
- **Defines.** embedded team, central team, quant developer, service owner, bus factor, coordination cost.
- **Uses (defined earlier).** model owner (B12.28), machine-learning engineer (B12.28), handoff specification (B12.28), canary deployment (B7.21), on-call rotation (B15.28), blameless review (B15.28), service-level objective (B15.28), platform team (ch19), product team (ch19).
- **Tutorial.** Twenty services with a dependency graph and incident rates: assign them to teams in an embedded and a central design; compute cross-team dependency edges, on-call pages per engineer per week and each design's bus factor; then move one engineer and see what breaks. End state: a table of the three measures for each design, and a drawing of the ownership graph.
- **Build.** `firm.teamtopo`: services, dependencies, change frequencies and incident rates as data, team assignments, coordination cost (cross-team edges weighted by change frequency), on-call load, bus factor (the smallest set of people whose loss orphans a service), and a comparison report; Python, graph code by hand (no new library).
- **Weekend problem.** Three order gateways -- named result: coordination cost and pages per engineer per week under the embedded and the central design, and the bus factor of each.
- **Facts to verify.** Conway 1968, How do committees invent? (Datamation); MacCormack, Rusnak and Baldwin 2012 (Research Policy): the mirroring hypothesis; Skelton and Pais 2019, Team Topologies; Beyer et al. 2016, Site Reliability Engineering: on-call load (pointer to Book 15 ch. 28); Forsgren, Humble and Kim 2018, Accelerate (delivery metrics).
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | M. E. Conway, "How Do Committees Invent?", Datamation, April 1968: the basic thesis is that organisations which design systems are constrained to produce designs which are copies of the communication structures of these organisations; a design effort should be organised according to the need for communication | Author's reprint | https://www.melconway.com/Home/Committees_Paper.html | 2026-09-28 | "organizations which design systems (in the broad sense used here) are constrained to produce designs which are copies of the communication structures of these organizations"; "a design effort should be organized according to the need for communication"; "Datamation magazine, where it appeared April, 1968" | hook; section 1 |
| F2 | A. MacCormack, C. Baldwin and J. Rusnak, "Exploring the duality between product and organizational architectures: A test of the 'mirroring' hypothesis", Research Policy 41(8), 2012 | Crossref | https://doi.org/10.1016/j.respol.2012.04.011 | 2026-09-28 | bibliographic (title) | section 1 |
| F3 | B. Beyer et al. (eds), Site Reliability Engineering (Google, 2016), chapter "Being On-Call": at least 50% of SRE time goes to engineering and no more than 25% to on-call; handling an incident (root cause, remediation, follow-up) takes about 6 hours on average, so the maximum is 2 incidents per 12-hour on-call shift | sre.google (the book's free online edition) | https://sre.google/sre-book/being-on-call/ | 2026-09-28 | "we strive to invest at least 50% of SRE time into engineering: of the remainder, no more than 25% can be spent on-call"; "takes 6 hours. It follows that the maximum number of incidents per day is 2 per 12-hour on-call shift" | section 4; dat:fm:engineering-organisation-design:sre |
| F4 | N. Forsgren, J. Humble and G. Kim, Accelerate, IT Revolution, 2018 | Open Library | https://openlibrary.org/works/OL19542983W | 2026-09-28 | bibliographic | section 5 |
| F5 | M. Skelton and M. Pais, Team Topologies, IT Revolution, 2019 | Open Library | https://openlibrary.org/works/OL21232655W | 2026-09-28 | bibliographic | section 1 |

## EXCLUDED

- The findings of MacCormack et al. (2012) and the delivery metrics of Accelerate: not restated beyond the titles (no abstract retrieved).


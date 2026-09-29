# 24. Entering a New Market — brief and source ledger

## Brief

- **Hook.** The plan says eight months to the first trade. The clearing agreement alone takes five, and it cannot start until the legal entity exists and has its identifier; the exchange will not certify the software until the clearing firm has set its limits. Nobody had drawn the critical path.
- **Sections.** Why enter: the edge and the size of the prize; The checklist: access, clearing, data, legal, staffing; The critical path; Staging the investment; A worked entry plan.
- **Defines.** entry plan, critical-path method, time to first trade, staged investment.
- **Uses (defined earlier).** stage gate (B7.1), kill criterion (B7.1), exchange membership (B1.30), clearing member (B1.30), futures commission merchant (B1.30), give-up (B1.30), legal entity identifier (B2.28), know-your-customer check (B3.25), incentive programme (B1.30), exchange certification (B13.25), revenue capture (B11.1), authorisation (ch17), total cost of ownership (ch20), best alternative to a negotiated agreement (ch23).
- **Tutorial.** An entry plan for a futures market in a new region: workstreams with durations and dependencies (entity, authorisation, clearing, membership, connectivity, data, hires, certification), the critical path, monthly costs, and three revenue ramps; the net present value with and without a kill point after six months of live trading. End state: a Gantt chart with the critical path, and the NPV distribution with and without staging.
- **Build.** `firm.entryplan`: workstreams as a dependency graph with durations and costs, the critical path (longest path) and slack, the cost schedule, revenue ramps, NPV and IRR, and the value of staging with kill points; Python; uses firm.firmecon, firm.clearcost and firm.feesched.
- **Weekend problem.** Eight months to first trade -- named result: the time to first trade on the critical path, and the value that the kill point adds to the entry's NPV.
- **Facts to verify.** published authorisation and registration timelines (FCA statutory periods; NFA registration steps) (pointer to ch17) (dated); an exchange's membership and certification process documents (dated); Kelley and Walker 1959, Critical-path planning and scheduling; Dixit and Pindyck 1994 (real options); a listed firm's disclosure of entering a new asset class or region (Form 10-K or annual report) (dated).
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Flow Traders, Annual Report 2025: "We expanded our presence in Asia, initiating active trading in China, an attractive growth market aligned with our core ETP strengths"; its total ETP value traded in Asia was EUR 152 billion in 2025 against EUR 114 billion in 2024 | Flow Traders annual report | https://www.flowtraders.com/media/2s2pdl01/flow-traders-annual-report-2025.pdf | 2026-09-28 | "We expanded our presence in Asia, initiating active trading in China"; "Flow Traders' total ETP value traded in Asia was EUR152 billion in 2025, compared to EUR114 billion in 2024" | section 1 |
| F2 | J. E. Kelley and M. R. Walker, "Critical-path planning and scheduling", Papers presented at the Eastern Joint IRE-AIEE-ACM Computer Conference, December 1959, pp. 160-173 | Crossref | https://doi.org/10.1145/1460299.1460318 | 2026-09-28 | bibliographic | section 3 |
| F3 | A. K. Dixit and R. S. Pindyck, Investment under Uncertainty, Princeton University Press, 1994 | Crossref | https://doi.org/10.1515/9781400830176 | 2026-09-28 | bibliographic | section 4 |

## EXCLUDED

- An exchange's membership and certification process documents and NFA registration steps: not fetched; the chapter's durations are inputs, and the statutory periods are chapter 17's.


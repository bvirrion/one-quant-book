# 28. Running a Multi-Strategy Book — brief and source ledger

## Brief

- **Hook.** A multi-strategy firm runs forty teams; in a bad month five of them lose at once, because three of their books were the same trade under different names.
- **Sections.** Allocation across strategies; Netting and shared risk; Turning strategies off; Capital, drawdown limits and the pod model.
- **Defines.** multi-strategy book, pod, drawdown limit, strategy correlation.
- **Uses (defined earlier).** risk budgeting (B7.26), internal crossing (B7.27), capacity curve (B7.28), deflated Sharpe ratio (B4.12).
- **Tutorial.** Run ten of this book's strategies together on the synthetic markets: allocate by risk budgets, net their trades, apply drawdown limits and stop rules, and measure the hidden overlap and the cost of stopping too early and too late.
- **Build.** `firm.multistrat`: multi-strategy allocation (risk budgets, correlation-aware sizing), netting on firm.tcost, drawdown limits and stop rules with their false-stop rates; Python.
- **Weekend problem.** Five at once — named result: the firm's drawdown with and without overlap detection, and the false-stop rate of a 5 per cent drawdown limit.
- **Facts to verify.** Pedersen 2015 (as ch1); Grossman and Zhou 1993 optimal investment strategies for controlling drawdowns (Mathematical Finance); public descriptions of the pod model (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. E. Khandani, A. W. Lo, "What happened to the quants in August 2007? Evidence from factors and transactions data", Journal of Financial Markets 14(1) (2011) 1-46: the "Quant Meltdown" in simulated long/short portfolios on valuation factors; a simulated market-making strategy lost heavily in the week of 6 August but was profitable before and after, suggesting market-wide deleveraging and a withdrawal of market-making capital from 8 August; two unwinds, 1 August 10:45-11:30 and 6 August from the open to 13:00, beginning with financials, long book-to-market and short earnings momentum (as Book 7 chapter 28 F1) | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.1016/j.finmar.2010.07.005 | 2026-09-25 | "suggesting that the dislocation was due to market-wide deleveraging and a sudden withdrawal of marketmaking risk capital starting August 8" | hook; section 2; strat:s1:running-a-multi-strategy-book:overlap; omsources |
| F2 | S. J. Grossman, Z. Zhou, "Optimal investment strategies for controlling drawdowns", Mathematical Finance 3(3) (1993) 241-276: for an investor who never wants wealth to fall below a fixed fraction alpha of its running maximum, with constant relative risk aversion the optimal risky investment is proportional to the surplus W - alpha M; risk is expected to fall at an all-time high and rise near the floor | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1467-9965.1993.tb00044.x | 2026-09-25 | abstract: "the optimal policy involves an investment in risky assets at time t in proportion to the surplus W_t - alpha M_t" | section 4; strat:s1:running-a-multi-strategy-book:drawdown; omsources |
| F3 | L. H. Pedersen, Efficiently Inefficient: How Smart Money Invests and Market Prices Are Determined, Princeton University Press (2015) (as chapter 1 F3) | Crossref metadata | https://doi.org/10.1515/9781400865734 | 2026-09-25 | Crossref: author, title, Princeton University Press | omsources |

## EXCLUDED

- Public descriptions of the pod model and of specific firms' drawdown rules: the sources found (Substack posts and career sites, some naming firms and quoting thresholds "reportedly") are not citable under the series' rule; no firm is named and no industry threshold is stated. The 5% limit of the named result is the brief's number, tested as one of five.
- The hook's "forty teams ... three books the same trade": rewritten as a hypothetical tied to Khandani and Lo's August 2007 episode.
- Pedersen (2015): metadata only; cited as further reading.

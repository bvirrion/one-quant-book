# 28. Build: an Execution Algorithm — brief and source ledger

## Brief

- **Hook.** A trader hands the algorithm an order to buy 200,000 shares by three o'clock with a limit price. Everything the book has built -- the schedule, the placement, the routing, the measurement -- has to run at once, and to keep running when the market does something the design did not expect.
- **Sections.** The algorithm as a state machine; Schedule, placement and routing together; Limits, pauses and exceptions; Measuring it; Rolling it out.
- **Defines.** I-would price, participation band.
- **Uses (defined earlier).** implementation-shortfall algorithm (ch16), execution algorithm (ch16), Almgren--Chriss model (ch14), urgency (ch14), order placement problem (ch17), smart order router (ch18), pre-trade cost estimate (ch19), slippage attribution (ch19), exchange simulator (ch26), agent-based model (ch27), transaction cost analysis (B7.23), A/B test (B7.21), canary deployment (B7.21), kill criterion (B7.1), trading pause (ch25).
- **Tutorial.** Assemble firm.execalgo from chapter 14's schedule, chapter 17's placement and chapter 18's router; run 200 parent orders in firm.exchsim populated by firm.agentmkt; measure them with firm.tca; test the algorithm against a TWAP baseline in a simulated A/B test, and through a halt and a volatility spike. Data: simulated.
- **Build.** `firm.execalgo`: a complete implementation-shortfall algorithm (scheduler, placement, router, limit and I-would prices, participation band, pause and resume on halts, cancel on kill, parameter interface, audit log) trading through firm.exchsim's order-entry client, measured with firm.tca; Python.
- **Weekend problem.** Beat TWAP by how much? -- named result: the shortfall saved against TWAP in basis points with its confidence interval, and its dependence on urgency and order size.
- **Facts to verify.** Almgren and Chriss 2000; Perold 1988; Kissell 2013; SEC Market Access Rule 15c3-5 pre-trade controls (as a design requirement; dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Almgren and N. Chriss, "Optimal execution of portfolio transactions", Journal of Risk 3(2) (2001) 5-39 (the brief's 2000 is the working-paper year; chapter 14 cites 2001) | Crossref record (as verified for chapter 14, F1) | https://doi.org/10.21314/jor.2001.041 | 2026-09-26 | bibliographic record | §2, omsources |
| F2 | A. F. Perold, "The implementation shortfall: paper versus reality", Journal of Portfolio Management 14(3) (1988) 4-9 | Crossref record (as verified for chapter 19) | https://doi.org/10.3905/jpm.1988.409150 | 2026-09-26 | bibliographic record | §4, omsources |
| F3 | R. Kissell, The Science of Algorithmic Trading and Portfolio Management, Academic Press (2014; the brief's 2013 is the first-release print year) | Crossref record (as verified for chapter 16, F5) | https://doi.org/10.1016/B978-0-12-401689-7.00001-5 | 2026-09-26 | bibliographic record | §2, omsources |
| F4 | SEC Rule 15c3-5 (17 CFR 240.15c3-5): a broker-dealer with market access must have controls reasonably designed to prevent the entry of orders exceeding pre-set credit or capital thresholds and of erroneous orders exceeding price or size parameters, order by order or over a short period, or duplicative orders (as verified for One Quant Book 13, chapter 22, F3) | 17 CFR 240.15c3-5 (c)(1)(i)-(ii), Cornell LII | https://www.law.cornell.edu/cfr/text/17/240.15c3-5 | 2026-09-26 | "Prevent the entry of orders that exceed appropriate pre-set credit or capital thresholds in the aggregate for each customer and the broker or dealer"; "Prevent the entry of erroneous orders, by rejecting orders that exceed appropriate price or size parameters, on an order-by-order basis or over a short period of time, or that indicate duplicative orders" | dat:mx:build-an-execution-algorithm:access |
| F5 | The SEC adopted Rule 15c3-5 on 3 November 2010 (Release 34-63241), ending unfiltered ("naked") market access (as verified for One Quant Book 1, F3) | SEC press release 2010-210 | https://www.sec.gov/newsroom/press-releases/2010-210-sec-adopts-new-rule-preventing-unfiltered-market-access | 2026-09-26 | "SEC Adopts New Rule Preventing Unfiltered Market Access" | dat:mx:build-an-execution-algorithm:access |

## EXCLUDED

- Rows F1-F5 reuse rows verified earlier in the series (chapters 14, 16, 19; Books 1 and 13); the sources were not refetched.
- The algorithm's design (state machine, band, I-would price, audit log) is the chapter's own and described as such; no firm's algorithm is named.
- All numbers of the A/B study and the stress scenarios are computed by mx_execalgo and tested.


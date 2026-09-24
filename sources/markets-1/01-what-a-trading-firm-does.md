# 1. What a Trading Firm Does — brief and source ledger

## Brief

- **Hook.** One share of one stock changes hands at 10:31:04; five firms earn something from that single print.
- **Sections.** Five business models; Where the money comes from: spread, risk premium, fee, carry, alpha; Principal versus agent; A map of one trade.
- **Defines.** market maker, proprietary trading firm, hedge fund, multi-manager platform, asset manager, principal, agent, bid--ask spread, alpha, assets under management.
- **Tutorial.** Decompose a day of simulated trades into who earned what (spread, fees, rebate, P&L).
- **Build.** `firm.ledger`: a fee-and-revenue ledger that every later component posts to.
- **Weekend problem.** A week at a small market maker — named result: the break-even daily volume.
- **Facts to verify.** public revenue figures of listed market makers (annual reports); fee model 2-and-20 history; size of global AUM (industry report).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Virtu Financial FY2025: total revenues $3,632.1m; Adjusted Net Trading Income $2,145.3m (FY2024: $2,876.9m; $1,597.7m) | Virtu Financial press release "Virtu Announces Fourth Quarter 2025 Results", 29 Jan 2026 | https://ir.virtu.com/news-releases/news-release-details/virtu-announces-fourth-quarter-2025-results | 2026-09-18 | "Total revenues increased 26.2% to $3,632.1 million ... Adjusted Net Trading Income increased 34.3% to $2,145.3 million ... compared to $1,597.7 million for 2024" | dat:m1:what-a-trading-firm-does:listed |
| F2 | Flow Traders FY2025: Net Trading Income EUR 485.8m; 635 FTEs at end 4Q25 | Flow Traders press release "4Q and FY 2025 Results", 12 Feb 2026 | https://www.flowtraders.com/news/flow-traders-4q-fy-2025-results/ | 2026-09-18 | "Net Trading Income came in at EUR 485.8m ... employed 635 FTEs at the end of 4Q25, compared to 609 at the end of 4Q24" | dat:m1:what-a-trading-firm-does:listed |
| F3 | Flow Traders FY2024: Net Trading Income EUR 467.8m; 609 FTEs; ETP value traded EUR 1,545bn | Flow Traders press release "4Q and FY 2024 Results", 13 Feb 2025 | https://www.flowtraders.com/news/flow-traders-4q-2024-results/ | 2026-09-18 | "Net Trading Income totaled EUR 467.8m ... ETP Value Traded increased by 5% in FY 2024 to EUR 1,545b ... 609 FTEs" | dat:m1:what-a-trading-firm-does:listed; exo 6 |
| F4 | Global AUM $147tn in 2025 (+11%), $128tn in 2024; >80% of 2025 revenue growth from markets | BCG Global Asset Management Report 2026 and 2025 | https://www.bcg.com/publications/2026/an-imperative-for-growth-and-the-new-economics-of-asset-management | 2026-09-18 | "Global assets under management reached $147 trillion in 2025, up 11%"; 2025 report press release: "$128 trillion in 2024" (https://www.bcg.com/press/29april2025-global-asset-management-record-high-critical-turning-point) | dat:m1:what-a-trading-firm-does:aum |
| F5 | A. W. Jones founded the first hedge fund in 1949 with $100,000; charged 20% of profits, initially no other fee; management fee added later | Institutional Investor, "Alfred Winslow Jones" (Hall of Fame) | https://www.institutionalinvestor.com/article/2btfiovsema7r1ake9534/premium/alfred-winslow-jones | 2026-09-18 | "He charged a 20 percent performance fee ... raised a total of $100,000" ; corroborated https://en.wikipedia.org/wiki/Alfred_Winslow_Jones | rem:m1:what-a-trading-firm-does:jones |

## EXCLUDED

- Revenue or profit figures of private market makers and hedge funds: no primary public source fetched; the chapter names only the two listed firms.
- Fee levels in the simulator (taker 0.30c, rebate 0.20c) are illustrative model parameters, stated as such; real schedules are Chapter 29's dated boxes.

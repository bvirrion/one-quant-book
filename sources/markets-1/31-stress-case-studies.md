# 31. Stress Case Studies — brief and source ledger

## Brief

- **Hook.** At 14:45:28 on 6 May 2010 trading in the E-mini paused for five seconds.
- **Sections.** 6 May 2010; 24 August 2015; 5 February 2018; January 2021; What the four have in common.
- **Defines.** flash crash, stub quote, limit up--limit down, market-wide circuit breaker, liquidity spiral, clearly erroneous trade.
- **Tutorial.** Reconstruct a liquidity withdrawal in a simulated book.
- **Build.** Incident replay harness.
- **Weekend problem.** Five seconds — named result: the depth that would have absorbed the sell programme.
- **Facts to verify.** CFTC-SEC 2010 report numbers; SEC Aug 24 2015 research note; XIV termination Feb 2018 (prospectus, press); SEC GameStop staff report; LULD plan bands.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | 6 May 2010: at 2:32 pm a mutual fund complex began a sell programme of 75,000 E-mini contracts (about $4.1bn) as a hedge, via an algorithm targeting 9% of the previous minute's volume "without regard to price or time"; executed in about 20 minutes; an earlier comparable programme by the same trader (with price and time taken into account) took more than 5 hours for its first 75,000 contracts; about 35,000 contracts sold 2:32-2:45 | CFTC-SEC, Findings Regarding the Market Events of May 6, 2010 (30 Sep 2010), pdftotext | https://www.sec.gov/news/studies/2010/marketevents-report.pdf | 2026-09-18 | executive summary pp. 2-3 | hook; section 1; exo 1, 4; pb; iq 1 |
| F2 | Between 2:45:13 and 2:45:27 HFTs traded over 27,000 contracts, about 49% of volume, buying about 200 net ("hot-potato"); buy-side depth in the E-mini fell to about 1,050 contracts ($58m), under 1% of the morning level; E-mini down more than 5% and SPY more than 6% from 2:41 to 2:45:27 | same report | https://www.sec.gov/news/studies/2010/marketevents-report.pdf | 2026-09-18 | executive summary p. 3 | hook; section 1; pb Q15 |
| F3 | CME Stop Logic paused E-mini trading for 5 seconds at 2:45:28; "sell-side pressure in the E-Mini was partly alleviated and buy-side interest increased. When trading resumed at 2:45:33 p.m., prices stabilized" | same report | https://www.sec.gov/news/studies/2010/marketevents-report.pdf | 2026-09-19 | p. 4 (fc.txt l. 291-295) | hook; section 1; pb Q9 |
| F4 | Over 20,000 trades in more than 300 securities executed at prices 60% or more away from their 2:40 values and were broken; executions at one penny or $100,000 against stub quotes | same report | https://www.sec.gov/news/studies/2010/marketevents-report.pdf | 2026-09-18 | executive summary pp. 5-6 | hook; def flash; exo 5; iq 1 |
| F5 | 8 Nov 2010: SEC approved exchange and FINRA rules that "effectively prohibit" stub quotes: market-maker quotes within 8% of the NBBO for circuit-breaker securities (20% near open and close), 30% for others; effective 6 Dec 2010; stub-quote executions were a significant proportion of the broken trades | SEC press release 2010-216 | https://www.sec.gov/news/press/2010/2010-216.htm | 2026-09-19 | "must enter quotes that are not more than 8% away from the NBBO" | table; exo 5 solution |
| F6 | 24 Aug 2015: E-mini limit down 5% and paused 9:25-9:30; SPY opened 5.2% down, low 7.8% down by 9:35, closed 4.2% down; by 9:35 NYSE had opened 38% of its S&P 500 listings; 1,278 LULD halts, 1,058 in 327 ETPs and 220 in 144 other securities; 80% of ETPs had no halt; 19.2% of ETPs fell 20% or more against 4.7% of corporates | SEC Division of Trading and Markets, Research Note: Equity Market Volatility on August 24, 2015 (Dec 2015), pdftotext | https://www.sec.gov/marketstructure/research/equity_market_volatility.pdf | 2026-09-18 | summary pp. 1-6 | section 2; fig halts; exo 3, 6; iq 3 |
| F7 | LULD rules: bands 5/10/20% around the 5-minute mean trade price; new reference only if 1% away and after 30 s; doubled 9:30-9:45 and 3:35-4:00; leveraged ETPs multiplied by leverage; 15 s in limit state leads to a pause of at least 5 minutes declared by the primary listing exchange | same research note, appendix on LULD | https://www.sec.gov/marketstructure/research/equity_market_volatility.pdf | 2026-09-18 | LULD background section | dat:m1:stress-case-studies:luld; exo 2; iq 2; build |
| F8 | LULD Amendment 12 (implemented 20 Nov 2017): harmonised reopening auction after a pause, with collars widening every five minutes; prompted by 24 Aug 2015 | Cboe LULD Amendment 12 fact sheet; NYSE fact sheet (search extract) | https://cdn.cboe.com/resources/membership/LULD-Amendment-12-Fact-Sheet.pdf | 2026-09-19 | "harmonized procedure for calculating auction collars" | table |
| F9 | 5 Feb 2018 facts | see chapter 25 ledger F3, F4 | https://www.bis.org/publ/qtrpdf/r_qt1803t.htm | 2026-09-18 | — | section 3; table |
| F10 | January 2021 facts: short interest 122.97% of float; about 2,700% rise; covering a small fraction of buying; clearing deposit requirement of about $3.7bn against $700m on deposit | see chapter 16 ledger F3 and chapter 5 ledger F1, F3 | https://www.sec.gov/files/staff-report-equity-options-market-struction-conditions-early-2021.pdf | 2026-09-18 | — | section 3 |
| F11 | SEC T+1 rule (adopted 15 Feb 2023, compliance 28 May 2024) was advanced in the aftermath of the 2021 meme-stock events | Morrison Foerster client note on the adopting release (search extract); ch. 5 ledger F4 | https://www.mofo.com/resources/insights/230224-new-sec-rules-and-amendments | 2026-09-19 | "in the aftermath of the 'meme stock' events in early 2021" | table |

## EXCLUDED


- "E-mini at its overnight limit by 09:15" and "SPY back above its open by 09:40": written from memory, not in the passages read; removed.
- "Since 2010 the clearly-erroneous thresholds are numerical and known in advance": true to my recollection but not checked against a rule text; the definition now says only that the 2010 threshold was chosen after the event (F4).
- "single-stock circuit breaker pilot (June 2010)" as a consequence: not checked; the table cites only F5 and "price bands" (F7).
- "volatility products closed or de-levered" (generic): replaced by the verified redemption of the largest inverse product (ch. 25 F4).
- All simulation numbers are the toy model's own and are attributed to nothing real. First version of the toy (depth as a function of the total fall, one-minute steps) was discarded on 2026-09-19: its result depended on the time step and churn reduced the fall. Replaced by depth as a function of the fall below a five-minute average, sub-stepped; test added for step independence.

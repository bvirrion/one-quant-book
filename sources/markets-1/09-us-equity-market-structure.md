# 9. US Equity Market Structure — brief and source ledger

## Brief

- **Hook.** The same 100 shares can be bought on sixteen exchanges and thirty dark pools; the law says which price is the best.
- **Sections.** Regulation NMS; The national best bid and offer; The tape and the direct feeds; Exchange families and fee models; Off-exchange trading; Speed bumps and tick rules.
- **Defines.** national best bid and offer, order protection rule, securities information processor, direct feed, maker-taker pricing, inverted venue, intermarket sweep order, dark pool, round lot, odd lot, access fee cap, trade-through.
- **Tutorial.** Build an NBBO from per-venue quotes and detect trade-throughs and locked markets.
- **Build.** `firm.nbbo`: consolidated best-quote builder.
- **Weekend problem.** A stale tape — named result: the latency-arbitrage profit per share.
- **Facts to verify.** Rule 611, 610, 612 text; number of exchanges (SEC list); off-exchange share (Cboe/FINRA); IEX 350 microsecond speed bump; 2024 tick-size and access-fee amendments.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Rule 611 adopted 2005: intermarket protection against trade-throughs for all NMS stocks; definition of trade-through; Rule 610(e) restricts locked and crossed quotations | SEC Fact Sheet "Regulation NMS Reforms" (Release 34-105655) | https://www.sec.gov/files/34-105655-fact-sheet.pdf | 2026-09-18 | PDF text: "Rule 611 of Regulation NMS was adopted in 2005 and established intermarket protection against trade-throughs ... A trade-through occurs when ..." | def opr; section 1 |
| F2 | On 11 June 2026 the SEC proposed to rescind Rule 611 and Rule 610(e); 60-day comment period after Federal Register publication | same fact sheet | https://www.sec.gov/files/34-105655-fact-sheet.pdf | 2026-09-18 | "On June 11, 2026, the Securities and Exchange Commission proposed amendments to Regulation NMS to: Rescind Rule 611 ... Rescind Rule 610(e)" | hook; dat:m1:us-equity-market-structure:nms; pb q18; iq 6 |
| F3 | 18 Sep 2024 amendments: $0.005 minimum pricing increment for certain stocks; access fee cap reduced from $0.003 to $0.001 | SEC Release 34-105656 (recital); SEC press release 2024-137 | https://www.sec.gov/files/rules/exorders/2026/34-105656.pdf | 2026-09-18 | "amended Rule 612 ... minimum pricing increment of $0.005 ... reduced the level of the access fee caps under Rule 610(c) ... to $0.001 per share" | def cap; dat nms; pb q17 |
| F4 | Order of 11 June 2026: compliance with amended Rule 612 and amended Rule 610(c) deferred until the first business day of November 2027 | SEC Release 34-105656 | https://www.sec.gov/files/rules/exorders/2026/34-105656.pdf | 2026-09-18 | "Rules 600(b)(89)(i)(F) and 612 ...: Until the first business day of November 2027. Rule 610(c) ...: Until the first business day of November 2027." | dat:m1:us-equity-market-structure:nms |
| F5 | 2025: ADV 17.6bn shares (+44.6%), ADNV $1.1tn (+43.3%); TRF share 50.6% of consolidated volume; of TRF volume 18.7% on ATSs and 81.3% through principal dealers | Cboe, "2025 U.S. Equities Year in Review" | https://www.cboe.com/insights/posts/2025-u-s-equities-year-in-review | 2026-09-18 | quotes as fetched | hook; dat:m1:us-equity-market-structure:where; figure; exo 3 |
| F6 | Round lot tiers by price (100 / 40 / 10 / 1 shares at $250, $1,000, $10,000); effective 3 Nov 2025; quote sizes disseminated in shares | Cboe Regulation NMS Round Lots Enhancements FAQ, 28 Oct 2025 | https://cdn.cboe.com/resources/membership/Round_Lots_Enhancements_FAQ.pdf | 2026-09-18 | "(1) $250.00 or less per share as 100 shares; (2) $250.01 to $1,000.00 ... 40 shares; ..." | dat:m1:us-equity-market-structure:lots; exo 2 |
| F7 | IEX: 38 miles of coiled fibre, 350 microseconds; SEC approved IEX as an exchange on 17 June 2016; Commission interpretation: delay is de minimis, quotes remain immediately accessible and protected | SEC Release 34-78102; IEX "speed bump" page | https://www.sec.gov/files/rules/interp/2016/34-78102.pdf | 2026-09-18 | search extract of the interpretation; https://exchange.iex.io/about/speed-bump/ | section Speed bumps |
| F8 | More than a dozen registered exchanges trade US equities; dozens of NMS-stock ATSs | SEC, National Securities Exchanges list; SEC ATS list | https://www.sec.gov/about/divisions-offices/division-trading-markets/national-securities-exchanges | 2026-09-18 | list pages (counts not printed in the book) ; https://www.sec.gov/foia/frequently-requested-documents/alternative-trading-system-ats-list | hook |

## EXCLUDED

- Exact count of equity exchanges and of dark pools: a search summary claimed '29 exchanges that trade US equities', which conflates options exchanges; the book prints only 'more than a dozen' and 'dozens'.
- The 2007 compliance date of Rule 611 and the ownership of exchanges by exactly three groups: not in a fetched source; replaced by 'two decades' and 'a few groups'.
- Later proposals of asymmetric speed bumps by other exchanges: not verified; removed.
- Real maker/taker/inverted fee levels: schedules change monthly; all fee figures are labelled illustrative and sit inside the 30-mil cap (real schedules: Chapter 29).
- Status of odd-lot quote dissemination on the SIPs (scheduled for May 2026 in an October 2025 document): not confirmed as implemented; not printed.
- Whether the June 2026 proposal has since been adopted or withdrawn: the dated box tells the reader to check.

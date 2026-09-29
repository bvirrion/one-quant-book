# 8. Short-Term Interest-Rate Futures — brief and source ledger

## Brief

- **Hook.** Twelve days before a central-bank meeting the futures price implies a 62 percent chance of a cut; the desk has to decide whether that is too high.
- **Sections.** Overnight-rate futures; IMM dates, packs, bundles and strips; Pricing a meeting; The convexity adjustment.
- **Defines.** overnight-rate future, IMM date, reference quarter, futures strip, pack, bundle, implied policy path, convexity adjustment.
- **Uses (defined earlier).** futures contract, overnight benchmark rate, compounding in arrears, daily settlement price, variation margin, policy rate.
- **Tutorial.** Extract meeting-by-meeting policy expectations from a strip of one-month and three-month futures.
- **Build.** `firm.meetings`: policy-path extractor.
- **Weekend problem.** Cut or hold — named result: the meeting probability implied by the futures and its sensitivity to the turn.
- **Facts to verify.** CME SOFR futures specs (1M average, 3M compounded); ICE SONIA / Euribor futures specs; IMM dates definition; FOMC meeting schedule current year; Euribor still published (EMMI).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CME Three-Month SOFR futures (SR3): contract unit USD 2,500 x IMM Index (100 minus rate); one basis point = USD 25; minimum tick 0.0025 (1/4 bp, USD 6.25) for contracts with four months or less to expiry, 0.005 (1/2 bp, USD 12.50) otherwise; reference quarter from (and including) the 3rd Wednesday of the 3rd month preceding the delivery month to (not including) the 3rd Wednesday of the delivery month; cash settled at 100 minus compounded daily SOFR over the reference quarter; nearest 39 March-quarterly contracts listed | Metro Trade (FCM) specification page for SR3 (secondary; cmegroup.com not fetchable) and search excerpt of CME Group Rulebook Chapter 460 | https://help.metrotrade.com/kb/three-month-sofr-futures-sr3-contract-specifications | 2026-09-23 | "$2,500 x contract-grade IMM Index"; "The interval from the 3rd Wednesday of the 3rd month preceding the delivery month to, but not including, the 3rd Wednesday of the delivery month" | dat:m2:short-term-interest-rate-futures:contracts; def reference quarter |
| F2 | CME One-Month SOFR futures (SR1): contract valued at USD 4,167 x IMM Index; one basis point = USD 41.67; all twelve months listed; cash settled on the arithmetic average of daily SOFR during the contract month; minimum tick 0.005 (USD 20.835), 0.0025 (USD 10.4175) in some cases | CME Rulebook Chapter 461 (search excerpt; site blocks fetching) | https://www.cmegroup.com/rulebook/CME/IV/400/461.pdf | 2026-09-23 | "Each contract is valued at $4,167 times the contract-grade IMM Index"; "$41.67 per futures contract" | dat:m2:short-term-interest-rate-futures:contracts; def overnight-rate future |
| F3 | ICE Three Month SONIA Index Futures: unit GBP 2,500 x Rate Index; price 100 minus compounded SONIA over the accrual period; accrual from the 3rd Wednesday of the delivery month to the business day before the 3rd Wednesday of the next quarterly month; ticks 0.0025 (GBP 6.25) front, 0.005 (GBP 12.50) otherwise; 25 quarterly delivery months | ICE product page, Three Month SONIA Index Futures | https://www.ice.com/products/68361266/Three-Month-SONIA-Index-Futures | 2026-09-23 | "Third Wednesday of the Delivery Month" (first accrual date) | dat:m2:short-term-interest-rate-futures:contracts; exo 6 |
| F4 | FOMC 2026 meetings: 27-28 Jan, 17-18 Mar, 28-29 Apr, 16-17 Jun, 28-29 Jul, 15-16 Sep, 27-28 Oct, 8-9 Dec; 2027: 26-27 Jan, 16-17 Mar, 27-28 Apr, 8-9 Jun, 27-28 Jul, 14-15 Sep, 26-27 Oct, 7-8 Dec | Federal Reserve, FOMC meeting calendars | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | 2026-09-23 | calendar table | examples; problem; fig timeline |
| F5 | Euribor: the rate at which wholesale funds in euro could be obtained by credit institutions in EU and EFTA countries in the unsecured money market; tenors 1 week, 1, 3, 6, 12 months; published each TARGET2 day at or shortly after 11:00 CET; hybrid methodology; administered by EMMI | EMMI, Euribor page | https://www.emmi-benchmarks.eu/benchmarks/euribor/ | 2026-09-23 | "the rate at which wholesale funds in euro could be obtained by credit institutions" | dat:m2:short-term-interest-rate-futures:contracts |
| F6 | New target range applies the day after the FOMC decision (Sept 2026: decision 16 Sept, effective 17 Sept) | Chapter 1 ledger F1 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm | 2026-09-23 | "effective September 17, 2026" | method; build rule |

## EXCLUDED

- Market prices of SOFR futures: none fetched; every price in the chapter is illustrative and labelled so.
- Pack and bundle definitions as CME products (colour codes of packs): not fetched; the definitions are given generically.
- Size and turnover of SOFR futures: not fetched.
- The Ho-Lee convexity formula is derived in the text (One Quant Book 6 treats it properly); the volatilities used are illustrative.


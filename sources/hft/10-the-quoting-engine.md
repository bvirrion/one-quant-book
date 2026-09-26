# 10. The Quoting Engine — brief and source ledger

## Brief

- **Hook.** A market maker changes its mind about its price tens of thousands of times a day on one instrument; every change is a cancel and a new order or a modification, each can cross a fill already on its way, and the venue counts them all.
- **Sections.** From target quotes to orders; Cancel-replace, priority and in-flight states; Throttles, message limits and order-to-trade ratios; Self-match prevention and multiple strategies; Quote ladders and the line not to cross.
- **Defines.** cancel-replace, quote ladder, self-match prevention, order-to-trade ratio, message throttle.
- **Uses (defined earlier).** rate limit (B3.15), post-only order (B3.15), price-time priority (B1.19), layering (B9.29), spoofing (B9.29), cancellation rate (B7.8), order lifecycle (B7.17), queue position (B7.18), latency model (B7.18), order-book replay (B7.18), exchange simulator (B10.26, by outline).
- **Tutorial.** Drive quoteengine from target quotes produced by the chapter 3 policy on firm_tape; count messages, measure the priority lost by modifications, and replay fills that cross cancels to test the in-flight state machine.
- **Build.** `firm.quoteengine`: target quotes to order actions (diffing, minimum price and size change, modify versus cancel-replace by the venue's priority rules), in-flight state machine per order, token-bucket throttle and order-to-trade budget, self-match prevention across strategies; Python reference, C++20 and Rust twins on one fixture.
- **Weekend problem.** Ten thousand changes of mind — named result: the message count and priority lost per hour under three quoting thresholds, against the capture each earns.
- **Facts to verify.** Commission Delegated Regulation (EU) 2017/566 (RTS 9) order-to-trade ratio (dated); CME Group messaging efficiency programme and self-match prevention (dated); Eurex excessive system usage and order-to-trade limits (dated); Nasdaq or Cboe anti-internalisation / self-trade prevention options (dated); US v. Coscia 7th Cir. 2017 (the line: from Book 9 ch. 29).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Commission Delegated Regulation (EU) 2017/566 (RTS 9), Article 2: trading venues calculate each member's ratio of unexecuted orders to transactions at least at the end of every session, in volume terms (total volume of orders / total volume of transactions) - 1 and in number terms (total number of orders / total number of transactions) - 1; the maximum is exceeded if the member's activity in one instrument exceeds either ratio; orders are counted per order type as set out in the Annex | legislation.gov.uk, as adopted | https://www.legislation.gov.uk/eur/2017/566/article/2/adopted | 2026-09-25 | "(a) in volume terms: (total volume of orders/total volume of transactions) - 1; (b) in number terms: (total number of orders/total number of transactions) - 1" | dat:hf:the-quoting-engine:limits |
| F2 | CME Globex Messaging Efficiency Program (2019 revision filed with the CFTC): messaging scores assign pre-defined factors to order types (new orders, modifications, ...); the score divided by traded volume in a product group during regular trading hours is the Volume Ratio, compared with Product Group Benchmarks set each quarter | CME Group submission to the CFTC, rule filing 8 November 2019 | https://www.cftc.gov/sites/default/files/filings/orgrules/19/11/rule110819cmedcm001.pdf | 2026-09-25 | pdftotext: "Messaging scores are calculated by assigning pre-defined factors to different order types (new orders, order modifications etc.)... divided by the... traded volume in a product group to obtain the... volume ratio" | dat:hf:the-quoting-engine:limits |
| F3 | United States v. Coscia (7th Cir., 7 August 2017): spoofing defined in 7 U.S.C. 6c(a)(5)(C) as "bidding or offering with the intent to cancel the bid or offer before execution"; the court rejected the vagueness argument that high-frequency traders cancel 98% of orders before execution | Seventh Circuit opinion, No. 16-3017 | https://media.ca7.uscourts.gov/cgi-bin/rssExec.pl?Path=Y2017%2FD08-07%2FC%3A16-3017%3AJ%3ARipple%3Aaut%3AT%3AfnOp%3AN%3A2006533%3AS%3A0&Submit=Display | 2026-09-25 | pdftotext: "high-frequency traders cancel 98% of orders before execution"; the statutory definition as quoted | §5 |

## EXCLUDED

- CME's current (2024) MEP document and benchmark tiers: cmegroup.com could not be fetched; the chapter states only the mechanism from the 2019 CFTC filing.
- Eurex excessive system usage fees and Nasdaq/Cboe self-trade prevention option lists: not fetched; self-trade prevention is described generically (Book 10 ch. 26 defines it; firm.exchsim implements modes).


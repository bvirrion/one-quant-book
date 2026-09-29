# 22. Data Strategy and Costs — brief and source ledger

## Brief

- **Hook.** The UK regulator's study of the wholesale data market concluded that users of trading data, benchmarks and credit ratings had little room to negotiate and that licence terms were complex enough to make costs hard to predict. For many trading firms the data bill is the fastest-growing line after pay.
- **Sections.** What a firm pays for data; Licences and their units of count; Audits and back-billing; Negotiating with exchanges and vendors; Data as a strategic asset.
- **Defines.** data budget, enterprise licence, derived-data licence, redistribution licence, back-billing.
- **Uses (defined earlier).** non-display fee (B1.29), market data feed (B1.4), direct feed (B1.9), securities information processor (B1.9), consolidated tape provider (B1.11), point-in-time data (B7.3), alternative data (B7.12), entitlement (B15.23), usage report (B15.23), unit of count (B15.23), market-data audit (B15.23), derived data (B15.23), total cost of ownership (ch20).
- **Tutorial.** A firm's data inventory -- feeds, terminals, non-display uses, alternative datasets -- priced under fee rules by user, device and use: find the headcount at which an enterprise licence wins, and estimate the back-billing exposure of an audit that finds under-reported users over three years. End state: the data budget by category, and the enterprise break-even chart.
- **Build.** `firm.databudget`: data products and fee rules as data (per user, per device, per use category, caps and enterprise terms), usage records, the budget, enterprise break-even, audit exposure with interest, and a per-strategy allocation of data costs; Python; uses firm.vendoreval's trial metrics for alternative data.
- **Weekend problem.** The audit letter -- named result: the headcount at which an enterprise licence beats per-user fees, and the back-billing exposure of an audit that finds 15 per cent under-reporting over three years.
- **Facts to verify.** FCA Wholesale Data Market Study, final report (2024) (dated); SEC Market Data Infrastructure rule (2020) (dated); MiFIR art. 13 reasonable commercial basis and the EU consolidated tape (dated); an exchange's published market-data policy: units of count, non-display categories, audit clauses (dated); D.C. Circuit 2020 decision on the SEC's market-data fee orders (NetCoalition line) (dated).
- **Data.** Synthetic; dated boxes.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | FCA, Wholesale Data Market Study, Market Study MS23/1.5 (February 2024): launched 2 March 2023 after persistent user concerns; covered benchmarks, credit ratings data and market data vendor services; found no evidence that firms cannot access the data they need, but evidence of and drivers for market power in all three markets, so that users may be paying higher prices; complex licensing by market data vendors and trade data providers increases users' costs; many users must hold licences both from the data generator (such as a trading venue) and from the vendor; a proliferation of licences for similar data and different use cases; complexity drives costs such as operating a compliance team | FCA publication | https://www.fca.org.uk/publication/market-studies/ms23-1-5.pdf | 2026-09-28 | "we have not found evidence that firms cannot access the wholesale data they need"; "across all 3 markets in scope of the study, we have identified evidence of, and drivers for, market power. Users may be paying higher prices"; "Many MDV users have to hold licences both from the data generator (such as a trading venue) and from the MDV"; "Complexity also drives additional costs for data users, such as operating a compliance team" | hook; section 1; dat:fm:data-strategy-and-costs:rules |
| F2 | Regulation (EU) No 600/2014 (MiFIR), Article 13(1) as adopted: trading venues shall make pre- and post-trade information available to the public on a reasonable commercial basis with non-discriminatory access, and free of charge 15 minutes after publication | CELEX 32014R0600 (text as adopted; later amendments not restated) | http://publications.europa.eu/resource/celex/32014R0600 | 2026-09-28 | "available to the public on a reasonable commercial basis and ensure non-discriminatory access to the information. Such information shall be made available free of charge 15 minutes after publication" | dat:fm:data-strategy-and-costs:rules |
| F3 | 17 CFR 242.614 (SEC market data infrastructure rules): registration and responsibilities of competing consolidators, which receive NMS data directly from exchanges and generate consolidated market data products (86 FR 18811, 9 April 2021, amended 89 FR 26617, 2024) | eCFR | https://www.ecfr.gov/current/title-17/chapter-II/part-242/subject-group-ECFR1b3a2a4a4ff4b1b/section-242.614 | 2026-09-28 | "Registration and responsibilities of competing consolidators"; "[86 FR 18811, Apr. 9, 2021, as amended at 89 FR 26617, Apr. 15, 2024]" | dat:fm:data-strategy-and-costs:rules |

## EXCLUDED

- An exchange's published market-data policy (units of count, non-display categories, audit clauses): the Nasdaq policy PDF was not reachable; fee levels in the chapter are illustrative inputs and Book 1 chapter 29 carries the sourced non-display fee.
- The 2020 D.C. Circuit decision on the SEC's market-data fee orders: not fetched; not stated.
- The EU consolidated tape under the 2024 MiFIR review: not restated.


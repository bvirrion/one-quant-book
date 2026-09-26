# 20. The Buy-Side Trading Desk and Its Brokers — brief and source ledger

## Brief

- **Hook.** A fund's trading desk sends its orders to six brokers' algorithms and pays each in commissions. Which broker is best cannot be seen in a quarter's data, so the desk lets a wheel choose, and measures.
- **Sections.** What the desk does; High touch and low touch; Algo wheels; Evaluating brokers; Paying for research and execution.
- **Defines.** high-touch trading, low-touch trading, algo wheel, broker scorecard, order management system, execution management system, commission sharing agreement, research unbundling.
- **Uses (defined earlier).** best execution (B1.11), broker (B1.4), sales-trader (B1.2), block trade (B1.2), indication of interest (ch9), execution algorithm (ch16), transaction cost analysis (B7.23), peer-universe comparison (ch19), A/B test (B7.21), randomisation unit (B7.21), minimum detectable effect (B7.21), power of a test (B4.12).
- **Tutorial.** Simulate an algo wheel over six brokers with different true costs and order mixes; compare random allocation with performance-weighted allocation (Thompson sampling); estimate broker differences with the chapter 19 toolkit and compute how many months the desk needs to rank them. Data: simulated.
- **Build.** `firm.algowheel`: randomised and stratified allocation, difficulty-adjusted broker evaluation (on firm.tca), Thompson-sampling allocation, a broker scorecard; Python.
- **Weekend problem.** Six brokers, one wheel -- named result: the months of flow needed to tell the best broker from the second with 80% power, with and without difficulty adjustment.
- **Facts to verify.** MiFID II research unbundling (2018) and the UK (FCA PS24/9) and EU (Listing Act 2024) re-bundling options (dated); SEC no-action relief on research payments and its expiry (dated); FCA thematic reviews of best execution; Anand et al. 2012 (RFS); a public description of algo wheels (buy-side publication; dated, only if citable).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. Anand, P. Irvine, A. Puckett, K. Venkataraman, Review of Financial Studies 25(2) (2012) 557-598: some brokers deliver better executions consistently over time | Crossref record; SSRN abstract (1272040) | https://doi.org/10.1093/rfs/hhr110 | 2026-09-26 | "Although some brokers can deliver better executions consistently over time, our analysis suggests that trading desk skill is not limited to a selection of better brokers" | §4, omsources |
| F2 | MiFID II required separate charges for execution and for research (P&L or research payment account), "unbundling"; the FCA's joint payment option came into force on 1 August 2024 | FCA PS24/9, Payment optionality for investment research (July 2024) | https://www.fca.org.uk/publication/policy/ps24-9.pdf | 2026-09-26 | "MiFID II introduced requirements to separate charges for execution and charges for research, thereby 'unbundling' these two services"; "The changes to the research rules will come into force on 1 August 2024." | dat:mx:the-buy-side-trading-desk-and-its-brokers:research, omsources |
| F3 | MiFID II implementation date 3 January 2018; SEC staff no-action relief (26 October 2017) letting broker-dealers receive research payments in hard dollars or from research payment accounts, temporarily | SEC press release 2017-200 | https://www.sec.gov/newsroom/press-releases/2017-200-0 | 2026-09-26 | "Jan. 3, 2018, implementation date"; "broker-dealers, on a temporary basis, may receive research payments from money managers in hard dollars or from advisory clients' research payment accounts" | dat:mx:the-buy-side-trading-desk-and-its-brokers:research, omsources |
| F4 | The SEC staff MiFID II no-action relief was extended to July 3, 2023 (November 4, 2019) and expired on July 3, 2023 | Statement of Commissioner M. T. Uyeda, July 5, 2023 | https://www.sec.gov/newsroom/speeches-statements/uyeda-statement-staff-no-action-letter-07-05-2023 | 2026-09-26 | "The MiFID II Relief expired on July 3, 2023."; "extension of relief to July 3, 2023" | dat:mx:the-buy-side-trading-desk-and-its-brokers:research, omsources |
| F5 | Directive (EU) 2024/2811 of 23 October 2024 (Listing Act) amends MiFID II Article 24(9a): the firm informs clients of its choice to pay jointly or separately for execution and research, assesses research annually; transposition by 5 June 2026, applied from 6 June 2026 | EUR-Lex official text (read through the WebFetch tool, EUR-Lex throttled direct downloads) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024L2811 | 2026-09-26 | "(b) the investment firm informs its clients of its choice to pay either jointly or separately for execution services and research"; "(c) the investment firm assesses on an annual basis the quality, usability and value of the research used"; "by 5 June 2026"; "They shall apply those provisions from 6 June 2026." | dat:mx:the-buy-side-trading-desk-and-its-brokers:research, omsources |

## EXCLUDED

- A public description of algo wheels by a buy-side firm: none cited (the brief allowed one only if citable); the chapter describes wheels generically.
- FCA best-execution thematic reviews: not needed.
- The simulated desk's parameters (600 orders a month, 30 bp noise, 25 bp difficulty dispersion, effects 0-8 bp) are assumptions stated in the
  text, not calibrated to real desks; the chapter says so by describing them as the simulated desk.
- All numbers are computed by mx_wheel and firm.algowheel and tested.


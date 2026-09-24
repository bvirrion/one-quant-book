# 20. Margin — brief and source ledger

## Brief

- **Hook.** The position did not change overnight; the money required to hold it rose by half.
- **Sections.** Variation margin; Initial margin: scenario methods; Initial margin: value-at-risk methods; Portfolio offsets; Procyclicality and intraday calls.
- **Defines.** performance bond, maintenance margin, scanning range, inter-commodity spread credit, margin period of risk, portfolio margining, procyclicality, intraday margin call.
- **Tutorial.** A SPAN-style scenario margin for a futures-and-options portfolio.
- **Build.** `firm.margin`: scenario margin engine.
- **Weekend problem.** March 2020 — named result: the additional margin called on a fixed portfolio.
- **Facts to verify.** SPAN 16 scenarios description; CME SPAN 2; Eurex Prisma; margin increases March 2020 (BIS/CFTC); LME nickel 2022 margin facts.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SPAN: risk array over 16 scenarios; first two volatility only; twelve at 1/3, 2/3, 3/3 of the price scan range with volatility up/down; scenarios 15-16 extreme moves (a multiple, "usually two or three times", "most exchanges set the multiplier to 3 and the percentage to approximately 30 percent"); price scan range = maintenance margin for futures; inter-commodity credits, intra-commodity (inter-month) charge, short option minimum; S&P 500 futures array of 12 April 2001 with maintenance margin $17,250 (5750 / 11500 / 17250 / 15525) | CFTC, Review of SPAN Margin System, April 2001 (pdftotext) | https://www.cftc.gov/sites/default/files/files/tm/tmspan_margining043001.pdf | 2026-09-18 | table "Futures Contract Risk Array: All S&P 500 Futures Contracts" | section 2; ex:m1:margin:array; met span; build tests |
| F2 | March 2020: initial margin requirements for centrally cleared markets rose by roughly $300bn; peak CCP variation margin call $140bn on 9 March 2020; six areas of further work incl. transparency, liquidity preparedness, responsiveness of IM models | BCBS-CPMI-IOSCO press release, 29 Sept 2022 | https://www.bis.org/press/p220929.htm | 2026-09-18 | "increased by roughly $300 billion over March 2020"; "the peak CCP variation margin call was $140 billion on 9 March 2020" | hook; section Procyclicality |
| F3 | Cohen and Tracol, "Market turbulence and soaring margins: lessons from two recent episodes", BIS Quarterly Review, March 2023 (27 Feb 2023) | BIS | https://www.bis.org/publ/qtrpdf/r_qt2303x.htm | 2026-09-18 | record | omsources |
| F4 | CME SPAN 2: historical VaR framework, minimum 10 years of data, volatility and correlation scaling, reporting by market / liquidity / concentration | CME Group SPAN 2 methodology page (search excerpt; site blocks fetching) | https://www.cmegroup.com/clearing/risk-management/span-overview/span-2-methodology.html | 2026-09-18 | "HVaR uses a minimum of 10-year historical data" | dat:m1:margin:models |
| F5 | Eurex Clearing Prisma: filtered historical scenarios plus stress period scenarios; liquidation groups with their own holding periods | Eurex Clearing Prisma page (search excerpt) | https://www.eurex.com/ec-en/services/margining/eurex-clearing-prisma | 2026-09-18 | "filtered historical scenarios, stress period scenarios" | dat:m1:margin:models |

## EXCLUDED

- Actual E-mini margin levels in March 2020 (roughly a doubling): not verified; the weekend problem says "the numbers are invented, in the proportions of a violent month".
- LME nickel, March 2022 (margin calls, suspension, cancelled trades): left to chapter 31, which needs its own sources.
- Current SPAN extreme-move parameters (secondary sources give 2 ranges at 35%); the chapter uses the 2001 review's 3 ranges at 30% and says parameters belong to the clearing house.
- Margin period of risk values by product class ("a day or two for listed futures, longer for swaps"): regulatory minima (EMIR: 2 days ETD, 5 days OTC) not fetched; wording kept qualitative.
- Black (1976) reference: JFE 3, 167-179; bibliographic detail from memory, standard.

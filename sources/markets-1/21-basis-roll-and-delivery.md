# 21. Basis, Roll and Delivery — brief and source ledger

## Brief

- **Hook.** The future trades eleven points above the index, and that is exactly right.
- **Sections.** Cost of carry; Fair value and index arbitrage; The roll; Delivery and final settlement; Off-book mechanisms.
- **Defines.** basis, cost of carry, fair value, implied financing rate, roll, contango, backwardation, cash settlement, physical delivery, special opening quotation, exchange for physical, basis trade at index close, trade at settlement.
- **Tutorial.** Fair value of an index future with discrete dividends; implied financing rate.
- **Build.** Fair-value calculator.
- **Weekend problem.** Rolling a billion — named result: the cost of the roll in basis points per year.
- **Facts to verify.** CME SOQ procedure; BTIC, TAS, EFP rule references; WTI April 2020 settlement price and TAS role (CFTC report); quarterly roll dates.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | WTI May 2020 contract: settled at -$37.63 on 20 April 2020, the penultimate trading day (expiry 21 April); session began at $17.73; traded below zero from about 2:08 p.m. ET to the end of the settlement period at 2:30 p.m.; first negative price since the contract's inception in 1983; intraday low -$40.32; all other expirations settled positive; factors cited: oversupply, COVID-19 demand reduction, storage concerns; TAS a trade type in crude since 2001; outright TAS 20.9% of all traded sides of the May contract on 20 April (Table 1) | CFTC Interim Staff Report, Nov 2020 (pdftotext) | https://www.cftc.gov/media/5296/InterimStaffReportNYMEX_WTICrudeOil/download | 2026-09-18 | "recorded an all-time intraday trading low price of -$40.32 per barrel before a final settlement of -$37.63" | hook; ex:m1:basis-roll-and-delivery:wti; def tas; iq 5 |
| F2 | E-mini S&P 500: trading in expiring futures terminates at the regularly scheduled start of trading on the NYSE on the day of final settlement; final settlement = special opening quotation on the third Friday from opening prices of component stocks | CME Rulebook Chapter 358, rules 35802.G and 35803.A, as filed with the CFTC (pdftotext) | https://www.cftc.gov/filings/orgrules/rule030416cmedcm003.pdf | 2026-09-18 | "Trading in expiring futures shall terminate at the regularly scheduled start of trading on the New York Stock Exchange" | def soq; dat:m1:basis-roll-and-delivery:ends |
| F3 | FESX: trading ends 12:00 CET on the third Friday; final settlement = average of the index 11:50-12:00 | Eurex product page | https://www.eurex.com/ex-en/markets/idx/stx/euro-stoxx-50-derivatives/products/EURO-STOXX-50-Index-Futures-160088 | 2026-09-18 | see chapter 18 ledger F3 | dat ends |
| F4 | EFP: "a transaction in which the buyer of a cash commodity transfers to the seller a corresponding amount of long futures contracts, or receives from the seller a corresponding amount of short futures, at a price difference" | CFTC Futures Glossary | https://www.cftc.gov/LearnAndProtect/EducationCenter/CFTCGlossary/glossary_e.html | 2026-09-18 | search excerpt of the glossary entry | def efp |
| F5 | BTIC: buyer and seller agree a basis to be added to that day's official closing index level to determine the futures price | CME Group BTIC pages (search excerpt; site blocks fetching) | https://www.cmegroup.com/trading/equity-index/btic-transactions.html | 2026-09-18 | "transacted at a price equal to the closing index level plus the agreed-upon spread" | def tas |
| F6 | WTI: physical delivery at Cushing, Oklahoma | see chapter 18 ledger F7 | https://www.cmegroup.com/rulebook/NYMEX/2/200.pdf | 2026-09-18 | search excerpt | dat ends |

## EXCLUDED

- The exact WTI last-trading-day rule ("third business day prior to the 25th calendar day"): not fetched; the dated box says "some days before the delivery month begins".
- Typical roll dates (eight trading days before expiry for US equity index futures): convention, not sourced; chapter 18's figure says "centred here eight trading days before expiry" as an illustration.
- Historical richness of the S&P roll and year-end spikes: CME articles unfetchable (see chapter 17 EXCLUDED); statements kept qualitative.
- Size of expiry-morning opening auctions: qualitative statement only.
- Convenience yield literature (Kaldor, Working): not cited.

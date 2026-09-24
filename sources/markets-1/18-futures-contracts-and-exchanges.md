# 18. Futures Contracts and Their Exchanges — brief and source ledger

## Brief

- **Hook.** One E-mini contract controls a quarter of a million dollars of stock for a few thousand dollars of margin.
- **Sections.** The contract; The exchange groups; Specifications: multiplier, tick, months; Sessions, settlement and limits; Who trades futures.
- **Defines.** futures contract, contract multiplier, tick value, expiry month code, daily settlement price, open interest, price limit (futures), front month, hedger, speculator.
- **Tutorial.** A contract-spec table and notional, tick value and leverage for ten contracts.
- **Build.** Contract master (reference data).
- **Weekend problem.** Sizing a hedge — named result: the number of contracts and the residual exposure.
- **Facts to verify.** CME ES, NQ, ZN, CL specs; Eurex FESX, FGBL specs; ICE Brent spec; CME price limit/circuit breaker rules; volumes by exchange (FIA).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ES: unit $50.00 times the index; minimum increment 0.25 = $12.50; calendar spreads 0.05 = $2.50; cash settlement to a special opening quotation on the third Friday; price limits 7% / 13% / 20% (and 5% overnight in this filing) | CME Rulebook Chapters 351 and 358 as filed with the CFTC, March 2016 (pdftotext) | https://www.cftc.gov/filings/orgrules/rule030416cmedcm003.pdf | 2026-09-18 | "The unit of trading shall be $50.00 times the Index"; "0.25 Index points, equal to $12.50 per contract" | table; dat:m1:futures-contracts-and-exchanges:specs; dat:m1:futures-contracts-and-exchanges:limits; hook |
| F2 | ES daily settlement: VWAP of lead-month Globex trades 14:59:30-15:00:00 CT; tier 2 bid/ask midpoint; other months from spreads | CME equity index daily settlement procedures as filed with the CFTC, Jan 2018 (pdftotext) | https://www.cftc.gov/sites/default/files/filings/orgrules/18/01/rule012618cmedcm002.pdf | 2026-09-18 | "trades on Globex between 14:59:30 and 15:00:00 Central Time" | dat:m1:futures-contracts-and-exchanges:limits |
| F3 | FESX: EUR 10 per point; minimum price change 1 = EUR 10; twelve nearest quarterly months; last trading day third Friday, 12:00 CET; final settlement = average of index 11:50-12:00 CET; trading 02:10-22:00 CET | Eurex product page | https://www.eurex.com/ex-en/markets/idx/stx/euro-stoxx-50-derivatives/products/EURO-STOXX-50-Index-Futures-160088 | 2026-09-18 | quoted | table; dat specs; exo 3 |
| F4 | FGBL: notional 6% coupon, 8.5 to 10.5 years; EUR 100,000; tick 0.01% = EUR 10; physical delivery | Eurex Euro-Bund Futures page (search excerpt of the page; the direct URL tried returned 404) | https://www.eurex.com/ex-en/markets/int/long-term-interest-rates/fix/government-bonds/Euro-Bund-Futures-137298 | 2026-09-18 | "Contract Size: EUR 100,000"; "0.01 percent, equivalent to a value of EUR 10" | table; dat specs |
| F5 | ZN: face value $100,000; tick one-half of 1/32 = $15.625; deliverable notes with remaining maturity of at least 6y6m and less than 8 years | CBOT Chapter 19 (search excerpt) and CBOT filing with the CFTC of 21 Feb 2025 (pdftotext) | https://www.cftc.gov/filings/orgrules/rules02212515871.pdf | 2026-09-18 | "U.S. Treasury Note Futures (6 1/2 to 8-Year)"; "a remaining term to maturity of not less than 6 years 6 months and less than 8 years" | table; dat specs |
| F6 | Brent: 1,000 barrels; $0.01 per barrel; up to 156 consecutive months; trading ceases last business day of the second month preceding the contract month; EFP delivery with option to cash settle against the ICE Brent Index | ICE product page | https://www.ice.com/products/219/Brent-Crude-Futures | 2026-09-18 | quoted | table; dat specs |
| F7 | CL: 1,000 US barrels; delivery at Cushing, Oklahoma | NYMEX Rulebook Chapter 200 (search excerpt; cmegroup.com blocks fetching) | https://www.cmegroup.com/rulebook/NYMEX/2/200.pdf | 2026-09-18 | "The unit of trading shall be 1,000 U.S. barrels (42,000 U.S. gallons)" | table; dat specs |
| F8 | Open interest: "The total of all futures and/or option contracts entered into and not yet offset by a transaction, by delivery, by exercise, etc."; commercial = uses futures for hedging as defined in CFTC Regulation 1.3 | CFTC COT Explanatory Notes | https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm | 2026-09-18 | quoted | def oi; def hedger |
| F9 | CL: 1,000 barrels; minimum fluctuation $0.01 per barrel = $10 a contract | KGI Futures (clearing member) contract-specification page reproducing the NYMEX specification; NYMEX Rulebook ch. 200 (search extract, PDF not fetchable) | https://www.kgieworld.sg/futures/cme-nymex-wti-crude-contractspecs | 2026-09-19 | "Minimum Price Fluctuation: $0.01 per barrel" | contract table |

## EXCLUDED

- CL minimum fluctuation $0.01 = $10: Chapter 200's text could not be fetched (cmegroup.com returns JSON error pages to scripts); printed in the table on the strength of the contract's universal quotation in cents and the identical ICE Brent rule. FLAG for a human check against the CME page. RESOLVED 2026-09-19: see F9 (secondary source).
- ES trading hours ("Sunday evening to Friday afternoon"): broker pages in search results only.
- Month codes F..Z: industry convention, no page fetched.
- The overnight ES price limit: 5% in the 2016 filing; later changes not verified. The dated box says so explicitly.
- FIA volume rankings by exchange, and the names of the exchange groups: the section describes the groups without naming them or giving volumes.
- NQ, micro contracts and their multipliers: not verified; the figure uses "a contract one tenth the size" without naming it.
- Initial margin levels: volatile and broker-dependent; every margin number in the chapter is a stated assumption.

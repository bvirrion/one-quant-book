# 22. Equity Index and Single-Stock Futures Worldwide — brief and source ledger

## Brief

- **Hook.** The most traded equity index contract in the world is not American.
- **Sections.** The main index contracts by region; Dividend futures; Total return futures; Single-stock futures; Trading hours and the global relay.
- **Defines.** dividend future, total return future, single-stock future, index point, mini contract, micro contract.
- **Tutorial.** Implied dividends from index futures and dividend futures.
- **Build.** Global contract calendar.
- **Weekend problem.** The dividend curve — named result: the implied dividend growth.
- **Facts to verify.** FIA volume rankings (Nifty, Bank Nifty, Kospi); Eurex dividend futures, TRF specs; SGX/HKEX contract specs; single-stock futures venues.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | 2025 global ETD volume 119.29bn contracts, down 42.2%; options 88.65bn (-50.3%); futures 30.64bn (+8.6%); equity 94,786,863,932 contracts (-48.8%); regions: Asia-Pacific 75.59bn (-55.6%), North America 24.50bn (+24.0%), Latin America 11.39bn (+14.2%), Europe 4.38bn (+5.4%), Other 3.43bn (+50.2%) | FIA, ETD Volume - December 2025 | https://www.fia.org/fia/articles/etd-volume-december-2025 | 2026-09-18 | quoted; the five regions sum to 119.29 (asserted in tests) | hook; dat:m1:index-and-single-stock-futures-worldwide:fia; fig regions; exo 8 |
| F2 | HSI futures: HK$50 per point; minimum fluctuation one point; spot, next three calendar months and next three quarter months plus long-dated June/December; hours 9:15-12:00, 13:00-16:30, 17:00-03:00; final settlement from quotations at five-minute intervals; last trading day the second last trading day of the contract month | HKEX contract summary | https://www.hkex.com.hk/Products/Listed-Derivatives/Equity-Index/Hang-Seng-Index-(HSI)/Hang-Seng-Index-Futures?sc_lang=en | 2026-09-18 | quoted | table; dat:m1:index-and-single-stock-futures-worldwide:hours; sessions_sample.csv |
| F3 | FESX specs and hours (02:10-22:00 CET) | Eurex product page | https://www.eurex.com/ex-en/markets/idx/stx/euro-stoxx-50-derivatives/products/EURO-STOXX-50-Index-Futures-160088 | 2026-09-18 | chapter 18 ledger F3 | table; dat hours; sessions_sample.csv |
| F4 | FEXD: EUR 100 per index dividend point; tick 0.1 = EUR 10; five nearest quarterly, next two semi-annual and eight following annual months; last trading day third Friday 12:00 CET; final settlement = cumulative total of relevant gross dividends of the constituents | Eurex product page | https://www.eurex.com/ex-en/markets/did/eqt-idx-div-fut/EURO-STOXX-50-Index-Dividend-Futures-946316 | 2026-09-18 | quoted | dat:m1:index-and-single-stock-futures-worldwide:fexd; exo 3; pb |
| F5 | TESX: EUR 10 per point; underlyings SX5E, SX5EDD distribution index and EUR STR; quoted as annualised TRF spread in bp with one decimal, minimum change 0.5 bp; accrued distributions and funding added to the price, daily changes via variation margin; funding rate EUR STR flat after transition from EUR STR + 8.5 bp; 21 nearest quarterly months and five following annual Decembers (up to 9y11m) | Eurex TESX product page and circular (search excerpts) | https://www.eurex.com/ex-en/markets/idx/trf/trf-products/EURO-STOXX-50-Index-Total-Return-Futures-253698 | 2026-09-18 | quoted excerpt; https://www.eurex.com/ex-en/find/circulars/circular-2755938 | dat:m1:index-and-single-stock-futures-worldwide:tesx |
| F6 | Eurex offers single-stock futures and options on 1,200+ underlyings from 20+ countries | Eurex equity derivatives page (search excerpt) | https://www.eurex.com/ex-en/markets/equ | 2026-09-18 | "SSFs and Options on 1,200+ underlyings from 20+ countries" | section SSF |
| F7 | OneChicago withdrew its registration as a national securities exchange for security futures (order of Feb 2021); last trading day 18 Sept 2020 | Federal Register, 18 Feb 2021 | https://www.federalregister.gov/documents/2021/02/18/2021-03218/self-regulatory-organizations-onechicago-llc-order-granting-onechicago-llcs-request-to-withdraw-from | 2026-09-18 | title of the order; trading end date from John Lothian News (secondary) | section SSF |
| F8 | ES specs | chapter 18 ledger F1 | https://www.cftc.gov/filings/orgrules/rule030416cmedcm003.pdf | 2026-09-18 | see there | table |

## EXCLUDED

- The brief's hook ("the most traded equity index contract is not American") and any contract-level ranking (Nifty, Bank Nifty, KOSPI 200): FIA's contract rankings were not fetched; the hook now uses the verified regional totals.
- The reason for the 2025 fall (Indian regulator's changes to index option lot sizes and weekly expiries): widely reported but not in the FIA page fetched; the dated box says only "their regulators' decisions about contract sizes and expiries" without naming a country.
- Nikkei 225 (JPX 403), KOSPI 200, Nifty, SGX A50 specifications: not verified, not printed. The "three regional benchmarks" table has Hong Kong as its Asian row for that reason.
- ES trading hours: an assumption in sessions_sample.csv, flagged in the file, the figure caption and the build box.
- NSE single-stock futures volumes: secondary sources only; the text says they "trade actively in India".
- Size of the structured-products dividend supply and the historical discount of the strip: qualitative.

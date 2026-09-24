# 6. Bond Futures — brief and source ledger

## Brief

- **Hook.** A futures contract on a ten-year note that does not exist: the short chooses which of a dozen real bonds to deliver, and the market prices the choice.
- **Sections.** The contract and its basket; Conversion factors and invoice price; Cheapest-to-deliver; Gross basis, net basis and implied repo; The delivery options.
- **Defines.** deliverable basket, conversion factor, invoice price, cheapest-to-deliver, gross basis, net basis, implied repo rate, quality option, wildcard option, basis trade.
- **Uses (defined earlier).** futures contract, cost of carry, physical delivery, implied financing rate, repo rate, dirty price, accrued interest.
- **Tutorial.** Compute conversion factors, gross and net basis and implied repo across a synthetic basket, and identify the CTD.
- **Build.** `firm.ctd`: CTD and basis analyser.
- **Weekend problem.** The switch — named result: the yield level at which the cheapest-to-deliver switches, and the value of the switch option.
- **Facts to verify.** CBOT TY / ZN contract spec (6% notional coupon, deliverable maturities, tick 1/2 of 1/32); Eurex Bund future spec (6% coupon, 8.5-10.5y); delivery process timeline (CBOT); hedge-fund Treasury basis trade size (Fed notes / OFR).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CBOT U.S. Treasury Note Futures (6 1/2 to 8-Year), code ZN: contract grade = Treasury notes with an original term to maturity of not more than 10 years and a remaining term of not less than 6 years 6 months and less than 8 years; from the March 2026 contract month, reopened securities may be added to the deliverable grade (CBOT Submission 25-099, effective 10 March 2025) | CBOT filing with the CFTC, 21 Feb 2025 (pdftotext) | https://www.cftc.gov/filings/orgrules/rules02212515871.pdf | 2026-09-23 | "a remaining term to maturity of not less than 6 years 6 months and less than 8 years" | def basket; dat:m2:bond-futures:contracts |
| F2 | ZN face value USD 100,000; minimum tick one-half of 1/32 = USD 15.625 | Book 1 ledger, chapter 18, F5 (same filing and CBOT Chapter 19) | https://www.cftc.gov/filings/orgrules/rules02212515871.pdf | 2026-09-18 | see Book 1 | dat:m2:bond-futures:contracts; exo |
| F3 | Euro-Bund future (FGBL): notional 6% coupon, deliverable remaining maturity 8.5 to 10.5 years, EUR 100,000 | Book 1 ledger, chapter 18, F4 (Eurex page) | https://www.eurex.com/ex-en/markets/int/long-term-interest-rates/fix/government-bonds/Euro-Bund-Futures-137298 | 2026-09-18 | see Book 1 | dat:m2:bond-futures:contracts |
| F4 | Conversion factor = approximate price of USD 1 par at a 6% yield; formula factor = a[(coupon/2) + c + d] - b with n whole years and z whole months from the first day of the delivery month, z rounded down to the quarter for the 10-year and bond contracts, to the month for 2-, 3-, 5-year; coupon rounded to the nearest 1/8 (ties up); worked examples 0.9229, 0.8747, 0.8653, 0.8357, 0.7943; invoice price = futures settlement price x conversion factor + accrued interest | CME Group, Calculating U.S. Treasury Futures Conversion Factors (copy hosted by rateslib; cmegroup.com not fetchable) | https://rateslib.com/py/en/latest/_downloads/e2668f383e50d915a487b8a20e599ccc/us-treasury-cfs.pdf | 2026-09-23 | "A conversion factor is the approximate decimal price at which $1 par of a security would trade if it had a six percent yield-to-maturity" | def cf; build tests; tutorial |
| F5 | Last trading day of the 10-year note and bond futures: seventh business day preceding the last business day of the delivery month; last delivery day: last business day of the month; wild card option: bonds can be selected after the futures price is fixed, daily between the end of futures trading and the end of bond trading, and for up to seven days after the last trade | OpenGamma Quantitative Research, M. Henrard, "Bond Futures: Description and Pricing" (2011) | https://quant.opengamma.io/Bond-Futures-OpenGamma.pdf | 2026-09-23 | "The last trading day is the Seventh business day preceding the last business day of the delivery month" | def options; dat:m2:bond-futures:contracts; fig timeline |
| F6 | Aggregate Treasury cash-futures basis trade volumes about USD 830 billion in September 2025, roughly double the early-2020 peak; 3.5% of privately held Treasuries by market value; 35% of hedge funds' long Treasury exposures | Federal Reserve, FEDS Notes, "Decomposing Hedge Funds' U.S. Treasury Exposures", 22 June 2026 | https://www.federalreserve.gov/econres/notes/feds-notes/decomposing-hedge-funds-u-s-treasury-exposures-20260622.html | 2026-09-23 | "aggregate basis trade volumes reached approximately $830 billion in September 2025" | dat:m2:bond-futures:basis |
| F7 | Hedge funds' cash Treasury holdings USD 2 trillion at year-end 2025, nearly three times five years earlier; published estimates of the basis trade range from USD 350 billion to 1.5 trillion; hedge funds' short futures positions USD 1.4 trillion in Q4 2025 | OFR blog, "Hedge Funds' Cash Treasury Holdings Reach $2 Trillion", 19 Aug 2026 | https://www.financialresearch.gov/the-ofr-blog/2026/08/19/hedge-funds-cash-treasury-holdings/ | 2026-09-23 | "estimated the size of the trade to be from $350 billion to $1.5 trillion" | dat:m2:bond-futures:basis |

## EXCLUDED

- Current CBOT times of the daily wild-card window (futures close and notice deadline): only the 2011 description (F5) was found; the text describes the window without clock times.
- Role of the basis trade in March 2020 (unwinds by hedge funds): the FSB review (chapter 4 F11) mentions leveraged non-bank sales generally; the chapter does not attribute March 2020 moves to the basis trade specifically.
- The deliverable basket, yields and futures price of the chapter are synthetic; real conversion factors are published by the exchange.


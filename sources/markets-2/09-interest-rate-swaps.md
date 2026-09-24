# 9. Interest-Rate Swaps — brief and source ledger

## Brief

- **Hook.** A company borrows at a floating rate and wants to sleep at night; a bank quotes it a fixed rate for ten years on a phone line, and hedges within the minute.
- **Sections.** The swap and its legs; Overnight index swaps and conventions; Pricing, par rates and risk; Swap spreads; Execution facilities and compression.
- **Defines.** interest-rate swap, fixed leg, floating leg, payer swap, receiver swap, overnight index swap, par swap rate, annuity, swap spread, swap execution facility, trade compression.
- **Uses (defined earlier).** notional, discount yield, DV01, compounding in arrears, overnight benchmark rate.
- **Tutorial.** Bootstrap a single OIS curve from par rates, reprice the inputs, and compute bucketed DV01 of a ten-year swap.
- **Build.** `firm.curve`: OIS curve bootstrap and swap pricer.
- **Weekend problem.** The corporate hedge — named result: the fixed rate and the DV01 of the ten-year hedge, and its P&L under a steepening.
- **Facts to verify.** swap conventions USD SOFR OIS (annual, ACT/360); BIS OTC derivatives statistics (IRS notional outstanding); negative 30y swap spreads (US, since 2008); CFTC SEF rule / made-available-to-trade; compression volume (TriOptima/LCH public).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | USD SOFR fixed-float OIS: annual payments on both legs, actual/360; floating leg pays compounded SOFR in arrears with a payment delay of two US Government Securities business days; legs start accruing two business days after trade (T+2 spot) | Clarus Financial Technology, "SOFR Swap Nuances" (secondary; market-data vendor) | https://www.clarusft.com/sofr-swap-nuances/ | 2026-09-23 | search excerpt: "trades with annual payments on each side, calculated using an Act/360 DCC" | dat:m2:interest-rate-swaps:conventions |
| F2 | OTC derivatives notional outstanding USD 846 trillion at end-June 2025 (+16% y/y, the largest rise since 2008); interest rate derivatives 79% of notional (about USD 668 trillion), +15% y/y; gross market value USD 21.8 trillion; euro-denominated IRD notional above dollar-denominated since 2022; latest BIS release (published 8 Dec 2025) | BIS, OTC derivatives statistics at end-June 2025 | https://www.bis.org/publ/otc_hy2512.htm | 2026-09-23 | "$846 trillion at June 2025, up 16%"; "79% of all OTC derivatives' notional amounts" | dat:m2:interest-rate-swaps:market |
| F3 | 30-year US swap spreads have been negative since September 2008, shortly after Lehman's default; before 2008 swap rates had always been above like-maturity government yields; explanations: pension demand for duration and dealer balance-sheet constraints | S. Klingler and S. Sundaresan, "An Explanation of Negative Swap Spreads: Demand for Duration from Underfunded Pension Plans" (SSRN 2814975; Journal of Finance 2019) | https://www.ssrn.com/abstract=2814975 | 2026-09-23 | search excerpt: "30-year U.S. swap spreads have been negative since September 2008" | §4; iq 4 |
| F4 | CFTC final rule on SEF obligations published 5 June 2013 (registration by 2 Oct 2013); certain interest rate swaps and credit default index swaps determined available to trade and required to be executed on a SEF from 15 Feb 2014 | SEC filing (Teucrium Commodity Trust 10-Q 2014, describing the CFTC rules; secondary) | https://www.sec.gov/Archives/edgar/data/0001471824/000089109214008431/e61236_10q.htm | 2026-09-23 | search excerpt: "beginning on February 15, 2014 certain interest rate swaps and credit default index swaps must be executed on a SEF" | def SEF; dat:m2:interest-rate-swaps:market |

## EXCLUDED

- Compression volumes (LCH SwapClear, triReduce): only search excerpts of old or promotional figures were found; the text defines compression without volumes.
- Current level of the 30-year swap spread: not fetched; the text says only that it has been negative since 2008.
- The par curve of the chapter is illustrative.
- ISDA SOFR fallback / conventions for other currencies (ESTR, SONIA OIS): not fetched; the conventions box covers USD only.


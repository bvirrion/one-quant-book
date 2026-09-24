# 11. Inflation Derivatives — brief and source ledger

## Brief

- **Hook.** In October 2022 UK retail price inflation reached 14.2 per cent; pension funds that had bought caps on their inflation-linked liabilities found out what the caps were worth.
- **Sections.** The foreign-currency analogy; Zero-coupon versus year-on-year; The year-on-year convexity adjustment; Seasonality in the model; Inflation options and limited price indexation.
- **Defines.** Jarrow--Yildirim model, year-on-year inflation swap, year-on-year convexity adjustment, inflation cap, limited price indexation.
- **Uses (defined earlier).** zero-coupon inflation swap (B2.11), index-linked bond (B2.11), real yield (B2.11), breakeven inflation rate (B2.11), indexation lag (B2.11), inflation seasonality (B2.11), deflation floor (B2.11), reference index (B2.11), liability-driven investment (B2.7), quanto adjustment (B5.17), Hull--White model (ch7), timing adjustment (ch6).
- **Tutorial.** Estimate monthly seasonal factors from US CPI (public data), then price a year-on-year swap and caplets under Jarrow--Yildirim and show the effect of the nominal-real correlation.
- **Build.** `firm.inflopt`: year-on-year swaps, inflation caps and floors, limited-price-indexation legs; reuses `firm.breakeven`.
- **Weekend problem.** The pension fund's LPI swap — named result: the value of a 0-5 per cent limited-price-indexation leg against the uncapped leg, and its volatility sensitivity.
- **Facts to verify.** UK RPI 14.2% October 2022 (ONS); RPI reform to CPIH methods from 2030 (UKSA/HM Treasury 2020); Jarrow and Yildirim 2003 (paper); US CPI NSA series (BLS/FRED, public domain); LPI market (public).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | UK RPI annual inflation was 14.2% in October 2022; CPI rose 11.1% and CPIH 9.6% in the 12 months to October 2022 | ONS, Consumer price inflation, UK: October 2022 | https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/consumerpriceinflation/october2022 | 2026-09-24 | "The annual RPI inflation rate was 14.2% in October 2022." | hook, problem |
| F2 | The government and the UK Statistics Authority decided (25 November 2020) to align RPI with CPIH methods and data, not before February 2030 (after the last specific index-linked gilt maturing in 2030) | HM Treasury and UKSA, response to the consultation on the reform to RPI methodology, 25 November 2020 | https://www.gov.uk/government/consultations/a-consultation-on-the-reform-to-retail-prices-index-rpi-methodology | 2026-09-24 | "The change proposed can legally and practically be made by UKSA in February 2030." | dat:rc:inflation-derivatives:uk |
| F3 | UK statutory pension increases (limited price indexation): default cap 5% for pensions attributable to service before the commencement day (6 April 2005) and 2.5% for service after it | Pensions Act 1995, section 51 (as amended) | https://www.legislation.gov.uk/ukpga/1995/26/section/51 | 2026-09-24 | categories X (5%) and Y (2.5%) by pensionable service before or after the commencement day | def:rc:inflation-derivatives:lpi, dat:rc:inflation-derivatives:uk, problem |
| F4 | Jarrow and Yildirim (2003) price TIPS and inflation options in an HJM framework with nominal and real curves | R. Jarrow and Y. Yildirim, "Pricing Treasury Inflation Protected Securities and related derivatives using an HJM model", Journal of Financial and Quantitative Analysis 38(2), 337-358, 2003 | https://econpapers.repec.org/article/cupjfinqa/v_3a38_3ay_3a2003_3ai_3a02_3ap_3a337-358_5f00.htm | 2026-09-24 | bibliographic record and abstract | def:rc:inflation-derivatives:jy, omsources |
| F5 | US CPI-U, all items, NSA, January 2010 to August 2026 (Book 2's data file, FRED CPIAUCNS from BLS; no October 2025 value) | BLS via FRED (Book 2, data/markets-2/cpi_us_monthly.csv) | https://fred.stlouisfed.org/series/CPIAUCNS | 2026-09-23 | as recorded in Book 2's LICENSES.md; public domain | fig:rc:inflation-derivatives:seasonal |

## EXCLUDED

- Sterling nominal and RPI swap curves and the model parameters are illustrative. The UK LPI swap market size: not sourced (web search budget exhausted); the text describes the product only. Re-searched 2026-09-24: no public figure for the LPI swap market (volumes are not published; only pension-fund and trade-press anecdotes found); still excluded. Curves and parameters illustrative by design.


# 12. Mortgage Modelling — brief and source ledger

## Brief

- **Hook.** In the summer of 2003 ten-year Treasury yields rose by more than a percentage point in six weeks, and much of the move was mortgage investors selling duration to hedge the negative convexity of their own portfolios.
- **Sections.** Anatomy of a prepayment model; Rate paths and path dependence; The option-adjusted spread in practice; Hedging negative convexity; Model risk in prepayment.
- **Defines.** prepayment model, refinancing incentive, prepayment S-curve, burnout, housing turnover, option cost, current coupon, primary--secondary spread, interest-only strip, principal-only strip.
- **Uses (defined earlier).** prepayment (B2.12), conditional prepayment rate (B2.12), PSA benchmark (B2.12), agency mortgage-backed security (B2.12), pass-through (B2.12), to-be-announced trade (B2.12), effective duration (B2.12), negative convexity (B2.12), option-adjusted spread (B2.21), Z-spread (B2.21), Monte Carlo (B4.26), Hull--White model (ch7).
- **Tutorial.** Compute the option-adjusted spread, effective duration and convexity of a pass-through on Hull--White paths with a refinancing S-curve and burnout; split its value into interest-only and principal-only strips.
- **Build.** `firm.mbsoas`: path-wise prepayment model and OAS engine on `firm.prepay` and `firm.shortrate`.
- **Weekend problem.** The convexity event of 2003 — named result: the notional of ten-year swaps a mortgage portfolio must pay to stay duration-neutral after a 100 basis-point rise, and the feedback it creates.
- **Facts to verify.** summer 2003 Treasury sell-off (FRED data); Fed research on mortgage convexity hedging (Perli-Sack 2003; Hanson 2014); agency MBS outstanding (SIFMA, dated); primary-secondary spread in 2020 (NY Fed staff report).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | The 10-year Treasury par yield was 3.13% on 13 June 2003 (its low of May-September 2003) and 4.61% on 2 September 2003 (the subsequent high) | US Treasury, Daily Treasury Par Yield Curve Rates, 2003 (CSV) | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2003 | 2026-09-24 | daily CSV for 2003, column "10 Yr": minimum 3.13 on 06/13/2003, later maximum 4.61 on 09/02/2003 | hook, problem |
| F2 | Perli and Sack (Federal Reserve, FEDS 2003-49) find that ten-year swap-rate volatility rises when mortgage prepayment risk is high, consistent with hedging amplifying rate moves, with effects expected to persist for several months | R. Perli and B. Sack, "Does Mortgage Hedging Amplify Movements in Long-term Interest Rates?", FEDS 2003-49, Federal Reserve Board | https://www.federalreserve.gov/pubs/feds/2003/200349/200349abs.html | 2026-09-24 | abstract: amplification effects "are generally expected to persist only for several months" | hook, sec. 12.4, omsources |
| F3 | Federal Reserve outright holdings of MBS (H.4.1, WSHOMCB): zero before 2009, peak USD 2,717.9bn on 23 Feb 2022, USD 1,913.6bn on 26 Aug 2026 | Federal Reserve H.4.1 via FRED, series WSHOMCB (Book 2 data file data/markets-2/fed_mbs_monthly.csv, downloaded 2026-09-23) | https://fred.stlouisfed.org/series/WSHOMCB | 2026-09-23 | values in the data file; computed maximum and last value | fig:rc:mortgage-modelling:fed, dat:rc:mortgage-modelling:holders |
| F4 | Agency MBS trading 2026 year to date through August: USD 367.0bn average daily volume | SIFMA, US Mortgage-Backed Securities Statistics (same row as Book 2, ch. 12, F5) | https://www.sifma.org/research/statistics/us-mortgage-backed-securities-statistics | 2026-09-23 | "Agency Trading $367.0 billion ADV" | dat:rc:mortgage-modelling:holders |
| F5 | In 2020 the rise in the mortgage-Treasury spread is more than accounted for by the primary-secondary spread (a markup in the primary market); regressions on demand proxies show the primary-secondary spread 73 bp higher than expected in March-April 2020 and 81 bp higher in May-September | A. Fuster, A. Hizmo, L. Lambie-Hanson, J. Vickery, P. S. Willen, "How resilient is mortgage credit supply? Evidence from the COVID-19 pandemic", NBER Working Paper 28843 | https://www.nber.org/system/files/working_papers/w28843/w28843.pdf | 2026-09-24 | "the primary-secondary spread is 73bp higher than expected in March and April 2020, and 81bp higher than expected in May through September" | primary-secondary definition, sources |

## EXCLUDED

- The 2020 primary-secondary spread: restored 2026-09-24 → F5 (NBER working paper). Agency MBS outstanding (SIFMA): re-searched 2026-09-24; SIFMA's page gives issuance and trading only (outstanding sits in a spreadsheet not retrieved), so no outstanding figure is printed; the dated box keeps SIFMA's trading volume. The pool, prepayment parameters and curve are illustrative by design.


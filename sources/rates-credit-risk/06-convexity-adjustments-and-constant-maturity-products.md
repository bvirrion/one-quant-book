# 6. Convexity Adjustments and Constant-Maturity Products — brief and source ledger

## Brief

- **Hook.** A note pays each year the ten-year swap rate observed that day; the forward swap rate is 4 per cent, and the dealer's fair value of the coupon is 4.3.
- **Sections.** Paying a rate at the wrong time: timing adjustments; Constant-maturity swaps and their replication by swaptions; The linear terminal swap-rate model; Quanto adjustments in rates; CMS spread options.
- **Defines.** timing adjustment, constant-maturity swap, CMS convexity adjustment, linear terminal swap-rate model, CMS spread option.
- **Uses (defined earlier).** convexity adjustment (B2.8), swaption (B2.13), volatility cube (B2.13), steepener (B2.31), annuity measure (B4.5), forward measure (B4.5), quanto adjustment (B5.17), shifted SABR (ch5), swaption matrix (ch5).
- **Tutorial.** Replicate a CMS swaplet and a CMS caplet with a strip of swaptions priced on the cube, and compare with the Hagan closed-form approximation across strikes.
- **Build.** `firm.cms`: CMS replication pricer on `firm.sabrcube`; timing and quanto adjustments.
- **Weekend problem.** The steepener note — named result: the fair participation of a ten-year-minus-two-year CMS spread note and its sensitivity to the correlation between the two rates.
- **Facts to verify.** Hagan 2003 'Convexity conundrums' (paper); CMS steepener note issuance and 2008 losses (public sources only); Andersen and Piterbarg 2010 (textbook).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Hagan developed the standard replication framework for CMS swaps, caps and floors (linear and other annuity mappings) | P. S. Hagan, "Convexity conundrums: pricing CMS swaps, caps, and floors", Wilmott Magazine, March 2003, 38-44 | https://www.researchgate.net/publication/240133238_Convexity_Conundrums_Pricing_CMS_Swaps_Caps_and_Floors | 2026-09-24 | bibliographic record | sec. 6.2-6.3, omsources |
| F2 | Daily changes of US Treasury 2-year and 10-year par yields, 2016-01-04 to 2026-09-23, have a correlation of 0.769 | US Treasury, Daily Treasury Par Yield Curve Rates (chapter 3 data file) | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve | 2026-09-24 | computed by the chapter's code from data/rates-credit-risk/treasury_par_yields.csv | problem, fig:rc:convexity-adjustments-and-constant-maturity-products:steep |

## EXCLUDED

- CMS steepener note issuance and 2008 losses: no public source fetched; the chapter's problem is illustrative and names no issuer. Re-searched 2026-09-24: only trade press (dealer estimates) and law-firm marketing, no regulatory or court record; still excluded.
- Curves and smiles are chapters 2 and 5's illustrative curves and synthetic cube; the 2y/10y correlation is a Treasury proxy for swap-rate correlation. Re-checked 2026-09-24: illustrative by design.


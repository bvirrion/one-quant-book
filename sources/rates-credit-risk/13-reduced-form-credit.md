# 13. Reduced-Form Credit — brief and source ledger

## Brief

- **Hook.** On 8 April 2009 the whole North American CDS market switched overnight to fixed coupons of 100 and 500 basis points and to one open-source model to convert quoted spreads into upfront cash.
- **Sections.** Default as the first jump of an intensity; Pricing the legs of a default swap; Bootstrapping a hazard curve; The standard model and its conventions; Credit risk measures: CS01 and jump to default.
- **Defines.** reduced-form model, probability of default, loss given default, risky discount factor, risky annuity, credit triangle, ISDA standard model, CS01, jump-to-default risk, default risk premium.
- **Uses (defined earlier).** hazard rate (B2.23), survival probability (B2.23), credit default swap (B2.23), standard coupon (B2.23), upfront payment (B2.23), credit event (B2.23), recovery rate (B2.21), credit spread (B2.21), credit rating (B2.21), Poisson process (B4.6), Cox process (B4.7), discount curve (ch2).
- **Tutorial.** Bootstrap a piecewise-constant hazard curve from a CDS term structure, convert spreads to upfronts and back, and compute bucketed CS01 and jump to default.
- **Build.** `firm.cdscurve`: hazard-curve bootstrap with standard-model conventions, CS01 and jump to default; imports `firm.cds` (flat hazard, Book 2).
- **Weekend problem.** The negative basis package — named result: the CS01 and jump-to-default of a long bond plus bought protection, and the recovery at which the package breaks even.
- **Facts to verify.** CDS Big Bang 8 April 2009, standard coupons (ISDA); European Small Bang June 2009 coupons; ISDA CDS Standard Model (open source, administrator); physical versus risk-neutral default probabilities (Hull, Predescu, White 2005); rating-agency default studies (public).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Big Bang Protocol effective 8 April 2009: North American CDS on investment-grade names trade with a fixed 100 bp coupon, high-yield names with 500 bp, with upfront payments; auction settlement hardwired; determinations committees | Paul, Weiss, "The Big Bang Protocol and a New Structural Framework for Credit Default Swaps", client memo, 24 March 2009 (same source as Book 2, ch. 23, F3) | https://www.paulweiss.com/media/hzjjrf1e/24mar09cds.pdf | 2026-09-23 | "CDS on investment grade Reference Entities will stipulate a fixed coupon of 100 basis points ... High-yield Reference Entities will trade on a fixed 500 basis points spread and be quoted in up-front points." | hook, dat:rc:reduced-form-credit:standard |
| F2 | The ISDA CDS Standard Model is source code for CDS calculations, copyright ISDA under an open-source licence, administered by S&P Global Market Intelligence; used so that participants match upfront amounts and translate upfront and spread quotes the same way | ISDA CDS Standard Model website | https://www.cdsmodel.com/ | 2026-09-24 | "a source code for CDS calculations and can be downloaded freely"; "available under an Open Source license"; SPGMI "administrator for this open source project"; "translate upfront quotations to spread quotations and vice versa in a standardized manner" | def:rc:reduced-form-credit:isda, dat:rc:reduced-form-credit:standard |
| F3 | Hull, Predescu and White (2005), Table 1: average seven-year real-world and risk-neutral default intensities (bp per year), Dec 1996-Jul 2004, real-world from Moody's 1970-2003 cumulative default rates, risk-neutral from Merrill Lynch index yields over the seven-year swap rate minus 10 bp with 40% recovery: ratios Aaa 16.8, Aa 13.0, A 9.8, Baa 5.1, Ba 2.1, B 1.2, Caa and lower 1.3 | J. Hull, M. Predescu and A. White, "Bond prices, default probabilities and risk premiums", Journal of Credit Risk 1(2), 2005, 53-60 (authors' PDF) | http://www-2.rotman.utoronto.ca/~hull/DownloadablePublications/CreditSpreads.pdf | 2026-09-24 | Table 1 rows "Aaa 4 67 16.8 63"; "A 13 128 9.8 115"; "Baa 47 238 5.1 191"; "Ba 240 507 2.1 267"; "B 749 902 1.2 153"; "the ratio of the risk-neutral to real-world default intensity decreases as the credit quality declines" | which-PD remark, sources |

## EXCLUDED

- Hull, Predescu and White (2005) and rating-agency default studies: restored 2026-09-24 → F3 (the paper's Table 1, which rests on Moody's default studies); the chapter's own example keeps an illustrative physical probability. The CDS curve, bond price and recovery are illustrative by design.


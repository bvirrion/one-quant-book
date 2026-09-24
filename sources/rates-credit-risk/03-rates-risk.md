# 3. Rates Risk — brief and source ledger

## Brief

- **Hook.** A swap book with zero parallel DV01 loses three million dollars on a day when two-year rates fell eight basis points and thirty-year rates rose six.
- **Sections.** Bucketed sensitivities and risk ladders; From par risk to zero risk: the Jacobian; Principal components of the curve; Hedging a swap book; Gamma and cross-gamma.
- **Defines.** bucketed sensitivity, risk ladder, key-rate duration, curve Jacobian, level factor, slope factor, curvature factor, cross-gamma.
- **Uses (defined earlier).** DV01 (B2.3), convexity (B2.3), par swap rate (B2.9), steepener (B2.31), flattener (B2.31), curve fly (B2.31), principal component analysis (B4.22), shrinkage (B4.22), bump-and-reprice (B5.4), pillar (ch1), curve calibration (ch1).
- **Tutorial.** Compute the par-rate risk ladder of a 200-swap book, map it to zero-rate risk through the Jacobian, run a PCA on daily US Treasury par-yield changes, and find the three-swap hedge that minimises residual variance.
- **Build.** `firm.ratesrisk`: risk ladders, Jacobian transforms, PCA of curve moves, minimum-variance hedge solver.
- **Weekend problem.** The twisted Tuesday — named result: the loss of a DV01-flat book explained by the first three components, and the three-swap hedge that removes 95 per cent of its variance.
- **Facts to verify.** US Treasury daily par yield curve (treasury.gov, public domain); Litterman and Scheinkman 1991: share of variance of level, slope, curvature; day of the hook: a real twist day from the Treasury data.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Daily US Treasury par yield curve rates, 4 January 2016 to 23 September 2026 (2,682 days; 1, 2, 3, 5, 7, 10, 20, 30 years), downloaded year by year as CSV; on 21 October 2022 the par yields changed by -8, -13, -14, -11, -8, -3, +7, +9 bp (1Y to 30Y); on 10 April 2025 by -6, -7, -6, -2, +1, +6, +12, +14 bp | US Treasury, Daily Treasury Par Yield Curve Rates | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve | 2026-09-24 | CSV endpoint daily-treasury-rates.csv/<year>/all?type=daily_treasury_yield_curve; file data/rates-credit-risk/treasury_par_yields.csv | hook, sec. 3.3, fig:rc:rates-risk:pca, fig:rc:rates-risk:pnl, problem |
| F2 | Works of the US Government are not subject to copyright (17 U.S.C. section 105) | Legal Information Institute, 17 U.S. Code 105 | https://www.law.cornell.edu/uscode/text/17/105 | 2026-09-24 | "Copyright protection under this title is not available for any work of the United States Government" | data/rates-credit-risk/LICENSES.md |
| F3 | Litterman and Scheinkman identified three common factors of bond returns (level, steepness, curvature) | R. Litterman and J. Scheinkman, "Common Factors Affecting Bond Returns", Journal of Fixed Income 1(1), 54-61, 1991 | https://jfi.pm-research.com/content/1/1/54 | 2026-09-24 | bibliographic record | def:rc:rates-risk:factors, omsources |
| F4 | Ho introduced key rate durations to measure non-parallel risk | T. S. Y. Ho, "Key Rate Durations: Measures of Interest Rate Risks", Journal of Fixed Income 2(2), 29-44, 1992 | https://www.pm-research.com/content/iijfixinc/2/2/29 | 2026-09-24 | bibliographic record | def:rc:rates-risk:krd, omsources |

## EXCLUDED

- The SOFR swap curve and the 200-swap book are illustrative; Treasury par-yield changes stand in for swap-rate changes (swap-spread moves ignored), as the text says. Re-checked 2026-09-24: illustrative by design.


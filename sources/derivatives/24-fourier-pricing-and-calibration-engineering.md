# 24. Fourier Pricing and Calibration Engineering — brief and source ledger

## Brief

- **Hook.** Every morning at seven a job fits a Heston model to 600 quotes; one Tuesday the volatility of volatility jumped from 0.6 to 1.4 with the fit error unchanged, and every exotic on the book moved.
- **Sections.** Pricing by transform; Calibration as a pipeline; Objective, weights and constraints; Stability from day to day; Testing a calibration.
- **Defines.** Carr--Madan formula, Lewis formula, vega weighting, recalibration P\&L.
- **Uses (defined earlier).** fast Fourier transform, COS method (Book 4 ch. 28), characteristic function (Book 4 ch. 1), Levenberg--Marquardt, regularisation (Book 4 ch. 16, 24), calibration (Book 4 ch. 24), Heston model (ch. 10), Bates model, variance gamma model (ch. 13).
- **Tutorial.** Price a full Heston strike grid by the Carr-Madan FFT and by the COS method, then run a daily calibration over 60 synthetic days with and without a penalty on parameter changes and plot the parameter paths.
- **Build.** `firm.calib`: calibration pipeline (quote filter, weights, bounded Levenberg-Marquardt with regularisation, warm start, diagnostics, parameter-jump alarms) for any model with a characteristic function.
- **Weekend problem.** The Tuesday jump — named result: the regularisation weight at which the day-to-day moves of the volatility of volatility fall below 0.1 while the fit error rises by less than 0.1 volatility point.
- **Facts to verify.** Carr-Madan 1999 J. Computational Finance; Lewis 2001 (Fourier pricing); Fang-Oosterlee 2008 COS method; Cont-Ben Hamida 2005 ill-posed calibration; Mikhailov-Nögel 2003 Heston calibration.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Carr and Madan, "Option valuation using the fast Fourier transform", Journal of Computational Finance 2(4) (1999) 61-73 | Crossref record 10.21314/JCF.1999.043 | https://api.crossref.org/works/10.21314/JCF.1999.043 | 2026-09-24 | Crossref metadata | def Carr-Madan formula, omsources |
| F2 | Lewis, "A simple option formula for general jump-diffusion and other exponential Levy processes" (2001): option value as a single integral in Fourier space, read as a Parseval identity; one integration for any payoff; applies to any European payoff under any Levy process with a known characteristic function | SSRN record with abstract, 10.2139/ssrn.282110 | https://api.crossref.org/works/10.2139/ssrn.282110 | 2026-09-24 | abstract in Crossref | def Lewis formula, omsources |
| F3 | Fang and Oosterlee, "A novel pricing method for European options based on Fourier-cosine series expansions", SIAM Journal on Scientific Computing 31(2) (2008) 826-848: the COS method; series coefficients of the density from the characteristic function; convergence exponential in most cases, cost linear | Crossref record with abstract, 10.1137/080718061 | https://api.crossref.org/works/10.1137/080718061 | 2026-09-24 | abstract in Crossref | sec. pricing by transform, omsources |
| F4 | Cont and Ben Hamida, "Recovering volatility from option prices by evolutionary optimization", Journal of Computational Finance 8(4) (2005) 43-76; working-paper abstract: the in-sample pricing error can have multiple global minima; the spread of a sample of calibrated models quantifies the ill-posedness of the inverse problem | Crossref records 10.21314/JCF.2005.130 and (abstract) 10.2139/ssrn.546882 | https://api.crossref.org/works/10.2139/ssrn.546882 | 2026-09-24 | abstract in Crossref (SSRN version) | sec. stability, omsources |

## EXCLUDED

- Mikhailov and Nögel (2003), Heston calibration in Wilmott magazine: no fetchable record (Crossref search returned other papers); not cited.
- The hook's numbers come from the chapter's synthetic market, not from a real desk; no external fact.

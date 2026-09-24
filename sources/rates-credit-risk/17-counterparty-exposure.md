# 17. Counterparty Exposure — brief and source ledger

## Brief

- **Hook.** When Lehman Brothers filed on 15 September 2008 its counterparties had to replace hundreds of thousands of derivatives in a market moving against all of them at once.
- **Sections.** Exposure and its profiles; Netting and collateral; Simulating exposure; The margin period of risk and the collateralised profile; Wrong-way risk.
- **Defines.** counterparty credit risk, counterparty exposure, expected exposure, expected positive exposure, expected negative exposure, potential future exposure, netting set, close-out netting, collateral threshold, minimum transfer amount, independent amount, wrong-way risk.
- **Uses (defined earlier).** margin period of risk (B1.20), variation margin (B1.5), initial margin (B1.5), mark-to-market (B1.7), credit support annex (B2.10), ISDA master agreement (B2.28), payment netting (B2.20), settlement risk (B2.20), Monte Carlo (B4.26), Longstaff--Schwartz method (B5.23), Hull--White model (ch7), multi-curve framework (ch2).
- **Tutorial.** Simulate the exposure profiles of a ten-year swap, a cross-currency swap and their netting set, with and without variation margin under a ten-day margin period of risk.
- **Build.** `firm.exposure`: exposure simulation engine (scenario paths, trade revaluation, netting, collateral); Python driver with a C++20 kernel and a Rust twin.
- **Weekend problem.** The uncollateralised corporate — named result: the peak PFE and EPE of a swap-plus-FX-forward netting set, before and after the client signs a CSA.
- **Facts to verify.** Lehman derivative counterparties and trade count (bankruptcy filings); ISDA netting opinions coverage (ISDA); Basel margin period of risk floors (10 days, 20 for large netting sets); Gregory, The xVA Challenge (textbook).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Lehman initially asserted around 930,000 derivative transactions at the time of its bankruptcy; by 13 November 2008 most had been terminated; in January 2009 counsel reported 18,000 not terminated; by May 2010 banks had filed more than $50 billion of claims for derivatives losses | Financial Crisis Inquiry Commission, The Financial Crisis Inquiry Report (2011), notes to chapter 20, note 8 (citing Lehman debtors' motion of 13 Nov 2008, Docket 1498, and the Valukas examiner's report) | https://www.govinfo.gov/content/pkg/GPO-FCIC/pdf/GPO-FCIC.pdf | 2026-09-24 | "Lehman initially asserted that there were around 930,000 derivative transactions at the time of bankruptcy"; "in January 2009, Lehman's counsel reported that 18,000 derivatives contracts had not been terminated"; "as of May 2010, banks had filed more than $50 billion in claims for losses related to derivatives contracts with Lehman" | hook, dat:rc:counterparty-exposure:lehman |
| F2 | Minimum margin period of risk (SA-CCR): at least ten business days for non-centrally-cleared derivatives with daily margin; five for cleared client trades; 20 business days for netting sets of 5,000 transactions not with a CCP; doubled for netting sets with outstanding disputes; for margining every N days, MPoR = 10 + N - 1 | BCBS, The standardised approach for measuring counterparty credit risk exposures, March 2014 (rev. April 2014), BCBS 279, Annex 4 | https://www.bis.org/publications/201403-standards-standardised-approach-measuring-counterparty-credit-risk-exposures.pdf | 2026-09-24 | "At least ten business days for non-centrally-cleared derivative transactions subject to daily margin agreements"; "20 business days for netting sets consisting of 5,000 transactions that are not with a central counterparty"; "Doubling the margin period of risk for netting sets with outstanding disputes"; "for weekly re-margining ... MPOR = 10 + 5 - 1 = 14" | margin period of risk section, dat:rc:counterparty-exposure:mpor |
| F3 | ISDA netting opinions address the enforceability of the termination, bilateral close-out netting and multibranch netting provisions of the 1992 and 2002 Master Agreements; ISDA has published netting opinions covering over 90 jurisdictions and collateral opinions covering over 60; generally updated annually | ISDA, Opinions overview page | https://www.isda.org/opinions-overview/ | 2026-09-24 | "ISDA has published netting opinions covering over 90 jurisdictions and collateral opinions covering over 60 jurisdictions. The opinions are generally updated on an annual basis." | dat:rc:counterparty-exposure:opinions |
| F4 | J. Gregory, The xVA Challenge (4th edition), Wiley, 2020 | Crossref record for the book (DOI 10.1002/9781119508991) | https://doi.org/10.1002/9781119508991 | 2026-09-24 | Crossref: title "The xVA Challenge", author Jon Gregory, publisher Wiley, published 2020, ISBN 9781119508977 | sources |

## EXCLUDED

- ISDA netting opinions coverage (number of jurisdictions): restored 2026-09-24 → F3 (new dated box after the netting definition).
- Gregory, The xVA Challenge: restored 2026-09-24 → F4 (bibliographic record checked; listed in the sources).
- Curves, volatilities, trades and hazard model: illustrative by design.


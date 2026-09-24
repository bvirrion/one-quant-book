# 25. Loans, CLOs and Securitisation — brief and source ledger

## Brief

- **Hook.** At the end of 2025 American companies owed USD 1.55 trillion of institutional leveraged loans, up 9.2% in a year; the loans are pooled into vehicles that sell tranches of their cash flows, and a test written into each vehicle's documents decides when its equity stops being paid.
- **Sections.** The leveraged-loan market; Securitisation; The CLO waterfall and its tests; Who holds which tranche.
- **Defines.** leveraged loan, term loan B, covenant-lite, securitisation, special-purpose vehicle, collateralised loan obligation, payment waterfall, overcollateralisation test, interest-coverage test, equity tranche.
- **Uses (defined earlier).** tranche, attachment point, seniority, credit rating.
- **Tutorial.** Run a CLO waterfall through a default wave and watch the OC test divert cash.
- **Build.** `firm.waterfall`: CLO waterfall engine.
- **Weekend problem.** The test that trips — named result: the default rate at which the equity tranche stops receiving cash.
- **Facts to verify.** US leveraged loan market size; CLO market size; CLO tranche structure typical; covenant-lite share; risk-retention rules.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Institutional leveraged loans outstanding USD 1,549bn at 2025:Q4, +9.2% on a year, 12.6% average annual growth since 2000 (PitchBook LCD); excludes bank commitments; share of new leveraged loans with debt/EBITDA of 4 or more above historical median; median ICR near historical low; default rate below median but defaults incl. distressed exchanges relatively high; securitisation bundles loans and sells claims on their cash flows through special purpose entities, less stringently regulated (risk retention) than banks; CLOs predominantly backed by leveraged loans | Federal Reserve Board, Financial Stability Report, May 2026, Table 1.1, section 2, box on securitisation | https://www.federalreserve.gov/publications/files/financial-stability-report-20260508.pdf | 2026-09-24 | "Leveraged loans 1,549 9.2 12.6" | hook; §1; §2; dat:m2:loans-clos-and-securitisation:size |
| F2 | CLO securities are issued by SPVs holding diversified portfolios of leveraged loans, funded by rated notes and unrated equity (tranches), actively managed by third-party managers; debt tranches receive principal and interest, subordinated tranches the residual after fees; US investors are typically banks, mutual funds, insurers, pension funds and hedge funds; issuers mainly in the Cayman Islands; CLOs grew from USD 264bn (2011) to USD 617bn (2018) (SIFMA) | Guse, Park, Saravay and Yook, "Collateralized Loan Obligations in the Financial Accounts of the United States", FEDS Notes, 20 September 2019 | https://www.federalreserve.gov/econres/notes/feds-notes/collateralized-loan-obligations-in-the-financial-accounts-of-the-united-states-20190920.html | 2026-09-24 | "Loans held in CLO issuers' portfolios are funded by the issuance of CLO securities, which are rated notes and unrated equity with varying degrees of credit risk, called "tranches," and are actively managed by third-party asset managers" | §2; §3; §4 |
| F3 | Payments follow "waterfall" instructions in the legal documents; the O/C ratio compares the par of the loan portfolio to the outstanding debt, tested on each payment date; a failure (from defaults, delinquencies, sales or excess CCC loans) diverts cash to repay senior tranches first; the I/C ratio requires interest from the pool to exceed interest due, with triggers | NAIC Capital Markets Bureau (J. Johnson), "Middle Market Collateralized Loan Obligations Primer", March 2025 | https://content.naic.org/sites/default/files/capital-markets-mm-clo-primer_0.pdf | 2026-09-24 | "When an O/C test "fails," the structure allows for cash flow diversion to accelerate repayment of the structure's senior debt tranches first" | §3; tutorial; problem |
| F4 | LSTA v. SEC, D.C. Circuit, 9 February 2018: risk retention rule under section 941 (5% of credit risk) vacated insofar as it applies to open-market CLO managers, who "neither originate the loans being securitized nor hold them as an asset at any point" | Chapman and Cutler, "DC Circuit Court of Appeals holds that open market CLO managers do not have to comply with Dodd-Frank risk retention requirements", client alert, February 2018 | https://www.chapman.com/publication-DC-Circuit-Risk-Retention-CLO-Managers | 2026-09-24 | "neither originate the loans being securitized nor hold them as an asset at any point" | §2 |

## EXCLUDED

- Current CLO market size (SIFMA, 2025-26) and covenant-lite share (PitchBook LCD): licensed or not fetched; only the Fed's 2011-2018 figures and the FSR's loan total are used.
- Typical CLO capital structure (AAA share, spreads): no public primary source fetched; the chapter's structure is labelled illustrative.
- European risk retention (EU Securitisation Regulation) details: not fetched; not stated.


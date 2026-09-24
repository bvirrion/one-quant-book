# 2. The Sell Side — brief and source ledger

## Brief

- **Hook.** A pension fund wants to sell 2 million shares before lunch and phones a bank.
- **Sections.** The markets division: sales, trading, structuring, research; Flow versus franchise; Prime services; Primary markets; What regulation did to the dealer.
- **Defines.** sell side, broker-dealer, flow trading, franchise, prime services, underwriting, risk-weighted assets, sales-trader, block trade.
- **Tutorial.** Price a risk bid for a block from spread, volatility and participation.
- **Build.** Block-pricing calculator (Python).
- **Weekend problem.** The risk bid — named result: the discount at which the desk breaks even with 95% confidence.
- **Facts to verify.** Volcker rule citation; Basel III / FRTB references; bank markets revenue split (public filings).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Goldman Sachs FY2025: firm net revenues $58,283m; Global Banking & Markets $41,453m; FICC $14,522m (intermediation $10,271m, financing $4,251m); Equities $16,535m (intermediation $9,340m, financing $7,195m); investment banking fees $9,339m (advisory $4,726m, equity underwriting $1,784m, debt underwriting $2,829m) | Goldman Sachs, Form 8-K, Full Year and Fourth Quarter 2025 Earnings Results | https://www.sec.gov/Archives/edgar/data/886982/000088698226000008/a4q25gsearningsresults.htm | 2026-09-18 | segment table of the release, figures as quoted | dat:m1:the-sell-side:gs; figure; exo 6 |
| F2 | Section 13 of the Bank Holding Company Act (Volcker rule) prohibits banking entities from proprietary trading; exemptions include government obligations, underwriting and market making-related activities, risk-mitigating hedging, trading on behalf of customers | FDIC, "Volcker Rule" | https://www.fdic.gov/capital-markets/volcker-rule | 2026-09-18 | "generally prohibits any banking entity from engaging in proprietary trading ..." | section 4 |
| F3 | Statutory wording "designed not to exceed the reasonably expected near term demands of clients, customers, or counterparties"; added by Dodd-Frank (2010) s.619 | 12 U.S.C. 1851(d)(1)(B), Legal Information Institute | https://www.law.cornell.edu/uscode/text/12/1851 | 2026-09-18 | text of (d)(1)(B) | section 4; pb q18 |
| F4 | Basel Committee market-risk standard "Minimum capital requirements for market risk", January 2019 | BCBS d457 | https://www.bis.org/bcbs/publ/d457.htm | 2026-09-18 | title and date of the standard | def RWA; omsources |

## EXCLUDED

- Typical size of real block discounts, and the share of variance an index hedge removes for a typical stock: no primary source; the chapter uses stated model parameters (kappa = 0.7, hedge ratio as an input) instead of empirical claims.
- Implementation dates of the Basel market-risk standard by jurisdiction: volatile and deferred several times; omitted.
- Banks' cost of equity 'around ten percent' and a 12% capital ratio are used as round illustrative inputs, flagged as such.

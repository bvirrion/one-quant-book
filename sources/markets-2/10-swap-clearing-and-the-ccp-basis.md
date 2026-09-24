# 10. Swap Clearing and the Clearing-House Basis — brief and source ledger

## Brief

- **Hook.** The same ten-year swap, with the same dates and the same rate, is worth two basis points more at one clearing house than at the other.
- **Sections.** The clearing mandate; The competing clearing houses; Initial margin, cleared and uncleared; Why the same swap has two prices.
- **Defines.** clearing mandate, client clearing, porting, uncleared margin rules, credit support annex, CCP basis.
- **Uses (defined earlier).** central counterparty, initial margin, variation margin, default fund, futures commission merchant, interest-rate swap, margin period of risk.
- **Tutorial.** Price the CCP basis from margin funding: simulate the initial-margin profile of a directional book at two clearing houses.
- **Build.** `firm.ccpbasis`: margin-funding cost of a book at two CCPs.
- **Weekend problem.** The one-way book — named result: the basis at which moving the book is break-even.
- **Facts to verify.** G20 2009 Pittsburgh commitment; CFTC/EMIR clearing mandates; LCH SwapClear / CME cleared volumes (public); LCH–CME basis evidence (public articles); UMR phases and thresholds (BCBS-IOSCO); EMIR 3 active-account requirement.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | G20 Pittsburgh (Sept 2009): "All standardized OTC derivative contracts should be traded on exchanges or electronic trading platforms, where appropriate, and cleared through central counterparties by end-2012 at the latest"; non-centrally cleared contracts subject to higher capital requirements; reporting to trade repositories | G20 Leaders' Statement, Pittsburgh Summit, 25 Sept 2009 | https://www.g20.utoronto.ca/2009/2009communique0925.html | 2026-09-23 | quoted sentence | hook; §1 |
| F2 | CFTC first clearing requirement determination adopted 29 Nov 2012 (four classes of interest rate swaps, two of CDS indices); swap dealers, major swap participants and active private funds began clearing on 11 March 2013; later phases for other entities in 2013 | CFTC press releases 6429-12 and 6684-13; Federal Register 13 Dec 2012 | https://www.cftc.gov/PressRoom/PressReleases/6429-12 | 2026-09-23 | search excerpt: "On March 11, 2013, swap dealers, major swap participants, and private funds active in the swaps market began clearing" | §1; dat:m2:swap-clearing-and-the-ccp-basis:mandates |
| F3 | BCBS-IOSCO margin requirements for non-centrally cleared derivatives: final phase 1 Sept 2022 for entities with aggregate average notional above EUR 8 billion (after a one-year Covid extension); initial margin threshold EUR 50 million | BCBS-IOSCO statements (BIS press releases 5 March 2019, 3 April 2020) and framework | https://www.bis.org/press/p200403a.htm | 2026-09-23 | search excerpt: "entities with an aggregate average notional amount (AANA) ... greater than EUR 8 billion" | def UMR; dat:m2:swap-clearing-and-the-ccp-basis:mandates; exo 6 |
| F4 | EMIR 3 published 4 Dec 2024, in force 24 Dec 2024; active account requirement: EU counterparties subject to the clearing obligation and above the threshold must hold an active account at an authorised EU CCP and clear a representative number of trades, by 24 June 2025; in scope: euro and zloty interest rate derivatives and euro STIR (excluding options) | DLA Piper, "EMIR 3 Active Account Requirement", June 2025 (secondary; law firm) | https://www.dlapiper.com/en/insights/publications/2025/06/emir-3-active-account-requirement | 2026-09-23 | search excerpt: "entering into force on December 24, 2024" | dat:m2:swap-clearing-and-the-ccp-basis:mandates |
| F5 | CME-LCH basis: buy-side clients subject to the clearing mandate at CME are predominantly fixed payers, so dealers receive fixed at CME and hedge by paying fixed at LCH, posting two lots of margin; the basis is the margin valuation adjustment; example (2017): a USD 100 million 30-year swap costs about USD 726,545 of margin funding over its life, 1.3 bp at CME and 2.1 bp at LCH, 3.4 bp in total | Clarus Financial Technology, "CME-LCH Basis for Dummies", 28 June 2017 | https://www.clarusft.com/cme-lch-basis-for-dummies/ | 2026-09-23 | "if they did that trade (bank would receive fixed at CME), and at the same time chose to offload that same swap at LCH (by paying fixed at LCH)" | hook; §4; ex basis |

## EXCLUDED

- Cleared volumes by clearing house (LCH SwapClear, CME) for a recent period: only an LCH Q1 2025 dashboard was fetched (record USD 464 trillion registered in the quarter); not used, to avoid a stale single-CCP figure.
- The current level of the CME-LCH basis: not fetched; the text uses the 2017 example and the mechanism.
- EU clearing-obligation start dates under EMIR (2016 onward): not fetched.
- Initial-margin model parameters (7 bp a day, 5-day MPOR, 99%, 50 bp funding) are illustrative; real CCPs use historical-simulation VaR.


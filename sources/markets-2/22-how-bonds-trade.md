# 22. How Bonds Trade — brief and source ledger

## Brief

- **Hook.** A portfolio manager sends one request for quote covering 400 bonds; four dealers answer in eleven minutes with a single price.
- **Sections.** Request for quote; Trade reporting and transparency; All-to-all and portfolio trading; Bond ETFs as a liquidity layer; Algorithmic dealer pricing.
- **Defines.** request for quote, trade reporting, dissemination cap, all-to-all trading, portfolio trade, axe, composite price.
- **Uses (defined earlier).** exchange-traded fund, authorised participant, creation basket, dealer-to-client platform, net asset value.
- **Tutorial.** Simulate RFQ competition among dealers and measure winning-spread distribution versus number of dealers queried.
- **Build.** `firm.rfq`: RFQ auction simulator with composite pricing.
- **Weekend problem.** How many dealers? — named result: the number of dealers to query that minimises expected cost including information leakage.
- **Facts to verify.** TRACE start (2002) and dissemination caps ($5mm IG, $1mm HY); MarketAxess/Tradeweb e-trading share (public filings); portfolio trading growth (public); EU bond transparency / consolidated tape.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | TRACE introduced July 2002; consolidates transaction data for eligible corporate bonds (agency debentures since 1 Mar 2010); firms report within 15 minutes for corporate and agency bonds; data disseminated in real time as received; 144A trades disseminated from 30 Jun 2014; TBA disseminated since Nov 2012 | FINRA, "TRACE: The Source for Real-Time Bond Market Transaction Data" (overview) | https://www.finra.org/sites/default/files/TRACE_Overview.pdf | 2026-09-23 | "Introduced in July 2002, TRACE (Trade Reporting and Compliance Engine) consolidates transaction data for all eligible corporate bonds" | §2 |
| F2 | Dissemination introduced in four phases over three years, large highly rated bonds first; exact volumes disseminated for trades below USD 1 million (high yield) and USD 5 million (investment grade), larger ones shown as "1MM+" / "5MM+"; FINRA released a historical dataset with exact volumes in March 2010 | Asquith, Covert and Pathak, "The Effects of Mandatory Transparency in Financial Market Design: Evidence from the Corporate Bond Market", NBER WP 19417, online appendix | https://data.nber.org/data-appendix/w19417/Transparency_online_appendix.pdf | 2026-09-23 | "exact volumes were reported for trades less than 1MM for high-yield bonds and trades less than 5MM for investment grade bonds" | def dissemination cap; §2 |
| F3 | FINRA Regulatory Notice 22-12: from 15 May 2023, corporate bond trades that are part of a portfolio trade (between two parties, a basket of at least 10 unique issues, a single agreed price for the basket) must carry a TRACE modifier | FINRA Regulatory Notice 22-12 | https://www.finra.org/rules-guidance/notices/22-12 | 2026-09-23 | "a basket of corporate bonds of at least 10 unique issues" | def portfolio trade; §3 |
| F4 | In the first week of the flag (15-19 May 2023) portfolio trades were 5.2% of TRACE corporate notional transacted | ICE, "Early observations about the new Portfolio Trade Flag from FINRA TRACE", May 2023 | https://www.ice.com/insights/fixed-income-data/early-observations-about-the-new-portfolio-trade-flag-from-finra-trace | 2026-09-23 | "For the first week these were 5.2% of the notional transacted" | §3 |
| F5 | ESMA launched the selection of the EU consolidated tape provider for bonds on 3 Jan 2025 and on 3 Jul 2025 selected Ediphy (fairCT), to operate it for five years under ESMA's direct supervision after authorisation | ESMA news, "ESMA selects Ediphy (fairCT) to become the first Consolidated Tape Provider for bonds" | https://www.esma.europa.eu/press-news/esma-news/esma-selects-ediphy-fairct-become-first-consolidated-tape-provider-bonds | 2026-09-23 | "Ediphy (fairCT) would operate the CTP for bonds for a period of five years under ESMA's direct supervision" | dat:m2:how-bonds-trade:transparency |

## EXCLUDED

- Electronic trading shares of named platforms (MarketAxess, Tradeweb filings): not fetched; the text does not name platforms' shares.
- Brief hook (400 bonds, four dealers, eleven minutes): a scene; replaced by the TRACE portfolio-trade facts.
- Bond ETF volumes and creation/redemption statistics: not fetched; the ETF mechanism is described from Book 1.


# 4. Exchanges, Brokers and Venues — brief and source ledger

## Brief

- **Hook.** The New York Stock Exchange is a listed company's subsidiary that sells data, ports and cabinets as well as matching.
- **Sections.** What an exchange sells; Members, brokers and access; Direct and sponsored access; Alternative venues; The consolidated view.
- **Defines.** exchange, exchange member, broker, direct market access, sponsored access, alternative trading system, multilateral trading facility, market data feed, order.
- **Tutorial.** Read an exchange group's segment revenue and compute the share from data and connectivity.
- **Build.** Venue registry (static reference data for the firm).
- **Weekend problem.** Building an exchange — named result: the break-even traded value per day.
- **Facts to verify.** exchange groups' revenue segments (10-K); SEC Rule 15c3-5 market access; Reg ATS; MiFID II MTF/OTF definitions.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ICE FY2025: consolidated net revenues $9.9bn; Exchanges segment net revenues $5,411m = Energy 2,182; Ags and metals 233; Financials 608; Cash equities and equity options 467; OTC and other 395; Data and connectivity services 1,031; Listings 495 (recurring 1,526; transaction net 3,885) | ICE press release "Intercontinental Exchange Reports Strong Full Year 2025 Results", 5 Feb 2026 | https://ir.theice.com/press/news-details/2026/Intercontinental-Exchange-Reports-Strong-Full-Year-2025-Results/default.aspx | 2026-09-18 | segment table of the release | dat:m1:exchanges-brokers-venues:groups; figure; hook; exo 1 |
| F2 | CME Group FY2025: revenue $6.5bn; clearing and transaction fees $5,281.1m; market data and information services $803.1m; average rate per contract $0.696 | CME Group press release, 4 Feb 2026 | https://www.cmegroup.com/media-room/press-releases/2026/2/04/cme_group_inc_reportsfourthconsecutiveyearofrecordannualrevenuea.html | 2026-09-18 | figures as quoted in the release (search extract; page fetch timed out, figures cross-checked with the 8-K listing https://www.sec.gov/Archives/edgar/data/1156375/000115637526000009/cme-20251231.htm) | dat:m1:exchanges-brokers-venues:groups; ex rpc |
| F3 | SEC adopted Rule 15c3-5 on 3 Nov 2010; pre-trade controls under the broker-dealer's direct and exclusive control; effectively ends unfiltered ("naked") access | SEC press release 2010-210; Release 34-63241 | https://www.sec.gov/newsroom/press-releases/2010-210-sec-adopts-new-rule-preventing-unfiltered-market-access | 2026-09-18 | "SEC Adopts New Rule Preventing Unfiltered Market Access" | rem:m1:exchanges-brokers-venues:15c35 |
| F4 | Regulation ATS adopted December 1998; ATS definition in Rule 300(a) | 17 CFR 242.300 (LII) | https://www.law.cornell.edu/cfr/text/17/242.300 | 2026-09-18 | definition text | def ATS |
| F5 | MiFID II art. 4(1)(22) definition of MTF | Directive 2014/65/EU; ESMA Q&A on market structures | https://www.esma.europa.eu/sites/default/files/library/esma70-156-4225_mifid_ii_final_report_on_functioning_of_otf.pdf | 2026-09-18 | "multilateral system, operated by an investment firm or a market operator, which brings together multiple third-party buying and selling interests ... in accordance with non-discretionary rules" | def MTF |
| F6 | ISO 10383 MIC: four alphanumeric characters; operating and segment levels; XNYS = NYSE, XNAS = Nasdaq; list published monthly, free of charge | ISO 10383 Registration Authority | https://www.iso20022.org/market-identifier-codes | 2026-09-18 | registry page; examples corroborated https://en.wikipedia.org/wiki/Market_Identifier_Code | rem:m1:exchanges-brokers-venues:mic; build |

## EXCLUDED

- Real access charges of brokers and sponsored-access providers: not public; the chapter's four-model example is labelled illustrative.
- Notional of a specific index future at today's index level: volatile; replaced by 'several hundred thousand dollars'. Contract specs are Chapter 18's dated boxes.
- Total daily share volume of a real market for the break-even example: the example and the problem use stated hypothetical markets (10bn and 8bn shares a day).
- In data/markets-1/venues_sample.csv the XTKS/XJPX and ARCX/XNYS operating-MIC relations are from memory of the registry, not re-fetched row by row: the file is labelled a sample and the build's stretch goal reloads the authoritative list.

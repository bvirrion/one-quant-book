# 11. European Equity Market Structure — brief and source ledger

## Brief

- **Hook.** A French stock trades in Paris, in London, in a bank's own book and in an auction that lasts a tenth of a second.
- **Sections.** MiFID II and its venue types; Fragmentation without a tape; Systematic internalisers; Dark caps and periodic auctions; The closing auction; Tick-size regime.
- **Defines.** regulated market, systematic internaliser, organised trading facility, double volume cap, periodic auction, large-in-scale waiver, reference price waiver, consolidated tape provider, best execution.
- **Tutorial.** Build a European best bid and offer across venues and measure fragmentation (Herfindahl).
- **Build.** Fragmentation monitor.
- **Weekend problem.** Where did the volume go? — named result: market share shift after a dark cap.
- **Facts to verify.** MiFID II/MiFIR articles; ESMA DVC; MiFIR review 2024 (CTP, DVC to single cap); tick-size RTS 11; closing auction share statistics.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | MiFID II venue categories and definitions (regulated market, MTF, OTF, systematic internaliser); best execution "all sufficient steps" (art. 27); MiFID II/MiFIR applied from 3 January 2018; MiFID I from November 2007 | Directive 2014/65/EU, arts 4(1)(20)-(24), 27, 93 | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0065 | 2026-09-18 | definitions as paraphrased in the chapter; MTF wording cross-checked in ch. 4 row F5 | defs rm, si, bestex; section 1 |
| F2 | ESMA selected EuroCTP on 19 Dec 2025 as CTP for shares and ETFs; later authorised; five-year term under ESMA supervision; go-live set for 14 Sep 2026; transition period to 30 Sep 2026; free for retail investors, academics, civil society, regulators | ESMA press releases | https://www.esma.europa.eu/press-news/esma-news/esma-selects-euroctp-become-first-consolidated-tape-provider-shares-and-etfs | 2026-09-18 | "The tape is now set to go live on 14 September 2026 ... transition period until 30 September 2026"; https://www.esma.europa.eu/press-news/esma-news/esma-authorises-euroctp-consolidated-tape-provider-shares-and-exchange-traded | dat:m1:european-equity-market-structure:ctp; hook |
| F3 | Single volume cap: 7% of EU volume over 12 months under the reference price waiver; three-month suspension; first results published 9 Oct 2025, quarterly thereafter; DVC (4% venue / 8% EU) discontinued, system decommissioned Jan 2026 | ESMA, "ESMA prepares for switch toward single volume cap in October 2025"; ESMA DVC page | https://www.esma.europa.eu/press-news/esma-news/esma-prepares-switch-toward-single-volume-cap-october-2025 | 2026-09-18 | "limited to 7% of total EU trading volume over the previous 12 months"; https://www.esma.europa.eu/double-volume-cap-mechanism | def cap; dat:m1:european-equity-market-structure:svc |
| F4 | July 2026: on-exchange ADVT EUR 57.5bn; addressable EUR 80bn; CLOB 52.8%, closing auctions 24.3%, periodic auctions 10.4%, non-displayed 10.9%; SI ADVT EUR 14.3bn = 17.8% of addressable | Cboe, "Market Metrics That Matter: European Equities July Volume Briefing", 17 Aug 2026 | https://www.cboe.com/insights/posts/market-metrics-that-matter-european-equities-july-volume-briefing | 2026-09-18 | figures as fetched | hook; dat:m1:european-equity-market-structure:july; figure; exo 3 |
| F5 | RTS 11 = Commission Delegated Regulation (EU) 2017/588: tick size depends on price and on average daily number of transactions (liquidity bands) on the most relevant market; annual calculation applies from the first Monday of April (2023 amendment) | EUR-Lex / ESMA | https://www.esma.europa.eu/document/amendment-commission-delegated-regulation-eu-2017588-rts-11 | 2026-09-18 | "calibrated to the average daily number of transactions (ADNT) on the most liquid market"; "apply the first Monday of April of each year" | section 4; exo 6 |

## EXCLUDED

- Whether the EuroCTP tape actually went live on 14 September 2026 (four days before writing): only the scheduled date is sourced; the box says 'was set for'.
- Names, locations and market shares of individual pan-European platforms: omitted; only one operator's published statistics are used, attributed generically.
- The 2018 start and size of the periodic-auction boom after the first DVC suspensions: not fetched; stated without date or figures.
- The actual RTS 11 tick table values: not reproduced; the exercise uses a hypothetical band change.
- Behaviour of alternative venues during primary-exchange outages: stated as a tendency, no specific incident cited.
- The post-suspension migration split (45/25/20/10) in the problem and the simulation is an assumption, labelled illustrative.

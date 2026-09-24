# 13. Auctions — brief and source ledger

## Brief

- **Hook.** At 15:59:50 a tenth of the day's volume is waiting for a single price.
- **Sections.** Call auctions and the uncrossing rule; Opening and closing auctions; Imbalance information; Volatility auctions and IPOs; Why the close keeps growing.
- **Defines.** call auction, uncrossing price, indicative price, order imbalance, market-on-close order, limit-on-close order, volatility interruption, closing price.
- **Tutorial.** Implement the uncrossing algorithm with tie-break rules.
- **Build.** `firm.auction`: auction uncrosser (used by the Book 10 simulator).
- **Weekend problem.** The index rebalance close — named result: the uncrossing price and paired volume.
- **Facts to verify.** NYSE/Nasdaq closing-cross rules and cutoff times; Xetra/Euronext uncrossing rules; closing auction volume share.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | NYSE: MOC/LOC entry until 15:50; regulatory imbalance published at 15:50 for imbalances of at least 500 round lots; after 15:50 closing orders only on the contra side; imbalance information every second | NYSE Closing Process fact sheet; NYSE Data Insights (Apr 2020) | https://www.nyse.com/publicdocs/nyse/NYSE_Auctions_Closing_Process_Fact_Sheet.pdf | 2026-09-18 | "Market on Close (MOC) - Can be entered until 3:50 pm"; "imbalance of at least 500 round lots"; https://www.nyse.com/data-insights/offsetting-a-regulatory-closing-imbalance | dat:m1:auctions:us; exo 3 |
| F2 | Nasdaq Closing Cross: early imbalance dissemination from 15:50 every 5 s, every second from 15:55; MOC accepted until 15:55, LOC until 15:58, IO until 16:00 | Nasdaq Closing Cross FAQ; SEC Release 34-84454 | https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf | 2026-09-18 | "At 3:55 p.m. ET ... Nasdaq stops accepting MOC orders. LOC orders may be entered until 3:58 p.m."; https://www.sec.gov/files/rules/sro/nasdaq/2018/34-84454.pdf | dat:m1:auctions:us; exo 3 |
| F3 | Xetra: auction price = price with the most executable volume and the lowest surplus | Deutsche Boerse glossary "Auction principle"; Xetra market model | https://www.deutsche-boerse.com/dbg-en/about-us/contact/glossary/glossary-article/Auction-principle-243106 | 2026-09-18 | "the price with the most executable volume and the lowest surplus in the order book" | met rules; section 1 |
| F4 | Euronext: uncrossing maximises executable volume and minimises imbalance, respecting price/time priority | Euronext AVD page; Trading Manual | https://www.euronext.com/en/trading/trading-services/auction-volume-discovery-avd | 2026-09-18 | "maximizing executable volume and minimizing imbalance while respecting time/price priority" | met rules |

## EXCLUDED

- The closing auction's share of US volume: the NYSE research note fetched gives order-timing statistics only; no US share is printed (the European 24.3% from chapter 11 is cross-referenced instead).
- Exact tie-break rules beyond volume and surplus on each exchange: the chapter's rules 3 and 4 are presented as 'the usual logic', with a warning to follow each venue's rulebook.
- NYSE D-Order timing statistics from the November 2025 note: interesting but not used.

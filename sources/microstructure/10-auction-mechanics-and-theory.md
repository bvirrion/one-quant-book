# 10. Auction Mechanics and Theory — brief and source ledger

## Brief

- **Hook.** In the minutes before a closing auction the exchange publishes an indicative price and imbalance every few seconds, and much of the auction's volume arrives in its last seconds. Every participant watches the same numbers and decides when to show its hand.
- **Sections.** Uncrossing rules revisited; Indicative prices and imbalance publication; Cut-offs, collars and random ends; Strategic behaviour near the uncross; Frequent batch auctions.
- **Defines.** auction cut-off time, auction collar, random end, frequent batch auction.
- **Uses (defined earlier).** call auction (B1.13), uncrossing price (B1.13), indicative price (B1.13), order imbalance (B1.13), market-on-close order (B1.13), limit-on-close order (B1.13), closing price (B1.13), volatility interruption (B1.13), periodic auction (B1.11), uniform-price auction (B2.4), Bayes--Nash equilibrium (B4.29), bid shading (B4.29), Kyle model (ch4), informed trader (ch4), latency arbitrage (B11.9, forward).
- **Tutorial.** Run closing auctions in firm.exchsim (Book 1's firm.auction does the uncross) with a market-on-close imbalance, liquidity providers who respond to the published imbalance, and one strategic participant; draw the indicative price's path and the arrival of volume; compare a fixed end with a random end, and a continuous market with frequent batch auctions for a sniping race. Data: simulated; published auction rules.
- **Build.** `firm.auctionsim`: the auction phase that firm.exchsim runs (order acceptance by phase, indicative price and imbalance publication, cut-off rules, collars, random end, the uncross through Book 1's firm.auction) and a frequent-batch-auction mode; Python.
- **Weekend problem.** The last ten seconds -- named result: the gap between the indicative and the final price against the time to the uncross, and the gain from late submission under a fixed and a random end.
- **Facts to verify.** Nasdaq closing cross rules (dated); NYSE closing auction rules and imbalance publication (dated); LSE / Euronext random end of auction periods (dated); Budish, Cramton, Shim 2015 the high-frequency trading arms race: frequent batch auctions (QJE); Madhavan 1992 trading mechanisms in securities markets (JF); Bogousslavsky and Muravyev 2023 who trades at the close? (JFE or current venue); share of US volume in closing auctions (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | E. Budish, P. Cramton and J. Shim, "The high-frequency trading arms race: frequent batch auctions as a market design response", Quarterly Journal of Economics 130(4) (2015) 1547-1621: exchanges should use frequent batch auctions, uniform-price double auctions conducted, for example, every tenth of a second | Crossref record with abstract | https://doi.org/10.1093/qje/qjv027 | 2026-09-25 | "we argue that financial exchanges should use frequent batch auctions: uniform price double auctions conducted, for example, every tenth of a second" | §5, omsources |
| F2 | A. Madhavan, "Trading mechanisms in securities markets", Journal of Finance 47(2) (1992) 607-641: a periodic auction offers greater price efficiency and can function where continuous mechanisms fail, at the cost of continuity and higher information costs | Crossref record with abstract | https://doi.org/10.1111/j.1540-6261.1992.tb04403.x | 2026-09-25 | "While a periodic auction offers greater price efficiency and can function where continuous mechanisms fail, traders must sacrifice continuity and bear higher information costs." | §1, omsources |
| F3 | V. Bogousslavsky and D. Muravyev, "Who trades at the close? Implications for price discovery and liquidity", Journal of Financial Markets 66 (2023) 100852 | Crossref record | https://doi.org/10.1016/j.finmar.2023.100852 | 2026-09-25 | bibliographic record | §4, omsources |
| F4 | Nasdaq publishes closing cross net order imbalance information between 3:50 and 4:00 p.m. ET; imbalance-only close orders must be priced and execute only at or above (buy) / below (sell) the 4:00 p.m. bid (ask) | Nasdaq Trader, The Nasdaq Opening and Closing Crosses | https://www.nasdaqtrader.com/trader.aspx?id=openclose | 2026-09-25 | "Closing Cross Net Order Imbalance information between 3:50 and 4:00 p.m., ET"; "Must be priced (limit), no market IO orders. IO buy/sell orders only execute at or above/below the 4:00 p.m., ET, bid/ask." | dat:mx:auction-mechanics-and-theory:rules |
| F5 | On the London Stock Exchange each auction call and each extension is followed by a random period of up to 30 seconds | London Stock Exchange, Maintaining orderly markets: circuit breakers explained (March 2020) | https://docs.londonstockexchange.com/sites/default/files/documents/maintaining-orderly-markets.pdf | 2026-09-25 | "each auction and extension is followed by a random period of up to 30 seconds" | dat:mx:auction-mechanics-and-theory:rules |

## EXCLUDED

- NYSE closing auction rules and imbalance publication times: not fetched from a primary page; not quoted.
- Share of US volume in closing auctions: no primary source fetched; not quoted.
- Bogousslavsky and Muravyev's findings: cited by title only.
- All simulated statistics (indicative gaps, arrival of paired volume, closing-price moves of late orders, sniping rates) are computed on firm.exchsim with firm.auctionsim and tested.

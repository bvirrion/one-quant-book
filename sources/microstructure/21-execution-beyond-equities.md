# 21. Execution Beyond Equities — brief and source ledger

## Brief

- **Hook.** Buying the same amount of risk takes an order in an index future, a request for quote in bonds, a stream of last-look prices in currencies and a venue that never closes in crypto. The objective is the same shortfall; the market's rules change what the algorithm can do.
- **Sections.** Futures: one book, implied liquidity, rolls; FX: streams, last look and aggregation; Bonds: requests for quote and portfolio lists; Crypto: round the clock, rate limits and on-chain legs; One order, four markets.
- **Defines.** request for stream, risk transfer price, liquidity aggregator, firm liquidity.
- **Uses (defined earlier).** request for quote (B2.22), last look (B2.15), hold time (B2.15), reject rate (B2.15), streaming quote (B2.15), benchmark fix (B2.17), fixing window (B2.17), all-to-all trading (B2.22), electronic communication network (B2.14), calendar spread (B1.19), implied-in (B1.19), roll (B1.21), rate limit (B3.15), centralised exchange (B3.15), automated market maker (B3.20), slippage tolerance (B3.22), funding rate (B3.17), implementation-shortfall algorithm (ch16), mark-out (B2.15).
- **Tutorial.** Execute the same parent order through execution adapters: an FX order on an aggregator of last-look liquidity providers (Book 2's firm.lastlook) against firm liquidity; a futures roll through outright and calendar-spread books with implied prices (firm.exchsim with Book 1's firm.match); a bond by request for quote to n dealers (Book 2's firm.rfq); a crypto order across a rate-limited venue and an AMM leg (Book 3's firm.amm). Data: simulated.
- **Build.** `firm.xexec`: execution adapters per market type (RFQ, streaming last-look aggregator, futures with implied books, rate-limited crypto venue, AMM routing) behind firm.acexec's scheduler interface; Python.
- **Weekend problem.** One order, four markets -- named result: the all-in cost of the same risk transfer in futures, FX, bonds and crypto in the simulator, and the part of it each market's rule explains.
- **Facts to verify.** FX Global Code principle 17 (last look) as in Book 2; BIS Triennial Survey 2025: FX execution methods (dated); Hendershott and Madhavan 2015 click or call? auction versus search in the over-the-counter market (JF); Oomen 2017 last look (QF); public statistics of electronic bond trading platforms from filings (dated); CME implied-price functionality (as in Book 1 ch. 19).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | FX Global Code principle 17: participants employing last look should be transparent and provide disclosures; last look as a risk control, not for information gathering (as verified for Book 2, chapter 15, F2) | Global Foreign Exchange Committee, FX Global Code (updated December 2024) | https://www.globalfxc.org/uploads/fx_global.pdf | 2026-09-23 | "Market Participants employing last look should be transparent regarding its use and provide appropriate disclosures to Clients." | §2, omsources |
| F2 | R. Oomen, "Last look", Quantitative Finance 17(7) (2017) 1057-1070 | Crossref record | https://doi.org/10.1080/14697688.2016.1262545 | 2026-09-26 | bibliographic record (the chapter claims only that the paper analyses last look) | §2, omsources |
| F3 | T. Hendershott and A. Madhavan, "Click or call? Auction versus search in the over-the-counter market", Journal of Finance 70(1) (2015) 419-447: periodic one-sided electronic auctions are a viable source of liquidity even in inactively traded bonds | Crossref record with abstract | https://doi.org/10.1111/jofi.12164 | 2026-09-26 | "We show that periodic one-sided electronic auctions are a viable and important source of liquidity even in inactively traded instruments." | §3, omsources |
| F4 | CME implied orders: implied in and implied out; implied quantity never matches implied quantity; no legging risk (as verified for Book 1, chapter 19, F3) | CME Group Client Systems Wiki, CME Globex Matching Algorithms and Implied Orders | https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/Implied+Orders | 2026-09-18 | "Implied quantity will never match with implied quantity"; no legging risk | §1, omsources |
| F5 | BIS Triennial Survey (April 2025): electronic trading 59% of FX turnover, virtually unchanged; customers using indirect disclosed electronic trading could in theory transact on over 15 multi-dealer platforms | BIS Quarterly Review, December 2025, "The FX trade execution landscape through the prism of the 2025 BIS Triennial Survey" | https://www.bis.org/publ/qtrpdf/r_qt2512v.htm | 2026-09-26 | "electronic trading accounting for 59%"; "Customers who turn to indirect disclosed electronic trading could, in theory, transact on over 15 multi-dealer platforms." | dat:mx:execution-beyond-equities:bis, omsources |
| F6 | A large spot exchange's order limit of 100 orders per 10 seconds (the chapter does not name the venue) | Book 3, chapter 15, F2: the venue's live exchangeInfo endpoint, fetched 2026-09-24 | https://api.binance.com/api/v3/exchangeInfo | 2026-09-24 | "ORDERS 100 per 10 SECOND" (REQUEST_WEIGHT 6,000 per 1 MINUTE, ORDERS 200,000 per 1 DAY), as recorded in Book 3's ledger and firm.ratelimit.binance_like | §4 |

## EXCLUDED

- Public statistics of electronic bond trading platforms from filings (brief, dated): not used; the bond section is a mechanism study with stated
  assumptions, and no platform is named.
- The four markets' spreads, volatilities and volumes are assumptions of a realistic order of magnitude, stated as such in the chapter, not facts.
- The futures roll is priced on firm.match's top-of-book quotes with one extra level, not in firm.exchsim (whose engine has no implied matching); the
  build lists implied matching in the simulator as a stretch.
- All numbers are computed by mx_xexec and firm.xexec and tested.


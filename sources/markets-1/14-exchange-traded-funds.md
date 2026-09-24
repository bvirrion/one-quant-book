# 14. Exchange-Traded Funds — brief and source ledger

## Brief

- **Hook.** A fund's shares trade at 50.10 while the basket inside is worth 50.00; within seconds someone fixes that.
- **Sections.** Structure: fund, sponsor, authorised participant; Creation and redemption; NAV, intraday value, premium and discount; When the underlying is closed or illiquid; Leveraged and inverse ETFs.
- **Defines.** exchange-traded fund, authorised participant, creation unit, creation basket, net asset value, indicative NAV, premium, in-kind transfer, leveraged ETF, volatility decay.
- **Tutorial.** Arbitrage bands from basket spread, creation fee and financing.
- **Build.** ETF premium monitor.
- **Weekend problem.** The daily rebalance of a 3x fund — named result: notional to trade at the close after a 5% move.
- **Facts to verify.** Rule 6c-11; ETF AUM totals (ICI/ETFGI); March 2020 bond ETF discounts (BIS/Fed papers); leveraged ETF rebalance formula sources.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Global ETF industry assets reached a record $24.03tn at end August 2026 ($23.11tn at end July) | ETFGI press release, as reported by Markets Media | https://www.marketsmedia.com/global-etf-assets-top-24-trillion-for-first-time/ | 2026-09-18 | "assets invested in the global ETFs industry reached a new record of $24.03 trillion at the end of August" | hook; dat:m1:exchange-traded-funds:size |
| F2 | SEC Rule 6c-11 adopted 25 Sep 2019 (effective 23 Dec 2019): ETFs meeting conditions operate without exemptive order; daily portfolio transparency; custom baskets with written policies; leveraged/inverse ETFs excluded | SEC press release 2019-190 | https://www.sec.gov/newsroom/press-releases/2019-190 | 2026-09-18 | "custom baskets"; "daily portfolio transparency"; leveraged/inverse ETFs not eligible | dat:m1:exchange-traded-funds:size |
| F3 | March 2020: IG corporate bond ETFs closed about 365 bp below NAV (asset-weighted) on 12 and 19 March; LQD from a 2.8% discount on 20 March to a 2.9% premium on 23 March; interpretation: ETF prices led stale NAVs | Aramonte and Avalos, BIS Bulletin no. 6, 14 April 2020 | https://www.bis.org/publ/bisbull06.htm | 2026-09-18 | figures and text of the bulletin | ex:m1:exchange-traded-funds:march |
| F4 | Todorov, "The anatomy of bond ETF arbitrage", BIS Quarterly Review, March 2021, pp. 41-53 | BIS | https://www.bis.org/publ/qtrpdf/r_qt2103d.htm | 2026-09-18 | title page | omsources |
| F5 | Cheng and Madhavan, "The Dynamics of Leveraged and Inverse Exchange-Traded Funds", Journal of Investment Management, Q4 2009 | SSRN | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1539120 | 2026-09-18 | SSRN record | omsources; prop rebalance, prop decay (standard results, derived in the text) |
| F6 | Madhavan, Exchange-Traded Funds and the New Dynamics of Investing, Oxford University Press, 2016, ISBN 9780190279394 | OUP | https://global.oup.com/academic/product/exchange-traded-funds-and-the-new-dynamics-of-investing-9780190279394 | 2026-09-18 | catalogue page | omsources |
| F7 | US market-wide circuit breakers: 7% / 13% / 20% declines of the S&P 500; Level 3 halts trading for the remainder of the day | Investor.gov glossary | https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-market-circuit-breakers | 2026-09-18 | "A market decline that triggers a Level 3 circuit breaker, at any time during the trading day, will halt market-wide trading for the remainder of the trading day" | solution pb q17 |

## EXCLUDED

- "87 consecutive months of net inflows" (ETFGI): seen only in a search snippet, not re-verified; removed.
- Any named leveraged or volatility product that lost nearly all its value in a day (February 2018): not verified in this run; the solution states only the prospectus warning, generically.
- Typical creation-unit sizes and creation fees of named funds: not verified; exercises use round illustrative numbers.
- The share of ETF trading that reaches the primary market (often quoted near 10%): no primary source fetched; the text says only "most ETF trading never reaches the primary market".
- Basket-cost magnitudes (4 bp large-cap, 30 bp small/foreign): illustrative orders of magnitude, flagged as "take" / "can be" in the text.

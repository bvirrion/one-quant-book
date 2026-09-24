# 12. Asian and Emerging Equity Markets — brief and source ledger

## Brief

- **Hook.** In Shanghai a stock that rises ten percent simply stops; in Tokyo the tick depends on the price; in Mumbai the tax is charged per trade.
- **Sections.** Japan; Hong Kong and the Connect programmes; Mainland China; Korea and Taiwan; India; What changes for a trading firm.
- **Defines.** price limit, board lot, T+0 restriction, Stock Connect, qualified foreign investor, securities transaction tax, uptick rule, foreign ownership limit, stamp duty.
- **Tutorial.** Simulate returns truncated by price limits and measure the spill-over to the next day.
- **Build.** Market-rules table (limits, lots, ticks, taxes) as reference data.
- **Weekend problem.** Limit-up — named result: expected days locked at the limit.
- **Facts to verify.** SSE/SZSE 10% and 20% limits; TSE tick tables; HK stamp duty rate; India STT rates; Korea short-selling bans dates; Stock Connect quotas.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Mainland main board limit 10%; ChiNext and STAR 20%; STAR no limit in first five days; same-day selling forbidden (T+1 trading rule) | Tiingo China stock market guide; STAR Market (Wikipedia) | https://www.tiingo.com/blog/china-stock-market-guide/ | 2026-09-18 | "main board stock prices to move up to 10% daily ... ChiNext ... 20% ... rule against same-day resale"; https://en.wikipedia.org/wiki/Shanghai_Stock_Exchange_STAR_Market | dat:m1:asian-and-emerging-equity-markets:china |
| F2 | Revised A-share trading rules of the Shanghai, Shenzhen and Beijing exchanges effective 6 July 2026: main-board ST limit widened to 10%; after-hours fixed-price trading 15:05-15:30 extended to all A-shares and ETFs | BigGo Finance (several reports); MMLC Group | https://finance.biggo.com/news/3af3d5fa-4282-4076-9de9-cf8f6f4c5eef | 2026-09-18 | "Takes Effect July 6: Main Board ST Stock Limits Widened to 10%, After-Hours Trading Expanded"; https://mmlcgroup.com/china-exchange-rules-2026/ | dat:m1:asian-and-emerging-equity-markets:china |
| F3 | HK stamp duty 0.1% each for buyer and seller from 17 Nov 2023 (was 0.13%) | KPMG tax alert | https://kpmg.com/us/en/home/insights/2023/11/tnf-hong-kong-reduced-stamp-duty-rate-on-stock-transfers-effective-17-november-2023.html | 2026-09-18 | "reduced from 0.13% to 0.1% for both the buyer and the seller ... 17 November 2023" | dat:m1:asian-and-emerging-equity-markets:hk; taxes figure |
| F4 | HKEX board lot reform: from 40+ sizes to eight (1, 50, 100, 500, 1,000, 2,000, 5,000, 10,000), lower value floor and new ceiling, phased from July 2026; consultation 18 Dec 2025 to 12 Mar 2026 | Caproasia; Charltons | https://www.caproasia.com/2026/07/01/hong-kong-exchange-hkex-implements-changes-to-board-lot-units-in-2-phases-effective-2-7-26-for-securities-trading-1-reduce-board-lot-units-from-40-to-8-options-1-50-100-500-1000-2000-500/ | 2026-09-18 | headline as quoted; https://www.charltonslaw.com/hkex-consults-on-proposed-enhancements-to-hong-kongs-board-lot-framework/ | dat:m1:asian-and-emerging-equity-markets:hk |
| F5 | Northbound Stock Connect daily quota RMB 52bn for each of Shanghai and Shenzhen links; structure of the link | HKEX Stock Connect information booklet (Feb 2024); Hang Seng Bank | https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/Getting-Started/Information-Booklet-and-FAQ/StockConnectFeb2024.pdf | 2026-09-18 | "northbound daily quota is set at RMB 52 billion for each of ..." | dat china; figure |
| F6 | India STT: delivery 0.1% each side (unchanged); from 1 Apr 2026 futures 0.05% sell side (was 0.02%), options 0.15% of premium sell side (was 0.10%) | ClearTax; ICICI Direct | https://cleartax.in/s/securities-transaction-tax-stt | 2026-09-18 | "STT on futures rose from 0.02% to 0.05% ... options premium rose from 0.10% to 0.15%"; https://www.icicidirect.com/futures-and-options/articles/stt-changes-in-budget-2026-what-f-o-traders-need-to-know | dat:m1:asian-and-emerging-equity-markets:india; exo 3 |
| F7 | India: T+1 standard; optional T+0 for top 500 stocks | Bajaj Finserv; Citi "Navigating India's T+0" | https://www.citigroup.com/global/insights/navigating-india-t-0 | 2026-09-18 | "T+0 settlement is operational for the top 500 stocks ... on an optional basis" | dat india |
| F8 | Korea: short-selling ban from November 2023, lifted 31 March 2025 for all listed stocks, with a naked short-selling detection system | Korea.net (FSC press release); CNBC | https://www.korea.net/Government/Briefing-Room/Press-Releases/view?articleId=84220&insttCode=A260302&type=N | 2026-09-18 | "Stock Short Selling to be Fully Reinstated from March 31"; https://www.cnbc.com/2025/03/31/south-korea-ends-its-longest-short-selling-ban-in-history-after-systemic-reforms.html | ex korea |
| F9 | TSE: separate tick tables by index membership; sub-yen ticks for the most liquid constituents | JPX, Tick Size (trading rules of domestic stocks) | https://www.jpx.co.jp/english/equities/trading/domestic/07.html | 2026-09-18 | "The tick size applied to TOPIX 500 constituents ..." ; leaflet on sub-yen tick sizes | section Japan |

## EXCLUDED

- Taiwan: no rule fetched; the chapter title keeps 'Taiwan' out of the text entirely (section title is 'Japan, Korea and the uptick rule'). Flag for the user: the outline's summary lists Taiwan.
- Japan's daily price limits and the 100-share trading unit: the limits are not described; the 100-share unit is stated from JPX pages seen in search results, not a dedicated fetch.
- China's stamp duty rate and direction: not verified; China is left out of the tax chart.
- A/H dual listings and their non-fungibility: stated generically without figures; no premium level is quoted.
- Several China and India rows rest on secondary sources (financial press, broker explainers), not on the exchanges' own circulars, which were not retrievable in English; marked as such in the omsources.

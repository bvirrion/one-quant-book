# 29. A Map of All Markets — brief and source ledger

## Brief

- **Hook.** One page, every market of the first three books: from government bonds that trade hundreds of billions of dollars a day to weather contracts that trade a handful.
- **Sections.** Size; Structure; Hours; Participants; Dominant strategy types.
- **Defines.** turnover velocity, follow-the-sun trading.
- **Uses (defined earlier).** notional turnover, exchange, request for quote, central counterparty, automated market maker, centralised exchange, market maker, proprietary trading firm.
- **Tutorial.** Build the synoptic chart of daily turnover by market on a log scale from the ledger's figures, and the UTC timeline of trading hours.
- **Build.** `firm.marketmap`: registry of markets (size, hours in UTC, structure, clearing), with queries for what is open now and shift coverage; uses `firm.calendar` and `firm.venues`.
- **Weekend problem.** The round-the-clock desk — named result: the smallest number of shifts, and traders per shift, that cover the firm's chosen markets' hours with a stated overlap.
- **Facts to verify.** BIS Triennial Survey 2025 FX turnover; US Treasury daily volume (SIFMA or FINRA TRACE); equity turnover by region (WFE); exchange-traded derivatives volume (FIA annual); crypto spot and derivatives volumes (a dated public dataset); European power exchange volumes (EPEX and Nord Pool annual reports); LME volumes (LME annual); event-contract volumes (a dated public source).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | OTC FX turnover USD 9.6 trillion a day in April 2025 (net-net) | BIS Triennial Survey 2025 (Book 2 ledger, ch. 14 F1) | https://www.bis.org/statistics/rpfx25_fx.htm | 2026-09-24 | "USD 9.6 trillion a day in April 2025" | dat:m3:a-map-of-all-markets:sizes; fig sizes |
| F2 | US Treasuries: trading (through August 2026) $1,203.6 billion ADV, +12.4% Y/Y; outstanding (as of August) $31.8 trillion; US fixed income trading (through August) $1,659.2 billion | SIFMA, US Treasury Securities Statistics; US Fixed Income Securities Statistics | https://www.sifma.org/resources/research/statistics/us-treasury-securities-statistics/ | 2026-09-24 | "Trading (through August) $1,203.6 billion ADV, +12.4% Y/Y"; "Outstanding (as of August) $31.8 trillion" | dat:m3:a-map-of-all-markets:sizes; fig sizes; def velocity |
| F3 | 2025 global exchange-traded derivatives volume 119.29 billion contracts | FIA, ETD volume December 2025 (Book 1 ledger, ch. 22 F1) | https://www.fia.org/fia/articles/etd-volume-december-2025 | 2026-09-24 | "119.29bn contracts" | dat:m3:a-map-of-all-markets:sizes |
| F4 | Binance BTCUSDT 24-hour quote volume: perpetual 17,647,283,210 USDT, spot 1,898,760,568 USDT; perpetual open interest 96,462.544 BTC (24 Sep 2026 about 13:06 UTC); Deribit BTC-PERPETUAL 24-hour volume_usd 1,578,446,400 (about 11:13 UTC) | Binance public API (fapi/v1/ticker/24hr, api/v3/ticker/24hr, fapi/v1/openInterest); Deribit public API | https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT | 2026-09-24 | JSON quoteVolume and openInterest fields | dat:m3:a-map-of-all-markets:sizes; fig sizes |
| F5 | NYSE core trading session 9:30 a.m. to 4:00 p.m. ET | NYSE, Hours and calendars | https://www.nyse.com/markets/hours-calendars | 2026-09-24 | "Core Trading Session: 9:30 a.m. to 4:00 p.m. ET" | fig day; §3 |
| F6 | Fixed moments reused from this book: perpetual funding 00:00, 08:00, 16:00 UTC (ch. 17 F1); crypto options expiry 08:00 UTC (ch. 19 F5); SDAC day-ahead auction at 12:00 CET (ch. 5 ledger); LME official prices published 12:20-13:25 London (ch. 8 F5); BRR New York window 15:00-16:00 ET (ch. 19 F2) | chapters 5, 8, 17 and 19 ledgers | https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031 | 2026-09-24 | see the cited rows | fig day |
| F7 | EPEX SPOT 2025: 917.5 TWh traded on its power markets (1,634.6 TWh double-sided) | EPEX SPOT, Annual Trading Results of 2025, 19 Jan 2026 | https://www.epexspot.com/sites/default/files/download_center_files/2026-01-19_EPEX%20SPOT_Annual%20Power%20Trading%20Results%202025_final_0.pdf | 2026-09-24 | "A total of 917.5 TWh (1,634.6 TWh double sided) was traded on the power markets of EPEX SPOT in 2025" | dat:m3:a-map-of-all-markets:sizes |
| F8 | LME futures and options ADV 2025: 717,334 lots (2024: 664,698, +7.9%) | LME Data Highlights 2025, as republished by Mondo Visione, Jan 2026 | https://mondovisione.com/media-and-resources/news/lme-data-highlights-2025-202618/ | 2026-09-24 | "Total 717,334 664,698 7.9%" | dat:m3:a-map-of-all-markets:sizes |
| F9 | CME FX Spot+ on Globex: Sunday 5:00 p.m. to Friday 4:00 p.m. CT with a 60-minute break each day beginning at 4:00 p.m. CT | CME Group, trading hours page (Internet Archive copy, 2025) | https://web.archive.org/web/2025/https://www.cmegroup.com/trading-hours.html | 2026-09-24 | "FX Spot+ Sunday 5:00 p.m. - Friday - 4:00 p.m. CT with a 60-minute break each day beginning at 4:00 p.m. CT" | section Hours |

## EXCLUDED

- US Treasury and equity turnover from WFE, EPEX and Nord Pool annual volumes, LME annual volumes and event-contract volumes: pages returned 403 or did not contain the figures; not used. **EPEX and LME annual volumes restored → F7, F8; WFE equity value traded re-searched 2026-09-24: the FY 2025 highlights give only growth rates in text (levels in charts); Nord Pool and event-contract volumes not found in a primary source; those stay excluded.**
- FX and CME Globex trading hours: no fetched source (CME blocks scripted access); the hours figure shows only sourced moments. **restored → F9 (CME's own schedule, via the Internet Archive); the figure still shows only the sourced fixed moments.**
- The firm's desk coverage windows (05:00-17:00 and 12:00-21:00 UTC) and shift rules are illustrative choices, not facts. **illustrative by design, not a sourcing gap.**

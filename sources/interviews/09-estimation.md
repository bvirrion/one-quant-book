# 9. Estimation — brief and source ledger

## Brief

- **Hook.** 'How many equity option contracts change hands in the United States on a typical day?' The candidate who answers 'between 20 and 80 million, most likely around 45' and shows the chain (listed names, contracts per name, a skew towards the index products) has answered better than one who happens to name the right number and cannot say how sure she is.
- **Sections.** The Fermi chain: decomposition, anchors and the geometric mean; Intervals: stating how sure you are, and being right that often; Market estimation questions: volumes, notionals, capacities; Checking an estimate against a second chain.
- **Defines.** Fermi estimate, calibrated interval.
- **Uses (defined earlier).** Brier score (B16.26), outcome bias (B16.26), proper scoring rule (B12.11), open interest (B1.18), sanity check (ch5), rule of 72 (ch8).
- **Question bank.** 13 questions, 4/5/4. Families: classical physical and population Fermi questions in new settings (two); market-size questions whose reference value is sourced (US option contracts a day, daily FX turnover, number of US-listed operating companies, shares of a large-cap traded a day, messages a second on a busy feed, bytes of a day of top-of-book data); an interval question scored against the true value; a two-chain cross-check; a self-assessment of calibration from ten past intervals (numeric: the binomial p-value of 5 hits in 10 at 90 per cent). Roles: trader 5, researcher 3, developer 2, bank 1, risk 1. Firms: market maker 4, proprietary firm 2, systematic fund 1, bank 1, any 4.
- **Facts to verify.** OCC or Cboe annual/monthly statistics: average daily US equity-option contract volume for the latest full year (dated); BIS Triennial Central Bank Survey 2025: daily FX turnover (dated; pointer to Book 2 ledger); number of US-listed operating companies (a WFE or exchange statistic, or a published research count) (dated); Cboe US equities market volume summary: consolidated daily share volume (dated); one busy feed's published peak message rate (OPRA or a venue's capacity statistics) (dated; pointer to Books 13-14 ledgers); UN World Population Prospects (latest revision) for the population anchors (dated); Tetlock and Gardner 2015 and Lichtenstein, Fischhoff and Phillips 1982 on overconfidence in interval estimates.
- **Data.** Figures: one chart (hit rate of stated 90 per cent intervals against their width, for a simulated overconfident and a calibrated estimator; fig_iv_calib.py). Code: iv_fermi.py (each chain's product equals the printed estimate; each ledger reference value lies in the printed interval; the calibration binomial test), exact where possible; the chart's simulation seeded.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Global OTC FX turnover USD 9.6 trillion a day in April 2025 | BIS Triennial Survey 2025 press release (pointer: ledgers markets-2/14 F1, markets-3 F1) | https://www.bis.org/press/p250930.htm | 2026-09-25 | "Global FX trading hits $9.6 trillion per day in April 2025" (as recorded in the Book 2 and Book 11 ledgers) | dat:iv:estimation:anchors; q4, q12 |
| F2 | OPRA SIP key operating metrics, July 2026: peak 63.9 million messages per second, 0.89 million per 10 ms | OPRA, Key Operating Metrics (August 2026) (pointer: ledgers low-latency/18 F3, networks/01 F1) | https://cdn.opraplan.com/documents/OPRA_SIP_Metrics_August_2026.pdf | 2026-09-28 | "Jul'26 99.986% 63.9 ... 7.9 ... 0.89 0.35" | dat:iv:estimation:anchors; hook; ex. opra; q5, q13 |
| F3 | OPRA capacity projection for July 2026, one stream: 4.403 Gb per 100 ms | SIAC/OPRA capacity notice of 15 Sept 2025 (pointer: ledger networks/22 F1 and low-latency F3) | https://cdn.opraplan.com/documents/notices/OPRA_Capacity_Projections_Update_0925.pdf | 2026-09-28 | "7/2026: ... 4.403 Gb" (as recorded) | dat:iv:estimation:anchors; q13 |
| F4 | CME Group 2025 average daily volume, total 28,129 thousand contracts | CME Group Inc., Form 10-K for 2025 (row recorded in ledger industry/02 F16) | https://www.sec.gov/Archives/edgar/data/1156375/000115637526000009/cme-20251231.htm | 2026-09-29 | "Average Daily Volume by Venue ... total 28,129" | dat:iv:estimation:anchors; q6 |
| F5 | World population 8.2 billion in 2024; peak around 10.3 billion in the mid-2080s | UN DESA, World Population Prospects 2024: Summary of Results | https://population.un.org/wpp/assets/Files/WPP2024_Summary-of-Results.pdf | 2026-09-29 | "reaching a peak of around 10.3 billion people in the mid-2080s, up from 8.2 billion in 2024" | dat:iv:estimation:anchors; q7 |
| F6 | Lichtenstein, Fischhoff and Phillips, Calibration of probabilities: the state of the art to 1980, in Judgment under Uncertainty, CUP 1982, 306-334 | Crossref | https://api.crossref.org/works/10.1017/CBO9780511809477.023 | 2026-09-29 | title, book, pages | section 2; omsources |
| F7 | Gneiting and Raftery, Strictly proper scoring rules, prediction, and estimation, JASA 102(477), 359-378, 2007 (interval score) | Crossref | https://api.crossref.org/works/10.1198/016214506000001437 | 2026-09-29 | title, journal, volume, issue, pages | section 2; q12; omsources |

## EXCLUDED

- OCC average daily US equity-option volume (planned hook): theocc.com refuses scripted fetches; the hook uses OPRA's published peak instead.
- Cboe consolidated share volume and the count of US-listed companies: not needed once the anchors above were chosen.


# 1. The Platform Map — brief and source ledger

## Brief

- **Hook.** At 07:40 the risk report, the overnight P&L and a researcher's backtest disagree about one position. Three teams spend the morning finding that a corporate action reached the security master after the risk batch had read it and before the P&L batch did: nobody had drawn which system reads what, and when.
- **Sections.** The systems of a trading firm; Data flows and their clocks; Systems of record and golden sources; Batch and stream; Reading a platform map.
- **Defines.** system of record, golden source, data-flow map, batch processing, stream processing, end-of-day batch, front-to-back flow.
- **Uses (defined earlier).** market data feed (B1.4), reference data (B1.28), security master (B7.4), risk engine (B6.29), product control (B6.27), order management system (B10.20), drop copy (B13.21), feature store (B12.24), machine-learning platform (B12.28).
- **Tutorial.** Describe the miniature firm built across the series (code/firm/ components of Books 1-15) as a data-flow map in data: systems, datasets, edges with schedules and latencies; compute the dependency closure of each dataset, the critical path of the end-of-day batch, and the set of reports affected by a late input. End state: a layered map of the firm (figure) and a table of blast radius per input.
- **Build.** `firm.platmap`: a platform map as data (systems, datasets, flows with cadence, deadline and owner), validation (every dataset has one system of record, no cycles in the batch), dependency closure, critical path of the batch with durations, impact of a late or wrong input; Python.
- **Weekend problem.** The morning the numbers disagreed -- named result: the set of reports and the latest safe start time of each batch job given input arrival times, and the minutes of slack the firm's end-of-day chain has before its 07:00 deadline.
- **Facts to verify.** BCBS 239, Principles for effective risk data aggregation and risk reporting (2013): accuracy, completeness, timeliness principles; a public description of a trading firm's data architecture (conference talk or engineering blog, dated).
- **Data.** The series' own component list (code/firm/), described as data; synthetic job durations.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | BCBS 239, "Principles for effective risk data aggregation and risk reporting", published 9 January 2013 | Basel Committee on Banking Supervision, BIS publication page | https://www.bis.org/publ/bcbs239.htm | 2026-09-28 | title "Principles for effective risk data aggregation and risk reporting"; date 9 January 2013 | dat:pl:the-platform-map:bcbs; omsources |
| F2 | BCBS progress report of 28 November 2023: of the 31 G-SIBs assessed, only two fully compliant with all the Principles | BCBS, "Progress in adopting the Principles for effective risk data aggregation and risk reporting" (d559) | https://www.bis.org/bcbs/publ/d559.htm | 2026-09-28 | page: "28 November 2023", "progress made by 31 G-SIBs (designated during 2011-21)"; the compliance count as quoted from the report and verified for One Quant Book 6, ch. 29 (F2, 2026-09-24): "Of the 31 banks assessed, only two banks are fully compliant with all the Principles." (bis.org refuses scripted PDF downloads) | dat:pl:the-platform-map:bcbs; omsources |
| F3 | Akidau et al., "The dataflow model", Proceedings of the VLDB Endowment 8(12), 1792-1803, August 2015 | Crossref record, DOI 10.14778/2824032.2824076 | https://api.crossref.org/works/10.14778/2824032.2824076 | 2026-09-28 | title, container, volume 8, issue 12, pages 1792-1803, issued 2015-08 | omsources |

## EXCLUDED

- A public description of a named trading firm's data architecture (brief): not needed; the chapter's map is the series' own firm.
- The hook's times are the chapter's own model (pl_platmap, HOOK_NIGHT), not a real incident.


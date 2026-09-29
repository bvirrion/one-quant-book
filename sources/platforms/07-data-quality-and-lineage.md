# 7. Data Quality and Lineage — brief and source ledger

## Brief

- **Hook.** On 6 May 2010, trades in more than three hundred securities were cancelled after the fact as clearly erroneous; a tick store that had captured them faithfully and never learned of the cancellation fed them to every backtest that touched that afternoon for years.
- **Sections.** Checks: completeness, validity, consistency, timeliness; Anomaly flags, not deletions; Cross-source checks; Vendor corrections and versions; Lineage and provenance.
- **Defines.** data-quality rule, data contract, anomaly flag, quarantine, cross-source check, vendor correction, data lineage, provenance record.
- **Uses (defined earlier).** clearly erroneous trade (B1.31), sequence number (B1.28), message gap (B13.16), restatement (B7.3), data vintage (B7.3), schema validation (B12.15), anomaly detection (B12.20), median absolute deviation (B4.15), data versioning (B12.25), content-addressed storage (B7.29), tick store (ch4), schema version (ch4).
- **Tutorial.** Plant defects in a generated day (sequence gaps from line loss, a crossed book, price spikes, a stale feed, a busted trade announced later, a vendor correction of a close) and run a rule suite over the tick store: completeness by sequence number, validity bounds, crossed or locked quotes, robust spike detection, staleness, cross-source comparison of lines A and B and of venue against consolidated feed; flag rather than delete, quarantine a partition, apply the correction as a new version and trace every affected downstream dataset through the lineage graph. End state: detection and false-flag rates per rule and the lineage of one corrected close.
- **Build.** `firm.dataqual`: rule definitions as data (severity, owner, scope), a runner over tick-store partitions producing flags with reasons, quarantine and release, correction handling as new versions through firm.pit, a lineage graph keyed by content hashes (firm.workflow) with downstream impact queries; Python.
- **Weekend problem.** The afternoon that was cancelled -- named result: the error in a backtest's P&L and in a volatility estimate when busted trades and planted spikes are kept, the error after flagging, and each rule's detection and false-flag rates.
- **Facts to verify.** SEC/CFTC 2010 report on the market events of May 6, 2010: number of securities with trades broken as clearly erroneous; FINRA/exchange clearly-erroneous execution rules (dated); a data vendor's published correction or cancel-and-correct message conventions (e.g. trade correction message types in a public feed specification); W3C PROV data model (provenance).
- **Data.** Generated day with planted defects; firm.exchsim lines A/B with loss and outages.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | 6 May 2010: between 2:40 and 3:00 p.m. over 20,000 trades across more than 300 securities executed at prices 60% or more away from their 2:40 p.m. prices, some at a penny or less or as high as $100,000; after the close the exchanges and FINRA agreed to break all such trades under their clearly erroneous trade rules | CFTC and SEC staffs, "Findings regarding the market events of May 6, 2010", 30 September 2010 | https://www.sec.gov/news/studies/2010/marketevents-report.pdf | 2026-09-28 | "over 20,000 trades (many based on retail-customer orders) across more than 300 separate securities, including many ETFs, were executed at prices 60% or more away from their 2:40 p.m. prices. After the market closed, the exchanges and FINRA met and jointly agreed to cancel (or break) all such trades under their respective clearly erroneous trade rules."; "at prices of a penny or less, or as high as $100,000" | hook; problem Q18; omsources |
| F2 | W3C PROV-DM: The PROV Data Model, W3C Recommendation of 30 April 2013; provenance is a record that describes the people, institutions, entities and activities involved in producing, influencing or delivering a piece of data | W3C | https://www.w3.org/TR/prov-dm/ | 2026-09-28 | title; "W3C Recommendation 30 April 2013"; "a record that describes the people, institutions, entities, and activities involved in producing, influencing, or delivering a piece of data or a thing" | dat:pl:data-quality-and-lineage:prov |

## EXCLUDED

- FINRA/exchange clearly-erroneous rule text (brief): not needed beyond the 2010 report; Book 1 ch. 31 owns the term.
- A vendor's correction-message conventions (brief): not needed; the chapter's correction is generic.


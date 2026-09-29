# 22. Post-Trade Systems — brief and source ledger

## Brief

- **Hook.** On 28 May 2024 US equities moved to settlement one business day after the trade; the time a firm has to confirm, allocate and fix a mismatched trade before it fails shrank from two days to one evening.
- **Sections.** From booked trade to settled trade; Confirmation and affirmation; Settlement instructions; Reconciliation and breaks; Operating under a short settlement cycle.
- **Defines.** trade confirmation, affirmation, confirmation matching, matching tolerance, standard settlement instruction, settlement instruction, reconciliation, reconciliation break, break ageing.
- **Uses (defined earlier).** settlement (B1.5), settlement cycle (B1.5), settlement fail (B1.5), central securities depository (B1.5), delivery versus payment (B1.5), clearing broker (B1.29), prime broker (B1.6), fails charge (B2.5), canonical trade model (ch21), booking (ch21), trade lifecycle event (ch21), position service (ch17).
- **Tutorial.** Take a day of booked trades from chapter 21, generate counterparty confirmations with planted discrepancies (price in the fourth decimal, a swapped settlement date, a wrong account, a missing trade), match them with field-level tolerances, generate settlement instructions from a standard-settlement-instruction table, and reconcile positions and cash against a simulated custodian statement; classify and age the breaks over a simulated week, and replay the week under a one-day cycle. End state: the match rate against tolerance and the break inventory by type and age under T+2 and T+1.
- **Build.** `firm.posttrade`: confirmation matching (keys, per-field tolerances, partial matches with scores), affirmation workflow with cut-off times, SSI store and settlement-instruction generation, a reconciliation engine (positions, cash, trades; one-to-one, one-to-many and aggregated matching), break classification, ownership and ageing reports; Python.
- **Weekend problem.** One evening instead of two days -- named result: the share of trades matched automatically at each tolerance, the breaks remaining at the affirmation cut-off under a two-day and a one-day cycle, and the fails and fails charges that follow.
- **Facts to verify.** SEC Release 34-96930 (2023), shortening the securities transaction settlement cycle: T+1 effective 28 May 2024, same-day affirmation; DTCC or industry report on T+1 affirmation rates after the move (dated); SWIFT MT54x / ISO 20022 settlement-instruction message types; CSDR settlement discipline regime (EU) cash penalties (dated).
- **Data.** Chapter 21's trades and synthetic counterparty and custodian files.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SEC Release 34-96930 (final rule, Shortening the Securities Transaction Settlement Cycle) amends Rule 15c6-1 to shorten the standard settlement cycle for most broker-dealer transactions from T+2 to T+1 | SEC | https://www.sec.gov/files/rules/final/2023/34-96930.pdf | 2026-09-28 | Summary: "adopting rule amendments to shorten the standard settlement cycle for most broker-dealer transactions from two business days after the trade date ("T+2") to one business day after the trade date ("T+1")" | hook, dat:pl:post-trade-systems:t1 |
| F2 | Compliance date 28 May 2024, following a Federal holiday | SEC 34-96930, Part VII | https://www.sec.gov/files/rules/final/2023/34-96930.pdf | 2026-09-28 | "the Commission is adopting a compliance date of May 28, 2024, which follows a Federal holiday for which both markets and banks will be closed" | hook, dat:pl:post-trade-systems:t1 |
| F3 | New Rule 15c6-2: broker-dealers must have agreements or policies to complete allocations, confirmations and affirmations as soon as technologically practicable and no later than the end of trade date | SEC 34-96930, Supplementary information | https://www.sec.gov/files/rules/final/2023/34-96930.pdf | 2026-09-28 | "address certain objectives related to completing allocations, confirmations, and affirmations as soon as technologically practicable and no later than the end of trade date" | sec. short cycle, dat:pl:post-trade-systems:t1 |
| F4 | The industry T+1 Report contemplated moving the affirmation cut-off of the central matching service from 11:30 a.m. ET on the day after trade date to 9:00 p.m. ET on trade date | SEC 34-96930, footnote in Part III | https://www.sec.gov/files/rules/final/2023/34-96930.pdf | 2026-09-28 | "the T+1 Report contemplates moving the "ITP Affirmation Cutoff" from 11:30 a.m. ET on the day after trade date to 9:00 p.m. ET on trade date" | hook, dat:pl:post-trade-systems:t1, windows of the model |
| F5 | Rule 17Ad-27: clearing agencies providing a central matching service must have policies to facilitate straight-through processing and file an annual report on it | SEC 34-96930, Supplementary information | https://www.sec.gov/files/rules/final/2023/34-96930.pdf | 2026-09-28 | "require clearing agencies that provide a central matching service ("CMSPs") to establish, implement, maintain, and enforce policies and procedures reasonably designed to facilitate straight-through processing ("STP") and to file an annual report" | dat:pl:post-trade-systems:t1 |

## EXCLUDED

- DTCC or industry reports of affirmation rates after the move to T+1: not fetched; the chapter prints no post-move affirmation rate.
- SWIFT MT54x and ISO 20022 settlement-instruction message types: not fetched; the chapter names no message type.
- EU CSDR settlement discipline cash penalties: not fetched; not mentioned.
- Fails charges for US equities: none sourced; the chapter reports the value of failing trades, and points to Book 2, chapter 5 for the Treasury fails charge.
- Everything else in the chapter (match rates, windows, staffing, ageing) is the chapter's synthetic model, stated as such; the windows are modelling choices anchored on F4.

# 17. Rebates, Inverted Venues and Tiers — brief and source ledger

## Brief

- **Hook.** Two venues show the same bid; one pays a passive fill about thirty cents per hundred shares and the other charges for it, so the queue on the first is long, the queue on the second is short, and a market maker has to decide which one to stand in.
- **Sections.** Fees as part of the spread; Queues on maker-taker and inverted venues; Tiers and their cliffs; Marginal fees and the volume decision.
- **Defines.** rebate capture, tier cliff, marginal fee.
- **Uses (defined earlier).** maker-taker pricing (B1.9), inverted venue (B1.9), access fee cap (B1.9), volume tier (B1.29), member rate (B1.30), effective tick (B10.7, by outline), queue value (ch5), wash trading (B3.16), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** rebate-capture passive making; inverted-venue queue placement; tier-aware volume management.
- **Tutorial.** On firm.feesched's schedules and a two-venue queue model, compute where a passive order should rest (fee, queue length, adverse selection), then the month's volume plan around a tier cliff and the marginal fee of each extra share.
- **Build.** `firm.rebatemm`: fee-adjusted queue value by venue, tier-cliff marginal-fee curve, volume allocation across venues under a tier schedule; Python, on firm.feesched.
- **Weekend problem.** Paid to wait, charged to wait — named result: the fee-adjusted edge of resting on each venue, and the month-end volume at which chasing the next tier stops paying.
- **Facts to verify.** SEC Rule 610 access fee cap amendments 2024 and their compliance status (dated); Battalio, Corwin, Jennings 2016 make-take fees and limit order execution quality (JF); A published maker-taker and an inverted venue fee schedule (Nasdaq, Cboe BYX/EDGA) (dated); SEC Transaction Fee Pilot and its vacatur, D.C. Circuit 2020 (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Amended Rule 610(c): access fees for executions against protected quotations priced at USD 1.00 or more may not exceed USD 0.001 per share (Release 34-101070; 89 FR 81620, October 8, 2024) | Federal Register | https://www.federalregister.gov/documents/full_text/text/2024/10/08/2024-21867.txt | 2026-09-25 | "will not be permitted to exceed or accumulate to more than $0.001 per share if the price of the protected quotation or other quotation is $1.00 or more" | dat:hf:rebates-inverted-venues-and-tiers:cap (row as verified for One Quant Book 10, ch. 7) |
| F2 | Compliance with the amended access fee caps extended to the first business day of November 2026 | SEC press release 2025-130, October 31, 2025 | https://www.sec.gov/newsroom/press-releases/2025-130-sec-issues-exemptive-order-regarding-compliance-certain-rules-under-regulation-nms | 2026-09-25 | "Rule 610(c) of Regulation NMS implementing the amended access fee caps: Until the first business day of November 2026." | dat:hf:rebates-inverted-venues-and-tiers:cap (row as verified for One Quant Book 10, ch. 7) |
| F3 | The SEC adopted the Transaction Fee Pilot (Rule 610T) on December 19, 2018: 1,460 randomly selected stocks in two test groups, one with a USD 0.0010 cap on exchange transaction fees (against the USD 0.0030 cap set in 2005), one with a prohibition on rebates; all other stocks a control group | D.C. Circuit opinion, New York Stock Exchange LLC v. SEC, No. 19-1042 | https://media.cadc.uscourts.gov/opinions/docs/2020/06/19-1042-1847356.pdf | 2026-09-25 | "assign 1,460 randomly selected stocks to one of two Test Groups. Half of those stocks will be subject to a $0.0010 cap ... the current $0.0030 cap established by the Commission in 2005. Stocks assigned to the other Test Group will be subject to a prohibition on exchanges' payment of rebates" | dat:hf:rebates-inverted-venues-and-tiers:cap (row as verified for One Quant Book 10, ch. 7) |
| F4 | The D.C. Circuit vacated Rule 610T, decided June 16, 2020 | D.C. Circuit opinion (F3) | https://media.cadc.uscourts.gov/opinions/docs/2020/06/19-1042-1847356.pdf | 2026-09-25 | "Decided June 16, 2020"; "We grant the petitions for review and vacate Rule 610T" | dat:hf:rebates-inverted-venues-and-tiers:cap (row as verified for One Quant Book 10, ch. 7) |
| F5 | R. Battalio, S. A. Corwin and R. Jennings, "Can brokers have it all? On the relation between make-take fees and limit order execution quality", Journal of Finance 71(5) (2016) 2193-2238: a negative relation between limit order execution quality and the rebate/fee level | Crossref record with abstract | https://doi.org/10.1111/jofi.12422 | 2026-09-25 | "we document a negative relation between several measures of limit order execution quality and rebate/fee level" | §1; strategy file (row as verified for One Quant Book 10, ch. 7) |

## EXCLUDED

- Published venue fee schedules (Nasdaq, Cboe BYX/EDGA): not restated; One Quant Book 10, chapter 7 cites them. The chapter's schedule is synthetic.

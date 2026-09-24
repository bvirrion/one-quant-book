# 20. Settlement Risk — brief and source ledger

## Brief

- **Hook.** On 26 June 1974 German regulators closed a bank at 15:30 Frankfurt time; its counterparties in New York had already paid their marks and never received their dollars.
- **Sections.** Herstatt; Payment versus payment; Netting; What remains unprotected.
- **Defines.** settlement risk, Herstatt risk, payment versus payment, payment netting, unilateral irrevocable payment time.
- **Uses (defined earlier).** delivery versus payment, currency pair, spot value date, central counterparty.
- **Tutorial.** Build the settlement-exposure timeline of a day's FX trades across time zones, gross and under PvP.
- **Build.** `firm.settlerisk`: settlement-exposure calculator.
- **Weekend problem.** The unsettled trillion — named result: the peak exposure of a gross-settled book and the reduction from netting and PvP.
- **Facts to verify.** Herstatt 1974 timeline (BIS); CLS settlement window, currencies, share of market (BIS 2022/2025); BIS settlement-risk estimates (2022 Triennial: $2.2tn unsettled); Basel Committee FX settlement guidance (2013).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | 26 Jun 1974: German supervisor closed Bankhaus Herstatt over losses on speculative FX positions, in the middle of the German business day, before US markets opened; it had received the marks bought two days earlier via the German payment system but not delivered the dollars sold; several institutions were affected and the US CHIPS system had to close for 24 hours; the case showed principal risk; CPSS 1996 strategy (three tracks: banks, industry groups, central banks); CLS, run by CLS Bank International, a direct consequence, started in September 2002; exposure runs from the unilateral cancellation deadline for the sold currency to final receipt of the bought currency (I period), then uncertain (U) and failed (F) periods; in 2006 CLS settled over USD 3 trillion a day and 32% of settlement obligations (about USD 1.2tn) still went through correspondent banking | ECB, Financial Stability Review, December 2007, Box 19 | https://www.ecb.europa.eu/press/financial-stability-publications/fsr/focus/2007/pdf/ecb~ccda416def.fsrbox200712_19.pdf | 2026-09-23 | "The bank was closed in the middle of the German business day, before the opening of US markets." | hook; §1; def |
| F2 | April 2022: USD 2.2 trillion of daily FX turnover subject to settlement risk (31% of deliverable turnover), up from 1.9tn in 2019; pre-settlement netting USD 1.3tn a day; USD 3.5tn settled with risk mitigation, of which USD 2.5tn via CLS, PvP in 18 currencies; PvP: final payment of one currency occurs if and only if the other's does; 20-40% at risk in the largest centres, over three quarters in some smaller ones; examples: Herstatt 1974; KfW EUR 300 million loss on Lehman (2008); Barclays USD 130 million loss to a small currency exchange (March 2020); reasons: cost, lack of access, unsupported currencies and time zones | Glowka and Nilsson, "FX settlement risk: an unsettled issue", BIS Quarterly Review, December 2022 | https://www.bis.org/publ/qtrpdf/r_qt2212i.htm | 2026-09-23 | "In April 2022, $2.2 trillion of daily FX turnover was subject to settlement risk" | §2-4 |
| F3 | April 2025 (new methodology, by settlement method): USD 5.2 trillion (just over a third) of average daily settlement via PvP; USD 7.6tn (54%) via intragroup, pre-settlement netting or bank accounts with timing controls (mitigate, do not eliminate); USD 1.4tn (10%) gross bilateral, fully exposed; main reasons: counterparty without PvP access, or unsupported currency; CPSS created 1990; Basel Committee established end 1974; CLS launched 2002 with CLSSettlement (PvP) | Drehmann, McGuire, Shirakami, Conway and Lovell, "Uncovering FX settlement risk: new measures from the 2025 BIS Triennial Survey", BIS Quarterly Review, June 2026 | https://www.bis.org/publ/qtrpdf/r_qt2606c.htm | 2026-09-23 | "In April 2025, 90% of the average daily settlement was via methods which eliminate or minimise FX settlement risk. But 10%, or $1.4 trillion, remained exposed to these risks." | §4; fig; dat:m2:settlement-risk:today |
| F4 | CLS: 18 currencies, more than USD 8.0 trillion settled on average each day, 75+ settlement members | CLS Group (ch. 14, F10) | https://www.cls-group.com/about-us/ | 2026-09-23 | "8.0+ USD trillion settled on average every day" | dat:m2:settlement-risk:today |

## EXCLUDED

- Brief hook's "15:30 Frankfurt time" and "counterparties in New York had paid marks": the ECB box says "in the middle of the German business day, before the opening of US markets" and that Herstatt had received marks; the text follows the ECB wording.
- CLS settlement window hours and pay-in schedule: not fetched from CLS; not used.
- Basel Committee 2013 FX settlement guidance: not fetched; not used.


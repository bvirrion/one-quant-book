# 17. Delta-One Instruments — brief and source ledger

## Brief

- **Hook.** Five ways to own the same index for a year, and five different costs.
- **Sections.** What delta-one means; Total return swaps; Futures as delta-one; Depositary receipts and dual listings; Comparing wrappers.
- **Defines.** delta-one, equity swap, funding spread, depositary receipt, dual listing, contract for difference, withholding tax, dividend enhancement.
- **Tutorial.** All-in annual cost of five wrappers for the same exposure.
- **Build.** Wrapper-cost comparator.
- **Weekend problem.** The ADR and the ordinary — named result: the arbitrage band in basis points.
- **Facts to verify.** ADR ratio and fees (depositary docs); 871(m); UK stamp duty and CFD exemption; futures roll cost statistics (CME).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | UK: SDRT 0.5% on electronic share purchases; stamp duty 0.5% on paper transfers over GBP 1,000; 1.5% on transfers into some depositary receipt schemes or clearance services; foreign shares bought outside the UK normally not charged | gov.uk, Tax when you buy shares | https://www.gov.uk/tax-buy-shares | 2026-09-18 | "You'll have to pay tax at 1.5% if you transfer shares into some 'depositary receipt schemes' or 'clearance services'" | dat:m1:delta-one-instruments:tax; pb |
| F2 | Intermediary relief: relief from stamp duty and SDRT for persons (including market maker principal brokers) who provide liquidity; FA 1986 ss 80A, 88A | HMRC Stamp Taxes on Shares Manual STSM042050 | https://www.gov.uk/hmrc-internal-manuals/stamp-taxes-shares-manual/stsm042050 | 2026-09-18 | "no SDRT is chargeable on an agreement to transfer securities to an intermediary" | dat tax |
| F3 | Section 871(m): dividend equivalents treated as US-source dividends; Notice 2024-44 extends the phase-in: rules not applied to non-delta-one transactions issued before 1 January 2027 | IRS Notice 2024-44 | https://www.irs.gov/pub/irs-drop/n-24-44.pdf | 2026-09-18 | "will not apply to any payment made with respect to any non-delta-one transaction issued before January 1, 2027" | dat tax; exo 5 |
| F4 | ADRs: ratio; custody fee (depositary services fee) commonly subtracted from gross dividends; "1000 ADRs could be assessed a fee ranging from $20 to $50"; Form F-6; Levels 1-3; unsponsored programmes; bulletin dated August 2012 | SEC Investor Bulletin: American Depositary Receipts (pdftotext) | https://www.sec.gov/files/adr-bulletin.pdf | 2026-09-18 | quoted | dat:m1:delta-one-instruments:adr |
| F5 | Madhavan, Marchioni, Li, Du, "Equity ETFs versus Index Futures: A Comparison for Fully Funded Investors", Journal of Index Investing 5(2), 2014, 66-75 | journal site | https://jii.pm-research.com/content/5/2/66 | 2026-09-18 | record | omsources |

## EXCLUDED

- CME figures on the E-mini S&P 500 implied financing spread (average 62 bp over 3m SOFR since the December 2022 roll; "richest June roll since 2007" in 2026): seen in search summaries only; both CME pages timed out. The chapter uses an explicit illustrative 30 bp and says only that the spread rises at year-ends.
- Issue/cancellation fee of "up to 5 cents per ADR": common in F-6 filings but none fetched; the problem states 5 cents as its own assumption.
- Typical retail CFD financing mark-up (2.5% to 3% over benchmark on brokers' pages): not sourced; the text says "commonly a few percent" and the comparator's 250 bp is declared illustrative.
- UK 1.5% charge: post-2024 legislative changes narrowed its scope for issues and capital-raising transfers; gov.uk still says "some" schemes. The problem applies it as an assumption of the exercise, citing the dated box.
- Whether ETFs are exempt from a purchase tax in a given market: declared an assumption in the figure caption ("exempt here").
- Treaty withholding rates (30% statutory, 15% treaty for US dividends): used in an exercise as given values; standard but not fetched from IRS Publication 515 in this run.

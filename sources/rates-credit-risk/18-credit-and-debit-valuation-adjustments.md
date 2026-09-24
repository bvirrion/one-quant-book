# 18. Credit and Debit Valuation Adjustments — brief and source ledger

## Brief

- **Hook.** The Basel Committee found that roughly two-thirds of the counterparty losses of the 2007-09 crisis came from marking the credit of living counterparties, not from defaults.
- **Sections.** CVA as the price of counterparty default; DVA and the bilateral view; Computing CVA; Sensitivities and hedging; Accounting and regulation.
- **Defines.** credit valuation adjustment, debit valuation adjustment, bilateral CVA, XVA, close-out amount.
- **Uses (defined earlier).** expected exposure (ch17), expected negative exposure (ch17), netting set (ch17), wrong-way risk (ch17), probability of default (ch13), loss given default (ch13), CS01 (ch13), hazard rate (B2.23), survival probability (B2.23), credit default swap (B2.23), credit spread (B2.21), additional tier 1 (B2.26).
- **Tutorial.** Compute CVA and DVA of chapter 17's netting set on a CDS-implied hazard curve, with bucketed CS01, and show the effect of wrong-way correlation.
- **Build.** `firm.cva`: CVA and DVA from exposure profiles and hazard curves, bucketed credit sensitivities; reads `firm.exposure` and `firm.cdscurve`.
- **Weekend problem.** The gain from getting riskier — named result: the DVA profit a bank books when its own spread widens by 50 basis points, and why regulators deduct it from capital.
- **Facts to verify.** BCBS statement on CVA losses in 2007-09 (two-thirds); IFRS 13 (2011, effective 2013) non-performance risk; Basel III deduction of DVA from CET1; bank DVA gains in 2011 (annual reports).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | During the financial crisis roughly two-thirds of losses attributed to counterparty credit risk were due to CVA losses and only about one-third to actual defaults; with the CVA risk capital charge, counterparty credit risk capital under Basel III doubles relative to Basel II | BCBS press release, "Capital treatment for bilateral counterparty credit risk finalised by the Basel Committee", 1 June 2011 | https://www.bis.org/press/p110601.htm | 2026-09-24 | "roughly two-thirds of losses attributed to counterparty credit risk were due to CVA losses and only about one-third were due to actual defaults"; "will double the level required under Basel II" | hook, dat:rc:credit-and-debit-valuation-adjustments:dva |
| F2 | Basel III paragraph 75: derecognise in CET1 all unrealised gains and losses from changes in the fair value of liabilities due to changes in the bank's own credit risk; July 2012 final rule: deduction from CET1 of all accounting valuation adjustments to derivative liabilities arising from own credit risk (DVA), phased in from 20% in 2014, full from 1 January 2018 | BCBS, Basel III (June 2011 revision), para. 75; BCBS press release 25 July 2012 "Regulatory treatment of valuation adjustments to derivative liabilities: final rule" | https://www.bis.org/press/p120725b.htm | 2026-09-24 | "Derecognise in the calculation of Common Equity Tier 1, all unrealised gains and losses that have resulted from changes in the fair value of liabilities that are due to changes in the bank's own credit risk"; "phased in, starting with 20% in 2014 and rising by 20% per year thereafter until full deduction occurs from 1 January 2018" | DVA section, dat:rc:credit-and-debit-valuation-adjustments:dva, weekend problem |
| F3 | IFRS 13 Fair Value Measurement, issued by the IASB in May 2011, defines fair value as an exit price, using the assumptions market participants would use, including assumptions about risk | IFRS Foundation, IFRS 13 page | https://www.ifrs.org/issued-standards/list-of-standards/ifrs-13-fair-value-measurement/ | 2026-09-24 | "In May 2011 the International Accounting Standards Board issued IFRS 13"; "the price that would be received to sell an asset or paid to transfer a liability in an orderly transaction between market participants at the measurement date (an exit price)"; "including assumptions about risk" | accounting section |
| F4 | IFRS 13 paragraph 42: the fair value of a liability reflects the effect of non-performance risk, which includes, but may not be limited to, an entity's own credit risk | IFRS 13 as adopted by Commission Regulation (EU) No 1255/2012, OJ L 360, 29.12.2012 | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32012R1255 | 2026-09-24 | "42 The fair value of a liability reflects the effect of non-performance risk. Non-performance risk includes, but may not be limited to, an entity's own credit risk" | fair-value paragraph |
| F5 | JPMorgan's third-quarter 2011 results included a USD 1.9 billion pretax (USD 0.29 per share after-tax) benefit from DVA gains in the Investment Bank, resulting from the widening of the firm's credit spreads | JPMorgan Chase & Co., third-quarter 2011 earnings release, Exhibit 99.1 to Form 8-K (October 2011) | https://www.sec.gov/Archives/edgar/data/0000019617/000095012311089762/y93007exv99w1.htm | 2026-09-24 | "$1.9 billion pretax ($0.29 per share after-tax) benefit from debit valuation adjustment ("DVA") gains in the Investment Bank, resulting from widening of the Firm's credit spreads" | fair-value paragraph |

## EXCLUDED

- Named banks' DVA gains in 2011: restored 2026-09-24 → F5 (JPMorgan's 3Q11 release on EDGAR, which now serves scripted requests with a declared user agent); the weekend problem keeps its illustrative bank.
- IFRS 13's explicit non-performance-risk paragraph (42): restored 2026-09-24 → F4 (EU-adopted text on EUR-Lex).


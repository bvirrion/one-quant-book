# 20. The Valuation-Adjustment Desk — brief and source ledger

## Brief

- **Hook.** A salesperson prices a twenty-year swap for an unrated corporate client; the valuation-adjustment desk adds thirty basis points a year, and the client walks to another bank.
- **Sections.** Why one central desk; Incremental pricing and allocation; What it hedges and what it cannot; Charging, transfer pricing and the desk's P&L; Organisation.
- **Defines.** XVA desk, incremental XVA, Euler allocation, XVA charge, proxy credit spread, contingent credit default swap.
- **Uses (defined earlier).** credit valuation adjustment (ch18), debit valuation adjustment (ch18), funding valuation adjustment (ch19), margin valuation adjustment (ch19), capital valuation adjustment (ch19), netting set (ch17), expected exposure (ch17), CS01 (ch13), credit default swap (B2.23), novation (B1.5), trade compression (B2.9).
- **Tutorial.** Compute the incremental CVA of a new trade in an existing netting set, compare it with the standalone figure, and allocate the netting set's CVA to its trades by Euler allocation.
- **Build.** `firm.xvaquote`: incremental XVA quote service over `firm.cva` and `firm.xvafund`; running-charge conversion.
- **Weekend problem.** The unrated corporate — named result: the all-in XVA add-on in running basis points for a twenty-year swap, and the part of it the desk can hedge in the market.
- **Facts to verify.** public descriptions of XVA desks (bank annual reports, published papers); EBA RTS on proxy spreads for CVA (EU Regulation 526/2014); Basel eligible CVA hedges (BCBS CVA framework); contingent CDS (public description).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Only single-name CDS, single-name contingent CDS and index CDS can be eligible CVA hedges; eligible single-name instruments reference the counterparty, a legally related entity, or an entity in the same sector and region | BCBS, Targeted revisions to the credit valuation adjustment risk framework, July 2020, MAR50.18-50.19 | https://www.bis.org/publications/202007-standards-targeted-revisions-credit-valuation-adjustment-risk-framework.pdf | 2026-09-24 | "Only single-name credit default swaps (CDS), single-name contingent CDS and index CDS can be eligible CVA hedges"; "(3) reference an entity that belongs to the same sector and region as the counterparty" | hedging section, dat:rc:the-valuation-adjustment-desk:proxy |
| F2 | For illiquid counterparties the market-implied PD must come from proxy credit spreads estimated from liquid peers via an algorithm discriminating on at least credit quality (eg rating), industry and region; single-name mapping (eg a municipality to its sovereign plus a premium) must be justified to the supervisor; fundamental analysis allowed when no peers exist but must relate to credit markets | same, MAR50.32(3) (SA-CVA requirements) | https://www.bis.org/publications/202007-standards-targeted-revisions-credit-valuation-adjustment-risk-framework.pdf | 2026-09-24 | "via an algorithm that discriminates on at least the following three variables: a measure of credit quality (eg rating), industry, and region"; "mapping a municipality to its home country"; "cannot be based on historical PD only - it must relate to credit markets" | proxy section, dat:rc:the-valuation-adjustment-desk:proxy |
| F3 | BA-CVA risk weight for not-rated or high-yield counterparties in basic materials, energy, industrials, agriculture, manufacturing, mining: 7.0% | same, MAR50.16 Table 1 | https://www.bis.org/publications/202007-standards-targeted-revisions-credit-valuation-adjustment-risk-framework.pdf | 2026-09-24 | "Basic materials, energy, industrials, agriculture, manufacturing, mining and quarrying 3.0% 7.0%" | weekend problem |
| F4 | EU RTS on proxy spreads (Commission Delegated Regulation (EU) No 526/2014, OJ L 148, 20.5.2014), Article 1: the proxy spread must consider all attributes of rating, industry and region; industry at least public sector, financial sector, others; region at least Europe, North America, Asia, rest of the world; reflects CDS and other liquid spreads; appropriateness judged on volatility rather than level | Commission Delegated Regulation (EU) No 526/2014 (EUR-Lex) | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32014R0526 | 2026-09-24 | "the proxy spread has been determined by considering all of the attributes of rating, industry and region"; "(i) public sector; (ii) financial sector; (iii) others"; "(i) Europe; (ii) North America; (iii) Asia; (iv) rest of the world" | proxy definition |

## EXCLUDED

- EBA RTS on proxy spreads (Commission Delegated Regulation (EU) No 526/2014): restored 2026-09-24 → F4 (EUR-Lex now serves the PDF).
- Public descriptions of named banks' XVA desks: re-searched 2026-09-24; only trade-press and vendor accounts, no filing or regulatory record describing a named bank's desk. Still excluded; the organisation section names no firm.
- Peer spreads, the client's internal rating and all trade terms: illustrative by design.


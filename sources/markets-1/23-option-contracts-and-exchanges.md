# 23. Option Contracts and the Options Exchanges — brief and source ledger

## Brief

- **Hook.** One stock, two thousand option series, seventeen exchanges.
- **Sections.** The contract; Clearing of options; The US options exchanges; European venues; Exercise, assignment and expiry.
- **Defines.** call option, put option, strike price, expiry, option premium, option series, American exercise, European exercise, assignment, option multiplier, in the money.
- **Tutorial.** Parse option symbols (OSI) and build a chain; payoff diagrams.
- **Build.** Option-chain container.
- **Weekend problem.** Expiry Friday — named result: the net share position after exercise and assignment.
- **Facts to verify.** OCC role and cleared volume; number of US options exchanges; OSI symbology; exercise-by-exception threshold 0.01; AM/PM settlement of SPX.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Exercise by exception: equity options $.01 in the money in customer, firm and market-maker accounts; index options $.01 in all account types; exchanges' cut-off for exercise notices 4:30 p.m. CT; "OCC randomly assigns exercise notices to its clearing members who, in turn assign their customers"; American vs European style | OIC, Options Exercise FAQ | https://www.optionseducation.org/referencelibrary/faq/options-exercise | 2026-09-18 | quoted | dat:m1:option-contracts-and-exchanges:expiry; dat:m1:option-contracts-and-exchanges:occ; def assignment; pb |
| F2 | OCC cleared a record 10.38 billion total contracts in 2022 | OCC press release, 3 Jan 2023 (title) | https://www.theocc.com/newsroom/press-releases/2023/0103occclearsrecordsetting1038billiontotalcontractsin2022 | 2026-09-18 | "OCC Clears Record-Setting 10.38 Billion Total Contracts in 2022" | dat:m1:option-contracts-and-exchanges:occ |
| F3 | OSI: 21-character key, 6-character root, YYMMDD, C/P, strike 5+3 digits; in force since February 2010 | OSI documentation as summarised by MarketsWiki / Fidelity (search excerpts) | https://www.fidelity.com/research/options/osi.shtml | 2026-09-18 | "Symbol - 6 bytes, Year - 2 bytes, Month - 2 bytes, Day - 2 bytes, Call/Put Indicator - 1 byte, Strike Dollar - 5 bytes and Strike Decimal - 3 bytes" | section 1; build |
| F4 | SPX: European, cash settled, $100 multiplier; standard (A.M.-settled) series expire on the third Friday with settlement from opening prices of the components and stop trading the business day before; SPXW (P.M.-settled) series trade until 4:00 pm ET on expiry and settle on closing prices | Cboe SPX and SPX Weeklys specifications (search excerpts) | https://www.cboe.com/tradable_products/sp_500/spx_options/specifications/ | 2026-09-18 | quoted excerpts | dat expiry; def style; exo 6; iq 6 |

## EXCLUDED

- Number of US options exchanges: secondary sources say 17 for 2026; the OCC participant list returned 403. The text says "more than fifteen" and the exercise uses sixteen as a stated assumption.
- Total number of listed option series (often quoted above one million): not verified; replaced by "hundreds of times as many".
- OCC 2025 annual volume: the OCC page returned 403; the 2022 record is used instead and dated as such.
- Strike-interval and expiry listing rules (weeklies, $0.50/$1/$2.50/$5 intervals): described qualitatively; the series count is an illustration with its inputs stated.
- Eurex/Euronext equity option styles and block-trade shares: the European paragraph is structural and unquantified.
- Evidence on pinning of stock prices at strikes (Ni, Pearson, Poteshman 2005): not cited; the mechanism is given as an answer in the problem, without a claim about its size.

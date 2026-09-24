# 6. Financing: Repo, Securities Lending and Prime Brokerage — brief and source ledger

## Brief

- **Hook.** A fund holds 5 billion dollars of stock with 1 billion of its own money; the rest is borrowed every night.
- **Sections.** Leverage and who provides it; Repo; Securities lending and the short sale; Prime brokerage and margin; Synthetic financing; When financing runs.
- **Defines.** leverage, repurchase agreement, haircut, securities lending, short sale, locate, rebate rate, prime broker, rehypothecation, total return swap, margin call.
- **Tutorial.** Cost of carry of a long--short book under cash and synthetic financing.
- **Build.** Financing-cost calculator feeding the P&L keeper.
- **Weekend problem.** Archegos in miniature — named result: the price drop that wipes out the equity.
- **Facts to verify.** Reg T 50%; SEC Rule 15c3-3 rehypothecation 140%; Archegos losses (Credit Suisse report, SEC complaint); Reg SHO locate.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Credit Suisse lost close to $5.5bn on Archegos; report published 29 July 2021; bank agreed standard swap margin of 7.5%; static margin; average margin 6.9%; dynamic margining not prioritised | Credit Suisse Group Special Committee of the Board, Report on Archegos Capital Management (Paul, Weiss), 29 July 2021 | https://www.sec.gov/comments/s7-32-10/s73210-20113776-265983.pdf | 2026-09-18 | "reduce Archegos's standard swap margin rate to 7.5%"; "swap margins remained depressed (an average of 6.9%)"; summary https://www.paulweiss.com/insights/client-news/credit-suisse-publishes-independent-review-of-archegos-losses | ex archegos |
| F2 | SEC charged Archegos and its founder, 27 April 2022; "$36 billion house of cards"; positions built with total return swaps on margin | SEC press release 2022-70 | https://www.sec.gov/newsroom/press-releases/2022-70 | 2026-09-18 | quote of the Director of Enforcement | ex archegos |
| F3 | Regulation T: 50% initial margin on purchases, 150% on short sales (12 CFR 220.12) | Federal Reserve Regulation T; summary | https://en.wikipedia.org/wiki/Regulation_T | 2026-09-18 | "initial margin of 50 percent for new purchases and 150 percent for short sales"; primary: 12 CFR 220.12(a),(c) | dat:m1:financing:rules |
| F4 | FINRA Rule 4210: 25% maintenance margin for long listed equity | FINRA Rule 4210 | https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210 | 2026-09-18 | rule text (c)(1) | dat:m1:financing:rules |
| F5 | SEA Rule 15c3-3: customer securities usable up to 140% of the customer's debit balance; excess must be in possession or control | FINRA interpretations of SEA Rule 15c3-3 | https://www.finra.org/sites/default/files/SEA.Rule_.15c3-3.pdf | 2026-09-18 | PDF text: "of 140 percent of the total of the debit balances in the customer's account"; "Customers' securities with a market value in excess of 140% of that amount must ..." | dat:m1:financing:rules |

## EXCLUDED

- Current interest rates, prime-broker spreads and borrow fees: volatile and mostly private; every rate in the chapter is labelled illustrative (4%, 0.50%, 0.30%).
- Total industry losses on Archegos across all banks and the names of the other dealers: not needed and not fetched; the chapter names only Credit Suisse, from its own report.
- Typical repo haircuts on government bonds (2%): used as an illustrative input to a proposition, not asserted as a market fact.

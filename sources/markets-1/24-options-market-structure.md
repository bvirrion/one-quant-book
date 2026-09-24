# 24. Options Market Structure — brief and source ledger

## Brief

- **Hook.** A customer's ten-lot starts a 100-millisecond auction among the largest firms in the world.
- **Sections.** Quote-driven markets and obligations; Allocation: customer priority and pro-rata; Price-improvement auctions; Complex orders; Penny increments, fees and order-flow payment.
- **Defines.** options market maker, quoting obligation, customer priority, price-improvement auction, complex order book, penny program, marketing fee, OPRA, quote protection.
- **Tutorial.** Allocate an incoming order under customer-priority pro-rata with a market-maker entitlement.
- **Build.** Options allocation rules in `firm.match`.
- **Weekend problem.** The auction — named result: the expected allocation to the initiating firm.
- **Facts to verify.** Cboe/ISE/PHLX allocation rules; PIM/AIM timers; Penny interval program permanent 2020; OPRA message rates.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Cboe AIM: auction period set by class, no less than 100 milliseconds and no more than 3 seconds; without price improvement, priority customer orders on the book first, then the initiating order for up to 50% of the agency order if one other user is at the price or 40% if two or more; never more than those percentages of the initial agency order at the final auction price | Cboe rule text in SEC filing SR-CBOE-2019-045, Exhibit 5A (search excerpt of the exhibit) | https://www.sec.gov/files/rules/sro/cboe/2019/34-87072-ex5.pdf | 2026-09-18 | "may be no less than 100 milliseconds and no more than 3 seconds"; "50% of the Agency Order if there is interest from one other User ... or 40% ... two or more other Users" | hook; dat:m1:options-market-structure:aim; build; pb |
| F2 | Penny Interval Program made permanent by SEC approval of 1 April 2020; all series of QQQ, SPY, IWM in $0.01; other classes $0.01 below $3.00 and $0.05 at $3.00 and above; a class remains while among the 425 most actively traded | SEC filings on the Penny Interval Program, e.g. Release 34-89167 Exhibit 5 (search excerpt); OIC article | https://www.sec.gov/files/rules/sro/nasdaq/2020/34-89167-ex5.pdf | 2026-09-18 | quoted excerpt; https://www.optionseducation.org/news/penny-increments | dat:m1:options-market-structure:penny; exo 3 |
| F3 | OPRA capacity projections, notice of 15 Sept 2025: 7/2026: maximum output 13.575 million msg per 100 ms, 4.403 Gb per 100 ms, 311 billion messages per day; 10/2025: 253; 1/2026: 298; 1/2027: 327; 7/2027: 343; one stream only, double for both; +10% for retransmissions; median latency under 18 microseconds | OPRA notice (pdftotext) | https://cdn.opraplan.com/documents/notices/OPRA_Capacity_Projections_Update_0925.pdf | 2026-09-18 | table "Capacity Projections" | dat penny; fig opra; exo 4; iq 4 |

## EXCLUDED

- The search engine's summary of the OPRA notice had the columns wrong (it gave 13.575 "billion messages per day"); the chapter uses the PDF's own table.
- Marketing fee levels and who directs the pool: generic definition only, no amounts.
- Market-maker quoting obligations (percentages of series and of the day, maximum widths): vary by exchange, not fetched; the definition says "a set percentage".
- The share of retail options flow executed in auctions, payment-for-order-flow amounts per contract, and wholesalers' names: not verified, not printed; the problem's 30 cents per contract and its five scenario probabilities are declared as the problem's own data.
- ISE/PHLX/BOX auction variants (PIM, PIXL, PIP) and their percentages: not fetched; only one exchange's rule is dated and described.
- Complex-order share of institutional volume: qualitative.

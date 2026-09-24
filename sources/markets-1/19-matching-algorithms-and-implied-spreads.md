# 19. Matching Algorithms and Implied Spreads — brief and source ledger

## Brief

- **Hook.** Two traders join the bid at the same price; in one product the first gets everything, in another they share.
- **Sections.** Price-time priority; Pro-rata and its variants; Market-maker privileges; Calendar spreads and implied prices; What the feed shows.
- **Defines.** price-time priority, pro-rata allocation, top-order allocation, lead market maker, calendar spread, implied-in, implied-out, market-by-order, market-by-price.
- **Tutorial.** Implement FIFO and pro-rata allocation and compare fills.
- **Build.** `firm.match`: allocation algorithms (used by the Book 10 matching engine).
- **Weekend problem.** The implied book — named result: the implied best bid in the spread.
- **Facts to verify.** CME matching algorithm list (F, K, A, etc.); Eurex allocation methods; CME implied functionality docs; CME MBO availability.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CME algorithms and products: FIFO (ES, NQ, ZN, ZF, ZB, CL outrights; 70.3% of volume); Configurable (ZT, ZQ, ZC, ZS, ZW outrights; 12.7%); Allocation = top order, pro rata with a 2-lot minimum, then FIFO (SR3 outrights; 10.5%); Threshold Pro Rata with LMM (10-year note options; 4.6%); nine algorithms listed; pro-rata allocations "rounded down to the nearest integer, including 0" | Databento, "CME matching algorithms explained" | https://databento.com/blog/cme-matching-algorithms-explained | 2026-09-18 | quoted table | dat:m1:matching-algorithms-and-implied-spreads:which; def prorata |
| F2 | CME list of supported algorithms (Allocation, FIFO, FIFO with LMM, FIFO with Top Order and LMM, Pro-Rata, Configurable, Threshold Pro-Rata, Threshold Pro-Rata with LMM); top order = first incoming order that betters the market; split FIFO/pro-rata | CME Group Client Systems Wiki, Supported Matching Algorithms (search excerpt) | https://cmegroupclientsite.atlassian.net/wiki/x/r5lAGw | 2026-09-18 | "incorporates a priority (top order) to the first incoming order that betters the market" | def top; dat which |
| F3 | Implied IN / OUT definitions; "Implied quantity will never match with implied quantity"; no legging risk | CME Group Client Systems Wiki, CME Globex Matching Algorithms and Implied Orders | https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/CME+Globex+Matching+Algorithms | 2026-09-18 | quoted; https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/Implied+Orders | def implied; pb q5 |
| F4 | Eurex: time, pro-rata and time-pro-rata allocation; time-pro-rata: "Orders with a higher time priority receive a higher matched quantity compared to the pro-rata allocation"; synthetic matching for futures spreads | Eurex, Matching principles | https://www.eurex.com/ex-en/trade/order-book-trading/matching-principles | 2026-09-18 | quoted | dat which |
| F5 | From 30 March 2026 Eurex changes Money Market Index Futures (FEU3, FST3, FEMP, FSR3) from time to time-pro-rata allocation | Eurex circular (search excerpt) | https://www.eurex.com/ex-en/find/circulars/circular-4972316 | 2026-09-18 | "will change the allocation scheme ... from 'time' to 'time-pro rata'" | dat which |

## EXCLUDED

- CME one-letter algorithm codes (F, K, A, T, C, O, Q, S, N): two sources disagreed in the search excerpts; codes are not printed.
- Loss of priority on quantity increase or price change: standard across exchanges but not fetched from a rulebook; the text says "on most exchanges".
- Dates and scope of CME market-by-order availability: not verified; the section describes the two feed types without attributing dates.
- How CME ranks implied against direct orders at the same price: documented on the wiki's "matching algorithm steps" page, not fetched; the problem treats the ranking rule as an open design question.
- Leg-price assignment convention for direct spread trades: mentioned qualitatively only.

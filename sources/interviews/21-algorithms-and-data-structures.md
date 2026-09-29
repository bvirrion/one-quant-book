# 21. Algorithms and Data Structures — brief and source ledger

## Brief

- **Hook.** 'Given a stream of trades, report after each one the median size of the last thousand.' The candidate sorts the window every time. It works, and the interviewer asks what happens at a million trades a second; the two heaps, the order-statistic tree and the counting array for bounded sizes are the three answers that score, each for a different reason.
- **Sections.** The families and how to recognise them: hashing, two pointers, sliding windows, heaps, sweeps, graphs, dynamic programming; Trading-flavoured variants: order books, streaming statistics, interval problems; The method: clarify, brute force, improve, test; Tutorial: testing an answer against a brute-force oracle.
- **Defines.** two-pointer technique, monotonic deque, sweep line.
- **Uses (defined earlier).** limit order book (B10.1), price-time priority (B1.19), Welford's algorithm (B4.25), sequence number (B1.28), matching engine (B10.1), cache line (B13.3), sanity check (ch5), think-aloud protocol (ch5), automated coding assessment (ch4).
- **Tutorial.** A short tutorial (1 p) may stay: write the brute force first, then test the fast answer against it on thousands of random inputs from a seeded generator, shrinking the failing case by hand. It earns its place because the same oracle tests check every answer of Part IV.
- **Question bank.** 14 questions, 5/5/4. Families: hashing (pair sums of order sizes, first duplicate client order identifier); two pointers (merging two sorted tapes, closest pair of bid and ask across venues); sliding window (maximum over the last k prices with a monotonic deque; the rolling median with two heaps); heaps (top-k symbols by volume over a stream); sweep line (the maximum number of simultaneously open orders from start and end times; merging overlapping trading halts); graphs (currency-conversion cycle detection with Bellman-Ford); dynamic programming (best single buy-sell and with k transactions and a fee); an order-book level structure (add, cancel, best price in the right complexity). Python for all; five also in C++20 (rolling median, top-k, order-book levels, open-orders sweep, arbitrage cycle). Roles: developer 9, researcher 3, trader 1, mle 2. Firms: market maker 5, proprietary firm 4, systematic fund 2, crypto firm 1, any 3.
- **Facts to verify.** none external: all answers are code; Cormen, Leiserson, Rivest and Stein (4th edition, 2022) as the method source.
- **Data.** Figures: none planned. Code: python/iv_algos.py (every answer) with an oracle per answer; cpp/iv_algos.hpp + cpp/iv_algos_test.cpp (the five C++20 answers against the same randomised cases, fixed seeds); tests assert equality with the oracle over many seeds and the complexity claims by operation counts, never timings.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F2 | Welford, Note on a method for calculating corrected sums of squares and products, Technometrics 4(3), 419-420, 1962 | Crossref | https://api.crossref.org/works/10.1080/00401706.1962.10490022 | 2026-09-29 | title, journal, volume, issue, pages | omsources |
| F1 | Cormen, Leiserson, Rivest and Stein, Introduction to Algorithms, Fourth Edition, MIT Press, 2022 | Open Library edition record (ISBN 9780262046305) | https://openlibrary.org/isbn/9780262046305.json | 2026-09-29 | title ``Introduction to Algorithms, Fourth Edition'', publisher MIT Press, 2022 | omsources |

## EXCLUDED


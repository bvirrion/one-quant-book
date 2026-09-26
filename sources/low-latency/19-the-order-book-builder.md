# 19. The Order-Book Builder — brief and source ledger

## Brief

- **Hook.** A book keyed by a balanced tree took hundreds of nanoseconds per update at the open; an array of price levels around the touch took a few tens, and then broke on the first stock that moved thirty percent in a day.
- **Sections.** What the book must answer, and how fast; Structures by feed type and tick regime; Order lookup: hash tables and open addressing; Correctness under gaps, crosses and recovery; Testing a book.
- **Defines.** book builder, dense price ladder, open addressing, book invariant.
- **Uses (defined earlier).** market data feed (B1.4), sequence number (B1.28), normalisation (B1.28), market-by-order (B1.19), market-by-price (B1.19), level 1 (B1.28), level 2 (B1.28), level 3 (B1.28), limit order book (B10.1), limit order (B10.1), market order (B10.1), price-time priority (B1.19), tick size (B10.1), price level (B10.1), exchange simulator (B10.26), matching engine (B10.1), feed handler (ch18), stale-book flag (ch18), cache miss (ch3), working set (ch3), microprice (B7.8).
- **Tutorial.** Three builders -- tree map, sorted vector and a recentring dense ladder with an open-addressing order map -- driven by the simulator's day for a large-tick and a small-tick instrument; a differential test against Book 1's firm.feed book and Book 7's firm.lobfeat on shared fixtures. End state: update-time histograms by structure and tick regime, measured on this laptop.
- **Build.** `firm.bookbuilder`: order-by-order book with constant-time order lookup, a dense ladder with recentring and a sparse fallback, level 1 and level 2 queries, invariants checked in debug builds, invalidation on gaps and rebuild from a snapshot; C++20 and Rust with a Python reference; acceptance: identical level 2 to firm.feed and firm.lobfeat on the fixtures and zero allocations per update after warm-up.
- **Weekend problem.** The stock that moved thirty percent -- named result: the ladder width against the expected number of recentrings a day for a given daily volatility and tick, and the width that minimises the day's total cost.
- **Data.** Book 10 simulator's recorded day (large-tick and small-tick instruments); Book 1 and Book 7 fixtures.
- **Facts to verify.** Nasdaq ITCH 5.0: order replace semantics (priority lost); cppreference: std::map node allocation and complexity.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ITCH 5.0 Order Replace (U): sent whenever an order has been cancel-replaced; the original order's remaining shares must be removed and a new order reference is used henceforth; side, symbol and attribution cannot change and are not repeated (retain them from the original Add Order) | Nasdaq TotalView-ITCH 5.0 specification, section 1.4.5 | https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf | 2026-09-25 | "All remaining shares from the original order are no longer accessible, and must be removed. The new order details are provided for the replacement, along with a new order reference number" | section 2; build |
| F2 | std::map: sorted associative container; search, removal and insertion in logarithmic complexity; usually implemented as red-black trees (one node per element) | cppreference.com, std::map | https://en.cppreference.com/w/cpp/container/map | 2026-09-25 | "Search, removal, and insertion operations have logarithmic complexity. Maps are usually implemented as Red-black trees" | section 2; tutorial |

## EXCLUDED


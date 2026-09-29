# 26. System Design — brief and source ledger

## Brief

- **Hook.** 'Design a matching engine.' Forty-five minutes, a whiteboard, no other words. The candidate who draws boxes for five minutes and then asks how many instruments, how many messages a second at peak, what latency at the 99th percentile, and what happens when the process dies, has already done better than the one who began with the order book's data structure.
- **Sections.** The method: requirements, capacity estimate, interfaces, core design, failure, and the numbers; The order book and the matching engine; Market data and the backtester; The risk service and the question of state.
- **Defines.** system-design interview, capacity estimate.
- **Uses (defined earlier).** limit order book (B10.1), matching engine (B10.1), price-time priority (B1.19), sequence number (B1.28), snapshot recovery (B10.26), feed handler (B13.18), order gateway (B13.21), sequencer architecture (B13.24), replicated state machine (B13.24), idempotent processing (B13.24), latency budget (B13.1), tail latency (B13.1), multicast (B13.16), back-pressure (B13.12), pre-trade risk check (B11.27), kill switch (B11.27), event-driven backtest (B7.17), fill model (B7.17), backtest engine (B15.11), event sourcing (B15.24), partitioning (B15.2), tick store (B15.4), Fermi estimate (ch9).
- **Question bank.** 13 questions, 4/5/4. Families: capacity estimates (messages a second and bytes a day for a feed, memory for a full-depth book of N instruments, numeric); the order-book core (data structure choices for add, cancel, execute, best price, with complexities; a reference implementation); the matching engine (determinism, sequencing, recovery by replay, the journal); a market-data distribution service (fan-out, gaps, snapshots, slow consumers); a backtester (event loop, clocks, fill models, reproducibility); a pre-trade risk service (state, latency, fail-closed); scaling and failure questions for each. Worked answers are structured by the lesson's method. Roles: developer 9, researcher 2, risk 1. Firms: market maker 5, proprietary firm 3, crypto firm 2, bank 1, any 1.
- **Facts to verify.** public capacity statistics used as anchors (a venue's or OPRA's published peak message rates) (dated; pointer to Books 13-14 ledgers); the series' own exchange simulator protocol (code/firm/exchsim/PROTOCOL.md) in prose.
- **Data.** Figures: two schematics (the matching-engine architecture with sequencer, journal and replicas; the market-data service with snapshot and incremental channels). Code: python/iv_design.py (the capacity estimates, asserted), cpp/iv_book.hpp + cpp/iv_book_test.cpp (a reference price-level book with add, cancel, execute and best price in C++20, tested against a Python oracle's recorded outcomes on seeded order streams); no timings.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|

## EXCLUDED

No external facts: all capacity figures are computed from stated assumptions (tests/test_solutions.py); header sizes (Ethernet 14, IPv4 20, UDP 8 bytes) are protocol constants, see the chapter 25 ledger (RFC 768).


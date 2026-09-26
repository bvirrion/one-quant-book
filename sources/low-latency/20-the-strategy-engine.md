# 20. The Strategy Engine — brief and source ledger

## Brief

- **Hook.** Two runs of the same strategy on the same day's data ended with different profits: one component iterated a hash map, another read the wall clock. After both were removed the runs agreed to the last bit, and every later bug could be replayed.
- **Sections.** The event loop; Single-threaded determinism; Timers and the injected clock; Configuration and parameters at run time; Hot-path discipline.
- **Defines.** event loop, run-to-completion processing, timer wheel, injected clock, parameter snapshot.
- **Uses (defined earlier).** exchange simulator (B10.26), matching engine (B10.1), simulated clock (B7.17), bitwise reproducibility (B4.25), quoting engine (B11.10), cancel-replace (B11.10), microprice (B7.8), ring buffer (ch12), hot path (ch1).
- **Tutorial.** Build the C++ engine: ring inputs, an event loop, a timer wheel and a simple quoting strategy on Book 7's microprice; run it twice on the same recorded input and compare output hashes; inject a wall-clock read and a hash-map iteration and watch the hashes diverge. End state: identical hashes over repeated runs, and the divergence table with each source of nondeterminism switched on.
- **Build.** `firm.stratengine`: event loop over market, order and timer events with fixed ordering rules, an injected clock (simulated or real), a timer wheel, versioned parameter snapshots applied between events; C++20 and Rust; acceptance: bit-identical output on replay and zero allocations in steady state.
- **Weekend problem.** Two runs, two profits -- named result: the number of distinct outcomes in a hundred reruns with each source of nondeterminism switched on, and one after the fixes.
- **Data.** Book 10 simulator's recorded day.
- **Facts to verify.** Varghese and Lauck 1987, Hashed and hierarchical timing wheels (SOSP); Fowler 2011, The LMAX Architecture (single-threaded business logic).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Varghese and Lauck, Hashed and hierarchical timing wheels: data structures for the efficient implementation of a timer facility, Proceedings of the 11th ACM SOSP, 1987, pp. 25-38 | Crossref record | https://api.crossref.org/works/10.1145/41457.37504 | 2026-09-25 | title, venue, pages, year | section 3 |
| F2 | LMAX: a Business Logic Processor on a single thread, in memory, using event sourcing: its state is entirely derivable by replaying the input events kept in a durable store; the business logic is deterministic, so output events need not be journalled | M. Fowler, The LMAX Architecture (2011) | https://martinfowler.com/articles/lmax.html | 2026-09-25 | "the current state of the Business Logic Processor is entirely derivable by processing the input events"; "The business logic is deterministic and very fast, so there's no gain from storing the results" | sections 1-2 |
| F3 | Rust's std HashMap uses a hashing algorithm resistant to HashDoS, randomly seeded from the host's secure randomness; iteration visits keys in arbitrary order | Rust standard library documentation, std::collections::HashMap | https://doc.rust-lang.org/std/collections/struct.HashMap.html | 2026-09-25 | "The algorithm is randomly seeded"; "An iterator visiting all keys in arbitrary order" | section 2 |

## EXCLUDED


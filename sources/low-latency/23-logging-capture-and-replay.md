# 23. Logging, Capture and Replay — brief and source ledger

## Brief

- **Hook.** A regulator asked why one order was sent at a given nanosecond. The firm answered by replaying the day's captured inputs through the same binary and showing the decision, the book and the parameters that produced it, to the bit.
- **Sections.** Why formatted logging is not for the hot path; Binary logging and deferred formatting; Capture: inputs, outputs and time; Deterministic replay of a production day; What must be kept, and for how long.
- **Defines.** binary log, deferred formatting, input journal, deterministic replay.
- **Uses (defined earlier).** exchange timestamp (B1.28), receive timestamp (B1.28), event loop (ch20), injected clock (ch20), ring buffer (ch12), replay parity test (B7.19), order-book replay (B7.18), bitwise reproducibility (B4.25).
- **Tutorial.** Log from the hot path as fixed-size records (a format identifier and raw arguments) into a ring drained by a writer thread; decode and format offline in Python; compare the hot-path cost with fprintf and std::format; journal the strategy engine's inputs, replay them and find a planted nondeterminism by bisecting the first diverging record. End state: cost per log call by method, measured on this laptop, and a replay that matches to the bit.
- **Build.** `firm.binlog`: log statements registered at compile time, a lock-free record ring, a writer thread, a file format with a schema header, a Python decoder, an input journal and a replay driver for firm.stratengine; C++20 and Rust with the Python decoder; acceptance: bit-identical replay and zero allocations on the logging path.
- **Weekend problem.** To the nanosecond -- named result: journal storage per day at given message rates and compression ratio, and the replay speed against real time.
- **Data.** Recorded inputs of chapter 20's engine.
- **Facts to verify.** Yang et al. 2018, NanoLog: a nanosecond scale logging system (USENIX ATC); Commission Delegated Regulation (EU) 2017/589 (RTS 6) record-keeping of algorithmic trading (article 28); Commission Delegated Regulation (EU) 2017/574 (RTS 25) timestamp granularity (pointer to B1.28); CAT NMS Plan record requirements (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | NanoLog (Yang, Park, Ousterhout, USENIX ATC 2018): extracts static log components at compile time, writes a compacted binary log at run time, re-inflates it offline; about 80 million simple messages a second, typical invocation overhead 8 ns in microbenchmarks and 18 ns in applications | USENIX ATC 18 presentation page | https://www.usenix.org/conference/atc18/presentation/yang-stephen | 2026-09-25 | "extracting static log components"; "outputs the log in a compacted, binary format at runtime"; "utilizes an offline process to re-inflate the compacted logs"; "typical log invocation overhead of 8 nanoseconds in microbenchmarks and 18 nanoseconds in applications" | section 2 |
| F2 | RTS 6 article 28: records of orders of high-frequency algorithmic trading kept for five years from the submission of the order | Commission Delegated Regulation (EU) 2017/589, EUR-Lex | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0589 | 2026-09-25 | "The records referred to in paragraphs 1 and 2 shall be kept for five years from the date of the submission of an order to a trading venue or to another investment firm for execution." | section 5; dat:ll:logging-capture-and-replay:records |
| F3 | RTS 25: participants using a high-frequency algorithmic trading technique keep business clocks within 100 microseconds of UTC with a time stamp granularity of 1 microsecond or better (1 ms for other trading); traceability to UTC reviewed at least once a year (article 4) | Commission Delegated Regulation (EU) 2017/574, Annex table 2, EUR-Lex | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0574 | 2026-09-25 | "100 microseconds"; "1 microsecond or better"; "conduct a review of the compliance of the traceability system with this Regulation at least once a year" | section 3; dat:ll:logging-capture-and-replay:records |

## EXCLUDED

- CAT NMS Plan record requirements (brief): not needed; the dated box states the EU rules as the example, and US order audit trails are Book 1's (chapter 28) and Book 11's.


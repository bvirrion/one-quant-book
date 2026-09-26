# 26. Build: Tick-to-Trade, Measured — brief and source ledger

## Brief

- **Hook.** A packet leaves the simulated exchange, and some microseconds later an order comes back: the whole path of this book is assembled, and every stage stamps the time it took.
- **Sections.** Assembling the path; Instrumentation points and stage timestamps; The budget against the measurement; What a tuned server would change.
- **Defines.** instrumentation point, latency attribution.
- **Uses (defined earlier).** exchange simulator (B10.26), matching engine (B10.1), tick-to-trade latency (ch1), latency budget (ch1), latency histogram (ch5), feed handler (ch18), book builder (ch19), event loop (ch20), order gateway (ch21), risk gate (ch22), binary log (ch23), kernel bypass (ch13).
- **Tutorial.** Replay the simulator's recorded A and B lines over loopback UDP at their recorded pace into the assembled C++ path (feed handler, ring, book builder, strategy engine, risk gate, gateway over TCP to the simulator), time every stage with the time-stamp counter into the binary log, and produce per-stage histograms and the budget report of chapter 1; run the Rust twin on the same input. End state: the end-to-end and per-stage histograms, measured on this laptop with no isolated cores, and the budget table.
- **Build.** `firm.ticktotrade`: the assembled path and its harness -- configuration, instrumentation points, per-stage histograms, budget report through firm.latbudget; C++20 and Rust; acceptance: orders identical to the Python reference strategy on the same input, zero allocations after warm-up, every stage timestamp ordered.
- **Weekend problem.** The budget, proven -- named result: the measured median, 99th and 99.9th percentiles per stage and end to end on this laptop, and the projected figures for a tuned server built from cited per-stage factors.
- **Data.** Book 10 simulator's recorded lines and order-entry server; measured on this laptop.
- **Facts to verify.** STAC tick-to-trade benchmark reports (dated); a public talk giving a production tick-to-trade figure (dated); a kernel-bypass stack's published loopback or wire latency (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ef_vi (Xilinx, now AMD, Solarflare adapters) gives an application direct access to the network adapter's datapath for lower latency and per-message overhead; its data path operations need no system call (kernel bypass) | ef_vi User Guide, SF-114063-CD issue 10, 2019 | https://www.amd.com/content/dam/amd/en/support/downloads/solarflare/onload/openonload/packages/SF-114063-CD-10_ef_vi_User_Guide.pdf | 2026-09-26 | "ef_vi grants an application direct access to the Solarflare network adapter datapath to deliver lower latency and reduced per message processing overheads"; "Kernel bypass: Data path operations do not require system calls." | section 4 |

## EXCLUDED

- STAC tick-to-trade reports and a public talk's production figure (brief): not used; STAC's reports are behind registration and the talks found give no citable figure with conditions. Kernel-bypass latency figures: the vendor's user guide describes the mechanism without a latency figure, so the projection uses chapter 1's budget (itself a stated assumption) rather than a vendor number.


# 25. Concurrency, Operating Systems and Networks — brief and source ledger

## Brief

- **Hook.** Two threads each add one to a shared counter a million times; the program prints 1,318,442. The candidate is asked for the smallest value it could print, which is not what anyone expects, and then for the three ways to make it print two million, ranked by what each costs on a hot path.
- **Sections.** Atomics, locks and memory ordering: the questions and the reasoning; Processes, threads, scheduling and system calls; Memory: virtual memory, page faults, caches and false sharing; Networks: what happens when a packet arrives, TCP against UDP, multicast.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** atomic operation (B13.11), memory ordering (B13.11), acquire--release ordering (B13.11), sequential consistency (B13.11), compare-and-swap (B13.11), ABA problem (B13.11), lock-free (B13.11), wait-free (B13.11), priority inversion (B13.11), data race (B13.9), context switch (B13.13), kernel bypass (B13.13), busy polling (B13.13), page fault (B13.6), cache line (B13.3), false sharing (B13.3), cache miss (B13.3), multicast (B13.16), ring buffer (B13.12), single-producer single-consumer queue (B13.12), back-pressure (B13.12), tail latency (B13.1), jitter (B13.1), output-prediction question (ch22).
- **Question bank.** 13 questions, 4/5/4. Families: the lost-update counter (the minimum possible final value, 2, with the interleaving; a model-checked answer for small counts); memory-ordering litmus tests (store buffering, message passing: which outcomes each ordering permits, enumerated by an exhaustive interleaving checker for sequential consistency and stated from the C++ model for acquire-release); a correct single-producer single-consumer queue (C++20, tested); deadlock and lock ordering; false sharing (why padding helps; the cache-line arithmetic); system calls and context switches (what a read on a socket costs, qualitatively; what kernel bypass removes); virtual memory (page-table arithmetic, numeric); the packet walk from wire to user space; TCP against UDP for market data and order entry; multicast gap detection with sequence numbers (Python, tested). Roles: developer 11, researcher 1, mle 1, trader 1. Firms: market maker 6, proprietary firm 5, crypto firm 1, any 2.
- **Facts to verify.** ISO C++20 memory model clauses for the litmus outcomes; the Linux kernel documentation for the receive path (NAPI, socket buffers) at a stated version; RFC 9293 (TCP) and RFC 768 (UDP); Herlihy and Shavit 2012 as the method source.
- **Data.** Figures: one schematic (the receive path of a packet from the NIC to the application, kernel and bypass paths side by side). Code: python/iv_conc.py (an exhaustive interleaving explorer for the counter and the sequentially consistent litmus tests; page-table arithmetic; gap detection), cpp/iv_spsc.hpp + cpp/iv_spsc_test.cpp (queue, stress-tested with a bounded run), cpp/snippets for the lost-update demonstration under ThreadSanitizer (the race diagnosed, the count not asserted).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Herlihy and Shavit, The Art of Multiprocessor Programming, revised reprint, 2012 | Open Library catalogue | https://openlibrary.org/works/OL25154026W | 2026-09-29 | title Art of Multiprocessor Programming, Revised Reprint, 2012 | omsources |
| F2 | RFC 768, User Datagram Protocol, J. Postel (1980) | RFC Editor | https://www.rfc-editor.org/rfc/rfc768.json | 2026-09-29 | doc_id RFC768, author J. Postel, Internet Standard | section 5; omsources |
| F3 | RFC 9293, Transmission Control Protocol (TCP), W. Eddy, Ed. (2022) | RFC Editor | https://www.rfc-editor.org/rfc/rfc9293.json | 2026-09-29 | doc_id RFC9293, author W. Eddy, Ed., Internet Standard | section 5; omsources |

## EXCLUDED

- The ThreadSanitizer run needs ASLR disabled (setarch -R) on this kernel; the test retries that way. No timing is printed.


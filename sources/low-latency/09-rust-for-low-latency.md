# 9. Rust for Low Latency — brief and source ledger

## Brief

- **Hook.** A team porting its feed handler to Rust found the median unchanged and one allocation per message hidden in a convenient iterator adapter; the compiler had stopped them sharing the book across threads, but not from allocating.
- **Sections.** Zero-cost abstractions, checked; Unsafe code and its boundaries; Controlling allocation; Threads, pinning and what the type system guarantees; Where async does and does not belong.
- **Defines.** data race, zero-cost abstraction, bounds-check elimination, sound abstraction, global allocator, async runtime.
- **Uses (defined earlier).** arena allocator (ch6), static polymorphism (ch7), cache line (ch3), microbenchmark (ch2).
- **Tutorial.** In one Rust crate: an iterator chain against an indexed loop and the bounds checks each leaves in the assembly; a counting global allocator asserting zero allocations per message; a thread pinned through sched_setaffinity by a small FFI declaration; the Rust twin of chapter 6's pool against the C++ one. End state: the C++ and Rust decoders side by side, cycles and allocations per message.
- **Build.** `firm.affinity`: thread placement by role -- pin, verify with sched_getcpu, name threads, read back the placement from firm.coreplan's plan; Rust and C++20.
- **Weekend problem.** The port -- named result: the Rust-to-C++ ratio of median cycles per message for the decoder and the book, and allocations per message in each (zero in both after the fix).
- **Data.** Measured on this laptop only.
- **Facts to verify.** Stroustrup, the zero-overhead principle (Foundations of C++, 2012); The Rust Reference and the Rustonomicon: unsafe, Send and Sync, GlobalAlloc; Linux sched_setaffinity(2).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Zero-overhead principle: "What you don't use, you don't pay for [Stroustrup, 1994]. And further: What you do use, you couldn't hand code any better." | B. Stroustrup, Abstraction and the C++ machine model (ICESS'04, 2005) | https://www.stroustrup.com/abstraction-and-machine.pdf | 2026-09-25 | quote as given | section 1 |
| F2 | Tokio (a Rust async runtime) is designed for IO-bound applications where each task spends most of its time waiting for IO; not for speeding up CPU-bound computations; offers a multi-threaded work-stealing runtime or a single-threaded one | Tokio tutorial, "When not to use Tokio" | https://tokio.rs/tokio/tutorial | 2026-09-25 | "Tokio is designed for IO-bound applications where each individual task spends most of its time waiting for IO"; "a multi-threaded, work-stealing runtime to a light-weight, single-threaded runtime" | section 5 |
| F3 | Rust: Send and Sync mark types safe to transfer or share between threads; unsafe code must uphold invariants that safe code relies on (soundness) | The Rustonomicon, Send and Sync | https://doc.rust-lang.org/nomicon/send-and-sync.html | 2026-09-25 | "A type is Send if it is safe to send it to another thread. A type is Sync if it is safe to share between threads" | section 4 |

## EXCLUDED


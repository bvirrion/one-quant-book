# 12. Queues, Ring Buffers and Shared Memory — brief and source ledger

## Brief

- **Hook.** A team measured a three-stage pipeline built on a standard blocking queue and found that the queues, not the work, dominated its latency; the ring buffer they replaced them with became a pattern with its own name.
- **Sections.** The single-producer single-consumer ring; Many readers: the disruptor pattern; Sequence locks for last-value data; Shared memory between processes; Back-pressure, slow consumers and conflation.
- **Defines.** ring buffer, single-producer single-consumer queue, disruptor pattern, sequence lock, shared-memory transport, back-pressure, slow consumer, conflation.
- **Uses (defined earlier).** acquire--release ordering (ch11), false sharing (ch3), lock-free (ch11), wait-free (ch11), M/M/1 queue (B4.8).
- **Tutorial.** An SPSC ring in C++ with cached indices; its round-trip latency between two pinned threads on the same core cluster and across clusters; a seqlock publishing the top of the book; a ring in /dev/shm written by a Rust process and read by a C++ process. End state: round-trip histograms by placement, measured on this laptop, and a cross-language test that passes.
- **Build.** `firm.ring`: SPSC ring, broadcast ring with per-reader sequences (disruptor style), seqlock slot, shared-memory segment with a versioned header; C++20 and Rust sharing one memory layout. The transport of every Part IV component.
- **Weekend problem.** Three strategies, one feed -- named result: the time before a slow consumer is overrun in a broadcast ring of given size during a burst, and the share of updates a conflating reader skips.
- **Data.** Measured on this laptop only.
- **Facts to verify.** Thompson et al. 2011, Disruptor technical paper (queue against ring latency figures); Lamport 1983, Specifying concurrent program modules (TOPLAS) -- the single-producer single-consumer queue; Linux seqlock documentation (kernel locking docs); Boehm 2012, Can seqlocks get along with programming language memory models? (MSPC); POSIX shm_open(3).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Disruptor technical paper (May 2011): mean latency per hop in a three-stage pipeline 52 ns (Disruptor) against 32,757 ns (ArrayBlockingQueue); 99% of observations below 128 ns against 2,097,152 ns; 99.99% below 8,192 ns against 4,194,304 ns; three orders of magnitude lower mean latency and about 8 times the throughput; locks and condition-variable signalling the main cause of the queue's latency | M. Thompson, D. Farley, M. Barker, P. Gee, A. Stewart, Disruptor: High performance alternative to bounded queues for exchanging data between concurrent threads | https://lmax-exchange.github.io/disruptor/files/Disruptor-1.0.pdf | 2026-09-25 | Table 3; "Mean latency per hop for the Disruptor comes out at 52 nanoseconds compared to 32,757 nanoseconds for ArrayBlockingQueue" | hook; section 2 |
| F2 | Lamport, Specifying concurrent program modules, ACM TOPLAS 5(2), April 1983 (the single-producer single-consumer queue without locks) | Crossref record | https://api.crossref.org/works/10.1145/69624.357207 | 2026-09-25 | title, venue, date | section 1 |
| F3 | Linux sequence counters: "a reader-writer consistency mechanism with lockless readers (read-only retry loops), and no writer starvation"; a read is consistent when the count is even at the start and unchanged at the end; data copied out inside the read-side section | Linux kernel documentation, Sequence counters and sequential locks | https://docs.kernel.org/locking/seqlock.html | 2026-09-25 | quote as given | section 3 |
| F4 | Boehm, Can seqlocks get along with programming language memory models?, MSPC 2012 | Crossref record | https://api.crossref.org/works/10.1145/2247684.2247688 | 2026-09-25 | title, venue, date | section 3 |
| F5 | POSIX shared memory: shm_open creates or opens a shared memory object, a handle unrelated processes can mmap to share a region | shm_open(3) man page | https://man7.org/linux/man-pages/man3/shm_open.3.html | 2026-09-25 | "A POSIX shared memory object is in effect a handle which can be used by unrelated processes to mmap(2) the same region of shared memory" | section 4 |

## EXCLUDED


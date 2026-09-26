# 11. Lock-Free Programming — brief and source ledger

## Brief

- **Hook.** In 1997 a spacecraft on Mars kept resetting itself: a low-priority task held a lock that a high-priority task needed while a medium-priority task ran. A trading thread waiting on a logger's lock has the same problem, only faster.
- **Sections.** Atomics and the memory model; Memory ordering: acquire, release, sequential consistency; Compare-and-swap loops and the ABA problem; Safe memory reclamation; Progress guarantees.
- **Defines.** atomic operation, memory ordering, acquire--release ordering, sequential consistency, compare-and-swap, ABA problem, hazard pointer, epoch-based reclamation, lock-free, wait-free, priority inversion.
- **Uses (defined earlier).** data race (ch9), cache coherence (ch3), false sharing (ch3), out-of-order execution (ch2).
- **Tutorial.** A Treiber stack in C++ with a tagged pointer against the ABA problem, stress-tested under the thread sanitiser; a counter under a mutex, a compare-and-swap loop, a fetch-add and per-thread counters, scaled from one to eight threads; the same stack in Rust, where the borrow checker forces the reclamation question into the open. End state: a scaling chart of operations per second by design and thread count, measured on this laptop.
- **Build.** `firm.mpmcq`: a bounded multi-producer multi-consumer queue (per-slot sequence numbers) with stress tests that check every item is delivered exactly once; C++20 and Rust.
- **Weekend problem.** The descheduled lock holder -- named result: the expected time per second the trading thread spends blocked behind a logger's mutex, given the logger's hold time and the chance it is descheduled while holding it, against zero for the lock-free queue.
- **Data.** Measured on this laptop only.
- **Facts to verify.** Jones 1997, What really happened on Mars (Pathfinder priority inversion, Reeves account); Boehm and Adve 2008, Foundations of the C++ concurrency memory model (PLDI); Herlihy 1991, Wait-free synchronization (TOPLAS); Treiber 1986, Systems programming: coping with parallelism (IBM RJ 5118); Michael 2004, Hazard pointers (IEEE TPDS); Fraser 2004, Practical lock-freedom (Cambridge PhD thesis).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Mars Pathfinder (1997): total system resets; a low-priority meteorological task held a mutex needed by the high-priority information bus task while the medium-priority communications task ran (priority inversion); fixed by uploading a short C program that enabled priority inheritance on the mutex | M. Jones, What really happened on Mars Rover Pathfinder, 7 December 1997 (account of D. Wilner's keynote at the IEEE Real-Time Systems Symposium) | https://www.cs.cornell.edu/courses/cs614/1999sp/papers/pathfinder.html | 2026-09-25 | "The spacecraft began experiencing total system resets, each resulting in losses of data"; "changed the values of these variables from FALSE to TRUE" | hook, section 5 |
| F2 | Herlihy, Wait-free synchronization, ACM TOPLAS 13(1), January 1991 | Crossref record | https://api.crossref.org/works/10.1145/114005.102808 | 2026-09-25 | title, venue, date | section 5, omsources |
| F3 | Michael, Hazard pointers: safe memory reclamation for lock-free objects, IEEE TPDS 15(6), June 2004 | Crossref record | https://api.crossref.org/works/10.1109/tpds.2004.8 | 2026-09-25 | title, venue, date | section 4 |
| F4 | Fraser, Practical lock-freedom, University of Cambridge Computer Laboratory technical report UCAM-CL-TR-579, February 2004 (epoch-based reclamation) | Cambridge technical report page | https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-579.html | 2026-09-25 | "Practical lock-freedom, Keir Fraser, February 2004, 116 pages" | section 4 |
| F5 | Boehm and Adve, Foundations of the C++ concurrency memory model, PLDI 2008 (ACM SIGPLAN Notices 43(6)) | Crossref record | https://api.crossref.org/works/10.1145/1379022.1375591 | 2026-09-25 | title, venue, date | section 1, omsources |
| F6 | D. Vyukov's bounded MPMC queue: array of cells with sequence numbers; "not lockfree in the official meaning, just implemented by means of atomic RMW operations w/o mutexes. The cost of enqueue/dequeue is 1 CAS per operation"; no dynamic memory allocation during operation | 1024cores.net, Bounded MPMC queue (archived copy; the domain has since expired) | http://web.archive.org/web/2020id_/http://www.1024cores.net/home/lock-free-algorithms/queues/bounded-mpmc-queue | 2026-09-25 | quote as given | build |

## EXCLUDED


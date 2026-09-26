# 10. Managed and Functional Languages on the Desk — brief and source ledger

## Brief

- **Hook.** An exchange built in Java processed millions of orders a second on a single thread; its authors pre-allocated everything, kept the business logic free of locks, and wrote about it in public.
- **Sections.** Garbage collection and its pauses; The low-latency managed style: pre-allocation, off-heap memory, warm-up; Just-in-time compilation and deoptimisation; The functional-language shops; Choosing a language for a desk.
- **Defines.** garbage collector, stop-the-world pause, off-heap memory, just-in-time compilation, warm-up period, deoptimisation.
- **Uses (defined earlier).** object pool (ch6), latency histogram (ch5), tail latency (ch1).
- **Tutorial.** Python is the managed language at hand: record every garbage-collector pause through gc.callbacks while a message loop allocates, then pre-allocate NumPy record buffers and freeze the heap, and compare the pause distributions and the loop's tail. End state: two pause histograms and the loop's percentiles, measured on this laptop.
- **Build.** `firm.gcwatch`: a pause and allocation-rate monitor for the firm's Python services (gc callbacks into firm.lathist's Python histogram), with a pre-allocated message pool; acceptance: no full collection during the steady-state loop; Python.
- **Weekend problem.** The garbage budget -- named result: the bytes a managed-language engine may allocate per order so that the young generation fills less than once in a trading session, for a given heap and message rate.
- **Data.** Measured on this laptop only.
- **Facts to verify.** Fowler 2011, The LMAX Architecture (orders per second on one thread); Thompson, Farley, Barker, Gee and Stewart 2011, Disruptor technical paper; Minsky and Weeks 2008, Caml trading (Journal of Functional Programming) and Minsky 2011, OCaml for the masses (ACM Queue); OpenJDK JEP 333 / JEP 377 ZGC pause-time goals (dated); Python gc module documentation (gc.freeze, gc.callbacks).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | LMAX: a Business Logic Processor that can handle 6 million orders per second on a single thread, on the JVM, in memory with event sourcing; ring buffers of 20 million slots (input) and 4 million (outputs); the Disruptor is a ring buffer; "At this scale of latency, you have to be aware of the garbage collector" | M. Fowler, The LMAX Architecture, 12 July 2011 | https://martinfowler.com/articles/lmax.html | 2026-09-25 | "a Business Logic Processor that can handle 6 million orders per second on a single thread"; "20 million slots for input buffer" | hook; section 2 |
| F2 | Jane Street Capital uses OCaml as its primary development language: over twenty OCaml programmers and hundreds of thousands of lines of OCaml, for critical trading systems, research, systems software and administration; valued for readable, correct, efficient code | Y. Minsky and S. Weeks, Caml trading: experiences with functional programming on Wall Street, Journal of Functional Programming 18(4), 2008 (abstract via Crossref) | https://api.crossref.org/works/10.1017/s095679680800676x | 2026-09-25 | "We have over twenty OCaml programmers and hundreds of thousands of lines of OCaml code"; "readable, correct, efficient code" | section 4 |
| F3 | Y. Minsky, OCaml for the Masses, ACM Queue 9(9), September 2011 (Jane Street) | Crossref record | https://api.crossref.org/works/10.1145/2030256.2038036 | 2026-09-25 | title, venue, date | omsources |
| F4 | OpenJDK ZGC (JEP 333): GC pause times should not exceed 10 ms; stop-the-world phases limited to root scanning; JEP 376: less than one millisecond should be spent inside ZGC safepoints on typical machines | OpenJDK JEP 333 and JEP 376 | https://openjdk.org/jeps/333 | 2026-09-25 | "GC pause times should not exceed 10ms"; JEP 376 (https://openjdk.org/jeps/376): "Less than one millisecond should be spent inside ZGC safepoints on typical machines" | dat:ll:managed-and-functional-languages-on-the-desk:jvm |
| F5 | CPython gc module: generational collector with thresholds (default 700, 10, 10); gc.callbacks invoked before and after each collection; gc.freeze moves all tracked objects to a permanent generation ignored by future collections | Python 3 documentation, gc module | https://docs.python.org/3/library/gc.html | 2026-09-25 | "gc.freeze(): Freeze all the objects tracked by the garbage collector; move them to a permanent generation and ignore them in all the future collections"; "gc.callbacks ... invoked before and after collection" | tutorial; build |
| F6 | OCaml runtime: a generational collector with a small, fixed-size minor heap (collected by a fast copying collector) and a major heap collected incrementally (mark and sweep) | Real World OCaml, Understanding the Garbage Collector | https://dev.realworldocaml.org/garbage-collector.html | 2026-09-25 | "The minor heap is where most of your short-lived values are held"; "The mark-and-sweep phases run incrementally over slices of the heap to avoid pausing the application for long periods of time" | section 4 |

## EXCLUDED


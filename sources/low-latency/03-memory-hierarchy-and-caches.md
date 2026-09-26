# 3. Memory Hierarchy and Caches — brief and source ledger

## Brief

- **Hook.** An order-book update costs a few nanoseconds when its price level is in the first-level cache and about a hundred when it is not: most of the difference between a fast book and a slow one is where its bytes live.
- **Sections.** Cache levels, lines and associativity; Coherence and false sharing; Translation buffers and huge pages; Prefetching and access patterns.
- **Defines.** cache line, set-associative cache, cache miss, cache coherence, false sharing, translation lookaside buffer, huge page, hardware prefetching, working set.
- **Uses (defined earlier).** hot path (ch1), microbenchmark (ch2).
- **Tutorial.** Measure the memory staircase with a pointer chase through a random cyclic permutation of growing size; measure two threads incrementing counters on one cache line and on padded lines; repeat a random-access loop over 1 GiB with and without transparent huge pages (madvise). End state: the staircase chart with this laptop's cache sizes marked, and a false-sharing bar chart.
- **Build.** `firm.memkit`: cache-line padding (CachePadded), aligned allocation, huge-page-backed buffers with fallback, a pointer-chase probe; C++20 and Rust.
- **Weekend problem.** The staircase -- named result: the latency of each level read off the pointer-chase curve and the number of instruments whose book fits in the second-level cache.
- **Data.** Measured on this laptop only.
- **Facts to verify.** Drepper 2007, What every programmer should know about memory; Papamarcos and Patel 1984, MESI protocol (ISCA); Linux transparent hugepage documentation (admin-guide/mm/transhuge); cache sizes of the laptop from lscpu and Intel documentation (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Redwood Cove (Meteor Lake P-core): L2 ("mid-level cache") of 2 MB on client parts; L3 latency of 75+ cycles against AMD's about 50 | Chips and Cheese, Intel's Redwood Cove: Baby Steps are Still Steps, 22 Sep 2024 | https://chipsandcheese.com/p/intels-redwood-cove-baby-steps-are-still-steps | 2026-09-25 | "Mid-level-cache size increased to 2 MBs for Client"; "At L3, Intel has 75+ cycle L3 latency compared to AMD's approximately 50 cycle latency" | section 1 |
| F2 | Meteor Lake with LPDDR5X-7467: DRAM latency about 153 ns from E-cores; 175.3 ns from LP E-cores with the memory controller not in a low-power state; over 200 ns in low-power conditions | Chips and Cheese, Update on Meteor Lake DRAM Latency Measurements, 27 May 2024 | https://chipsandcheese.com/p/update-on-meteor-lake-dram-latency-measurements | 2026-09-25 | "DRAM latency from E-Cores was measured at about 153 ns"; "the LPE-Cores see 175.3 ns of DRAM latency" | section 1, figure |
| F3 | Transparent huge pages: in madvise mode only regions marked MADV_HUGEPAGE get huge pages (the default); a single TLB entry maps more memory, and a TLB miss runs faster, especially with virtualization using nested page tables | Linux kernel documentation, admin-guide/mm/transhuge | https://docs.kernel.org/admin-guide/mm/transhuge.html | 2026-09-25 | "a single TLB entry will be mapping a much larger amount of virtual memory"; "the TLB miss will run faster (especially with virtualization using nested pagetables...)"; madvise "is the default behaviour" | section 3 |
| F4 | Drepper's survey of the memory hierarchy for programmers (caches, TLBs, NUMA, prefetching), 2007 | U. Drepper, What every programmer should know about memory, LWN series, 2007 | https://lwn.net/Articles/250967/ | 2026-09-25 | series index, part 1 of 9 | omsources |
| F5 | MESI (Illinois) cache-coherence protocol | M. Papamarcos and J. Patel, A low-overhead coherence solution for multiprocessors with private cache memories, ISCA 1984 | https://doi.org/10.1145/800015.808204 | 2026-09-25 | DOI record | section 2 |

## EXCLUDED


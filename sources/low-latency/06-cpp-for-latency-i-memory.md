# 6. C++ for Latency I: Memory — brief and source ledger

## Brief

- **Hook.** A strategy ran at a steady two microseconds a message, except once or twice a minute when it took several hundred: the tail was the allocator, taking its slow path and faulting in a fresh page.
- **Sections.** Object layout, padding and alignment; What an allocation costs, and when; Arenas, pools and free lists; Small buffers and fixed-capacity containers; Page faults and pre-faulting.
- **Defines.** structure padding, arena allocator, object pool, free list, small-buffer optimisation, fixed-capacity container, page fault, pre-faulting.
- **Uses (defined earlier).** cache line (ch3), working set (ch3), latency histogram (ch5), hot path (ch1).
- **Tutorial.** Count heap allocations with a replaced global operator new; measure the latency distribution of new/delete against a pool and a monotonic arena (std::pmr and hand-written); reorder a message struct's fields and watch its size and its line count change; count page faults with getrusage before and after pre-faulting. End state: allocation counts per message and the tail of each allocator, measured on this laptop.
- **Build.** `firm.arena`: arena, fixed-size object pool with an intrusive free list, fixed-capacity vector and string, and an allocation counter used by every later acceptance test to assert zero allocations on the hot path; C++20 and Rust.
- **Weekend problem.** Four hundred microseconds, once a minute -- named result: allocations and page faults per message before and after the rewrite (from seven and a fault every few thousand messages to zero), and the tail they removed.
- **Data.** Measured on this laptop only.
- **Facts to verify.** glibc malloc tunables: mmap threshold and trim threshold defaults (manual, dated); libstdc++ std::string small-string capacity (15 characters); C++17 polymorphic memory resources (standard, [mem.res]).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | glibc malloc: allocations at or above M_MMAP_THRESHOLD that the free list cannot satisfy use mmap, which the kernel must zero; default 128*1024, adjusted upward dynamically when larger blocks are freed; M_TRIM_THRESHOLD default 128*1024: free() returns top-of-heap memory with sbrk above it | mallopt(3) man page | https://man7.org/linux/man-pages/man3/mallopt.3.html | 2026-09-25 | "leads to a default setting of 128*1024 for the M_MMAP_THRESHOLD parameter"; "Nowadays, glibc uses a dynamic mmap threshold by default"; "The default value for this parameter is 128*1024" (M_TRIM_THRESHOLD) | section 2 |
| F2 | C++17 polymorphic memory resources: std::pmr::memory_resource, monotonic_buffer_resource, unsynchronized_pool_resource | cppreference, std::pmr::memory_resource | https://en.cppreference.com/w/cpp/memory/memory_resource | 2026-09-25 | header <memory_resource>, since C++17; classes listed | section 3 |

## EXCLUDED


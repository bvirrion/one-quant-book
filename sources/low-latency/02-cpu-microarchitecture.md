# 2. CPU Microarchitecture — brief and source ledger

## Brief

- **Hook.** The same twelve lines of C++ ran six times faster on sorted input than on shuffled input: nothing in the source changed, only how often the processor guessed a branch right.
- **Sections.** Pipelines and superscalar execution; Out-of-order execution and the reorder buffer; Branch prediction and its misses; Frequency scaling, turbo and idle states; Simultaneous multithreading and heterogeneous cores.
- **Defines.** microbenchmark, compiler barrier, time-stamp counter, instruction pipeline, out-of-order execution, reorder buffer, branch prediction, branch misprediction, instructions per cycle, dynamic frequency scaling, idle state, simultaneous multithreading, heterogeneous cores.
- **Uses (defined earlier).** hot path (ch1), jitter (ch1).
- **Tutorial.** C++ microbenchmarks with a cycle counter: a branchy filter on sorted and shuffled data and its branchless rewrite; one dependency chain against four independent accumulators; the same loop pinned with taskset to a performance core and to an efficiency core of this hybrid laptop. End state: a chart of cycles per element by variant and core type.
- **Build.** `firm.ubench`: the microbenchmark harness every later chapter uses -- warm-up, repetitions, an optimisation barrier, rdtscp and steady-clock timers, raw samples to CSV; C++20 header and Rust twin.
- **Weekend problem.** The branch that cost a quote -- named result: the expected cycles per message lost to one data-dependent branch at a given misprediction rate, and the rate above which the branchless version wins.
- **Data.** Measured on this laptop only.
- **Facts to verify.** Stack Overflow question 11227809 (2012), why is processing a sorted array faster; Intel 64 and IA-32 Architectures Optimization Reference Manual: misprediction penalty, reorder-buffer size of the performance core (dated); Intel product page of the Core Ultra 7 155H: 6 P + 8 E + 2 LP-E cores, turbo frequency (dated); Agner Fog, The microarchitecture of Intel, AMD and VIA CPUs.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Stack Overflow question 11227809 (asked 2012-06-27): summing elements >= 128 of 32,768 random values; unsorted 11.54 s, sorted 1.93 s, ~6x | Stack Overflow, via the Stack Exchange API | https://api.stackexchange.com/2.3/questions/11227809?site=stackoverflow&filter=withbody | 2026-09-25 | "Without std::sort... runs in 11.54 seconds. With the sorted data, the code runs in 1.93 seconds"; "~6x faster" | hook; section 3 |
| F2 | Intel Core Ultra 7 155H: 16 cores (6 performance, 8 efficient, 2 low-power efficient), 22 threads, P-core max turbo 4.8 GHz, E-core max turbo 3.8 GHz, 24 MB cache, launched Q4 2023 | Intel product specifications | https://www.intel.com/content/www/us/en/products/sku/236847/intel-core-ultra-7-processor-155h-24m-cache-up-to-4-80-ghz/specifications.html | 2026-09-25 | "Total Cores 16... Performance-cores 6... Efficient-cores 8... Low Power Efficient-cores 2... Total Threads 22... 4.8 GHz... 3.8 GHz" | dat:ll:cpu-microarchitecture:laptop |
| F3 | Golden Cove: reorder buffer of 512 entries (45% larger than Sunny Cove's); rename width 6 per cycle; six decoders | Chips and Cheese, Popping the Hood on Golden Cove, 2 Dec 2021 | https://chipsandcheese.com/p/popping-the-hood-on-golden-cove | 2026-09-25 | "Golden Cove's reorder buffer is a staggering 45% larger than Sunny Cove's" (512 entries); "increases rename width to 6 instructions per cycle" | section 2 |
| F4 | Golden Cove's renamer can execute up to 6 dependent adds with small immediates per cycle | Chips and Cheese, Lion Cove: Intel's P-Core Roars, 27 Sep 2024 | https://chipsandcheese.com/p/lion-cove-intels-p-core-roars | 2026-09-25 | "the ability to execute up to 6 dependent adds with small immediates per cycle" | section 2, figure |
| F5 | On Alder Lake P-cores the branch misprediction penalty is high, sometimes exceeding 20 clock cycles; the core can sustain six instructions per cycle;  integer addition with a small immediate constant has zero latency in some cases; a floating-point addition has a latency of 2 cycles when followed by another addition | A. Fog, The microarchitecture of Intel, AMD and VIA CPUs (updated 2026-05-23) | https://www.agner.org/optimize/microarchitecture.pdf | 2026-09-25 | "The penalty for branch misprediction is high, sometimes exceeding 20 clock cycles in my measurements"; "steady throughput of six instructions per clock cycle per core"; "Integer addition with a small immediate constant has zero latency in some cases"; "[latency of] 2 clock cycles when followed by another addition instruction, and 3 clock cycles otherwise" | sections 2 and 3 |

## EXCLUDED


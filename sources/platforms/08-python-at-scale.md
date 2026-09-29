# 8. Python at Scale — brief and source ledger

## Brief

- **Hook.** A researcher's loop over one day's 800,000 order-book messages took four minutes; the same computation written over arrays took under a second, and the version that computed a year in chunks never held more than a few hundred megabytes: the language was the same, the cost model was not.
- **Sections.** What the interpreter costs; Thinking in arrays; Memory: objects, arrays and copies; Chunks and out-of-core loops; Processes, threads and the interpreter lock.
- **Defines.** interpreter overhead, global interpreter lock, array programming, chunked processing, process-based parallelism, serialisation cost, peak resident memory.
- **Uses (defined earlier).** just-in-time compilation (B13.10), garbage collector (B13.10), SIMD (B13.14), cache miss (B13.3), shared-memory transport (B13.12), floating-point number (B4.25), compensated summation (B4.25), tick store (ch4), columnar layout (ch3).
- **Tutorial.** Compute order-flow imbalance and a rolling spread over a day of messages four ways -- a Python loop, a loop over preallocated arrays, numpy array expressions, and chunks of the day streamed from the tick store -- measuring time per message and peak resident memory; compare a pandas object column, a categorical and an Arrow string array; hand a large array to a second process by pickling and by shared memory. End state: a chart of nanoseconds per message by method and a table of peak memory by representation.
- **Build.** `firm.pyscale`: a chunked pipeline runner (source iterator, per-chunk kernel with carried state, bounded memory), a memory and time probe (tracemalloc, resource peak RSS), and the carried-state helpers (rolling windows across chunk boundaries) with tests that chunked and whole-day results agree; Python.
- **Weekend problem.** Four minutes or one second -- named result: the speed-up of the array version over the loop, the chunk size that minimises time within a fixed memory budget, and the largest history that fits the budget.
- **Facts to verify.** Python documentation: the global interpreter lock and the free-threaded build (PEP 703, dated); numpy documentation: broadcasting and ufuncs; Python multiprocessing.shared_memory documentation; pandas documentation: categorical and Arrow-backed string dtypes.
- **Data.** The chapter 4 store's generated day; measured on this laptop.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | PEP 703, Making the Global Interpreter Lock Optional in CPython: status Final, Python version 3.13; adds a build configuration (--disable-gil) to run Python code without the GIL; the GIL remains the default | Python Enhancement Proposals | https://peps.python.org/pep-0703/ | 2026-09-28 | "Status: Final"; "Python-Version: 3.13"; "This PEP proposes adding a build configuration (--disable-gil) to CPython to let it run Python code without the global interpreter lock" | dat:pl:python-at-scale:freethreading; omsources |
| F2 | Starting with the 3.13 release, CPython supports a free-threaded build with the GIL disabled; the official macOS and Windows installers optionally install free-threaded binaries | Python documentation, Python support for free threading | https://docs.python.org/3/howto/free-threading-python.html | 2026-09-28 | "Starting with the 3.13 release, CPython has support for a build of Python called free threading where the global interpreter lock (GIL) is disabled."; "the official macOS and Windows installers optionally support installing free-threaded Python binaries" | dat:pl:python-at-scale:freethreading; omsources |
| F3 | multiprocessing.shared_memory provides SharedMemory for allocation and management of shared memory accessed by one or more processes, avoiding serialisation and copying | Python documentation, multiprocessing.shared_memory | https://docs.python.org/3/library/multiprocessing.shared_memory.html | 2026-09-28 | "for the allocation and management of shared memory to be accessed by one or more processes"; "compared to sharing data via disk or socket or other communications requiring the serialization/deserialization and copying of data" | section 5; omsources |

## EXCLUDED

- The brief's hook numbers (four minutes, 800,000 messages) were replaced by the chapter's own measurements.


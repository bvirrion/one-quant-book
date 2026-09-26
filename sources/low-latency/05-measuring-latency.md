# 5. Measuring Latency — brief and source ledger

## Brief

- **Hook.** A service's 99th percentile improved after a change that made it slower: the load generator waited for each reply before sending the next request, so during every stall it simply stopped measuring.
- **Sections.** Clocks: cycle counters and the kernel's clocks; Timestamping at the wire; Histograms and percentiles; Coordinated omission; Profilers and hardware counters.
- **Defines.** invariant time-stamp counter, hardware timestamp, latency histogram, coordinated omission, measurement overhead, sampling profiler, hardware performance counter.
- **Uses (defined earlier).** exchange timestamp (B1.28), receive timestamp (B1.28), tail latency (ch1), jitter (ch1), time-stamp counter (ch2), microbenchmark (ch2), bootstrap percentile interval (B4.13).
- **Tutorial.** Calibrate the time-stamp counter against the steady clock and measure the cost of each clock call; fill a log-linear histogram; drive a service with periodic stalls by a closed-loop and by an open-loop load generator, with and without the correction. End state: two percentile curves that disagree above the 90th percentile, measured on this laptop.
- **Build.** `firm.lathist`: a log-linear latency histogram (bounded relative error, constant-time record, merge, percentiles, serialisation) with coordinated-omission correction and a TSC clock calibrated against the steady clock; C++20, Rust and Python on one shared fixture.
- **Weekend problem.** The benchmark that lied -- named result: the 99.9th percentile reported with and without the correction for a service that stalls 10 ms once a second.
- **Data.** Measured on this laptop; a histogram fixture shared by the three languages.
- **Facts to verify.** Tene, How NOT to measure latency (talk, 2015) and the HdrHistogram documentation; Intel SDM: RDTSC/RDTSCP semantics and the invariant TSC; Linux clock_gettime(2) and the vDSO; Linux perf_event_open(2), perf_event_paranoid; MiFID II RTS 25 clock accuracy (pointer to B1.28).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Intel SDM vol. 3, section 17.15.1 (Invariant TSC): the invariant TSC runs at a constant rate in all ACPI P-, C- and T-states; indicated by CPUID.80000007H:EDX[8]; the OS may use it for wall-clock timer services, its reads being much more efficient than ring transitions or platform timers | Intel 64 and IA-32 Architectures Software Developer's Manual, vol. 3 (mirror of the section) | https://xem.github.io/minix86/manual/intel-x86-and-64-manual-vol3/o_fe12b1e2a880e0ce-615.html | 2026-09-25 | "will run at a constant rate in all ACPI P-, C-. and T-states"; "CPUID.80000007H:EDX[8]" | section 1 |
| F2 | Gil Tene, How NOT to Measure Latency, QCon San Francisco 2015 (recorded 26 March 2016): latency and response-time characterisation and measurement pitfalls | InfoQ | https://www.infoq.com/presentations/latency-response-time/ | 2026-09-25 | title, speaker, conference | hook; section 4 |
| F3 | HdrHistogram: values tracked with configurable significant digits (3 digits: quantisation no larger than 1/1,000 of any value); recordValueWithExpectedInterval adds values linearly decreasing in steps of the expected interval down to the last above it, to correct coordinated omission; example of a 100 s pause | HdrHistogram README (GitHub) | https://github.com/HdrHistogram/HdrHistogram | 2026-09-25 | "additional values, linearly decreasing in steps of expectedIntervalBetweenValueSamples, down to the last value that would still be higher than expectedIntervalBetweenValueSamples" | section 3 and 4 |
| F4 | /proc/sys/kernel/perf_event_paranoid: 2 allows only user-space measurements (default since Linux 4.6); 1 kernel and user; 0 CPU-specific data; -1 no restrictions | perf_event_open(2) man page | https://man7.org/linux/man-pages/man2/perf_event_open.2.html | 2026-09-25 | "2 allow only user-space measurements (default since Linux 4.6)" | section 5 |

## EXCLUDED


# 13. Distributed Compute and Schedulers — brief and source ledger

## Brief

- **Hook.** A parameter sweep of ten thousand backtests was submitted at 18:00 and finished at 09:30 the next day, although the cluster had been idle by 02:00: forty tasks, each thirty times longer than the median, had been scheduled last.
- **Sections.** Clusters and what they are for; Schedulers and queues; Task graphs; Parameter sweeps and stragglers; Caching, failure and cost.
- **Defines.** compute cluster, job scheduler, task graph, embarrassingly parallel workload, parameter sweep, makespan, straggler, speculative execution, fair-share scheduling, work stealing.
- **Uses (defined earlier).** pipeline stage (B7.29), content-addressed storage (B7.29), walk-forward analysis (B7.20), backtest overfitting (B7.20), M/M/1 queue (B4.8), training checkpoint (B12.23), backtest engine (ch11), process-based parallelism (ch8).
- **Tutorial.** Simulate a cluster (nodes, cores, memory classes, failure and preemption rates) as a discrete-event model and schedule a sweep of backtests with lognormal durations under first-in-first-out, longest-first, fair-share between two teams and work stealing; add speculative re-execution of stragglers and content-addressed caching of repeated stages; run a small real sweep through the same scheduler interface on this laptop (one worker). End state: makespan and cost by policy, and a Gantt chart of the naive and the tuned schedules.
- **Build.** `firm.jobgraph`: task graph with resource requests, a scheduler interface with FIFO, longest-processing-time, fair-share and work-stealing policies, a discrete-event cluster simulator (failures, preemption, retries, speculative execution), a local executor with one worker, caching through firm.workflow keys, cost accounting; Python.
- **Weekend problem.** The sweep that finished at 09:30 -- named result: the makespan and node-hours of the 10,000-task sweep under each policy, the gain from speculative execution, and the lower bound the best schedule reaches within.
- **Facts to verify.** Graham 1969, Bounds on multiprocessing timing anomalies (SIAM J. Appl. Math.): list scheduling bounds; Dean and Barroso 2013, The tail at scale (Communications of the ACM); Dean and Ghemawat 2004, MapReduce (OSDI): backup tasks for stragglers; Slurm workload manager documentation: fair-share (dated); Blumofe and Leiserson 1999, work stealing (JACM).
- **Data.** Simulated cluster; task durations calibrated on measured backtests of chapter 11 at small size.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | List scheduling on m identical machines has makespan at most 2 - 1/m times optimal; LPT at most 4/3 - 1/(3m) times optimal; both attributed to Graham 1969 | Wikipedia, List scheduling; Longest-processing-time-first scheduling (secondary, citing Graham 1969); Crossref for the paper | https://en.wikipedia.org/wiki/List_scheduling ; https://en.wikipedia.org/wiki/Longest-processing-time-first_scheduling ; https://api.crossref.org/works/10.1137/0117039 | 2026-09-28 | "makespan is at most 2 - 1/m times the optimal makespan" (Graham 1969); LPT "4/3 - 1/(3m) times the optimal" (Graham 1969); Crossref: "Bounds on Multiprocessing Timing Anomalies", SIAM J. Appl. Math. 17(2) 416-429, 1969 | section Schedulers and queues; exo 1; omsources |
| F2 | MapReduce: stragglers (e.g. a machine with a bad disk, reads from 30 MB/s to 1 MB/s); near completion the master schedules backup executions of in-progress tasks; the sort took 44% longer with backups disabled | Dean and Ghemawat, MapReduce: Simplified Data Processing on Large Clusters, OSDI 2004 | https://www.usenix.org/legacy/event/osdi04/tech/full_papers/dean/dean.pdf | 2026-09-28 | "a machine with a bad disk may experience frequent correctable errors that slow its read performance from 30 MB/s to 1 MB/s"; "When a MapReduce operation is close to completion, the master schedules backup executions of the remaining in-progress tasks"; "takes 44% longer to complete when the backup task mechanism is disabled" | section Parameter sweeps and stragglers; omsources |
| F3 | Slurm Fair Tree: default fair-share algorithm since Slurm 19.05; level fair-share LF = S/U; siblings' children ranked below/above as a block | Slurm documentation, Fair Tree Fairshare Algorithm | https://slurm.schedmd.com/fair_tree.html | 2026-09-28 | "Starting with Slurm 19.05, the Fair-share factor in the priority/multifactor plugin will default to the Fair Tree algorithm"; "LF = S / U"; "if accounts A and B are siblings and A has a higher fairshare factor than B, all children of A will have higher fairshare factors than all children of B" | dat:pl:distributed-compute-and-schedulers:slurm; omsources |
| F4 | Blumofe and Leiserson, Scheduling multithreaded computations by work stealing, JACM 46(5) 720-748, 1999 | Crossref, DOI 10.1145/324133.324234 | https://api.crossref.org/works/10.1145/324133.324234 | 2026-09-28 | title, authors, volume 46, issue 5, pages 720-748, 1999 | def work stealing; omsources |
| F5 | Dean and Barroso, The tail at scale, CACM 56(2) 74-80, 2013 | Crossref, DOI 10.1145/2408776.2408794 | https://api.crossref.org/works/10.1145/2408776.2408794 | 2026-09-28 | title, authors, volume 56, issue 2, pages 74-80, 2013 | omsources |

## EXCLUDED

- Slurm's decayed usage (PriorityDecayHalfLife) described only generally ("usage decays over time"): not quoted; the Fair Tree page fetched does not state the decay mechanism. -> the sentence was removed from the text.


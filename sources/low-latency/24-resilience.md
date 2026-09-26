# 24. Resilience — brief and source ledger

## Brief

- **Hook.** On 1 October 2020 a stock exchange halted trading for a full day: a storage device failed and the automatic switch to its backup did not happen as designed. Failover is a feature that is exercised rarely, and so fails when it is needed.
- **Sections.** Failure modes of a trading system; Sequencer architectures; Replicated state machines and failover; Exchange disconnects and recovery; Testing failover.
- **Defines.** sequencer architecture, replicated state machine, primary--backup replication, failover, split brain, idempotent processing.
- **Uses (defined earlier).** exchange simulator (B10.26), matching engine (B10.1), input journal (ch23), deterministic replay (ch23), cancel on disconnect (B10.26), drop copy (ch21), heartbeat (ch15), operational risk (B6.28).
- **Tutorial.** Model the architecture in Python, then run it in C++: a sequencer that numbers every input, two replicas of the engine and order state applying the journal, the primary killed at every cut point of a short scenario, the backup taking over with a fencing epoch; then the simulator drops the order-entry session and the gateway reconnects, replays from its sequence number and reconciles its open orders. End state: a table of failure points against recovery outcome (state equal, orders duplicated or not) with and without idempotency keys.
- **Build.** `firm.sequencer`: sequencer, journal, replica apply, failover with fencing epochs, and the gateway's reconnect-and-reconcile procedure; Python reference, C++20 and Rust; acceptance: state equality after failover at every cut point of the scenario, no duplicate orders after reconnect.
- **Weekend problem.** The failover that doubled the orders -- named result: duplicate orders sent after a failover without idempotency keys, over the distribution of failure points, and zero with them, with the recovery time achieved.
- **Data.** Book 10 simulator with scheduled session drops.
- **Facts to verify.** Japan Exchange Group / Tokyo Stock Exchange report on the 1 October 2020 system failure; Schneider 1990, Implementing fault-tolerant services using the state machine approach (ACM Computing Surveys); Ongaro and Ousterhout 2014, In search of an understandable consensus algorithm (Raft, USENIX ATC); Fowler 2011, The LMAX Architecture (replicated business logic).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Tokyo Stock Exchange, arrowhead failure of 1 October 2020: a memory module failed in Device 1 of the shared disk device; operations were supposed to switch automatically to Device 2 but did not; automatic switching did not function for a memory module failure unless the device's settings were changed; the settings were changed on 4 October | TSE notice, The Cause of the Recent Failure in arrowhead and Measures Implemented (5 October 2020) | https://www.jpx.co.jp/english/corporate/news/news-releases/0060/b5b4pj000003qm41-att/arrowhead_e.pdf | 2026-09-26 | "A failure occurred in a memory module in Device 1 of the Shared Disk Device in arrowhead. Operations were supposed to switch automatically to Device 2, but switching did not function as expected."; "automatic switching could occur in a failure caused by a memory module failure if the Device settings were changed" | hook; section 1 |
| F2 | TSE's report on the sequence of events: access difficulties detected at 7:04; at 8:36 decision to halt trading of all issues from the 9:00 open; manual switchover to Device 2 succeeded at 9:26; orders received before 8:54 had been matched and their execution notices accumulated without being sent to participants; only a limited number of participants could resend orders; at 11:45 decision to halt for the whole day; no contingency plan for the NAS becoming unavailable and no agreed rules or tests for rebooting and resuming | TSE, The Failure of Equity Trading System on October 1, 2020 (report, 19 October 2020) | https://www.jpx.co.jp/english/corporate/news/news-releases/0060/b5b4pj000003r769-att/trading_system.pdf | 2026-09-26 | "At 9:26 a.m., we succeeded in a manual switchover to Device 2 of NAS, which returned all functions back to normal."; "orders that were received before 8:54 a.m. had been matched and execution notifications had accumulated within arrowhead without being sent to trading participants"; "at 11:45 a.m., we decided to halt trading for the whole day" | hook; section 4 |
| F3 | Schneider, Implementing fault-tolerant services using the state machine approach: a tutorial, ACM Computing Surveys 22(4), 299-319, December 1990 | Crossref record | https://api.crossref.org/works/10.1145/98163.98167 | 2026-09-26 | title, journal, volume, issue, pages, date | section 3 |
| F4 | Ongaro and Ousterhout, In search of an understandable consensus algorithm (Raft), USENIX ATC 2014: a consensus algorithm for managing a replicated log, equivalent to multi-Paxos | USENIX ATC 14 presentation page | https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro | 2026-09-26 | "Raft is a consensus algorithm for managing a replicated log." | section 3 |

## EXCLUDED

- Fowler 2011 (LMAX): already cited in chapter 20 (its ledger row F2); chapter 24 points back to it rather than repeating the source.


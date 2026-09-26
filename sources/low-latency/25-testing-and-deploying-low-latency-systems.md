# 25. Testing and Deploying Low-Latency Systems — brief and source ledger

## Brief

- **Hook.** A release passed every functional test and added a few hundred nanoseconds to the 99th percentile, because one log statement had moved inside the hot loop; the performance gate caught it, after two false alarms the week before had taught the team how to run it.
- **Sections.** The test pyramid for a trading system; Tests backed by the exchange simulator; Exchange certification and conformance; Performance regression gates; Staged rollouts and rollback.
- **Defines.** property-based test, differential test, fuzz testing, exchange certification, performance regression gate.
- **Uses (defined earlier).** exchange simulator (B10.26), matching engine (B10.1), canary deployment (B7.21), staged rollout (B7.21), paper trading (B7.21), permutation test (B4.13), bootstrap (B4.13), power of a test (B4.12), microbenchmark (ch2).
- **Tutorial.** Fuzz the FIX parser with a mutational loop and the sanitisers; property-test the order gateway over random interleavings; run a certification script against the simulator; then gate a planted regression with interleaved A/B benchmark runs and a bootstrap on the percentile ratio, on this noisy shared laptop. End state: the gate's false-alarm rate and detection rate against the number of interleaved runs.
- **Build.** `firm.perfgate`: interleaved A/B benchmark runner, bootstrap and permutation comparison of latency percentiles, thresholds and a report, plus a certification-script runner against the simulator; Python.
- **Weekend problem.** A few hundred nanoseconds -- named result: the number of interleaved runs the gate needs to detect a 5% rise in the 99th percentile with 90% power at this machine's measured noise.
- **Data.** Measured on this laptop; Book 10 simulator for the certification script.
- **Facts to verify.** Claessen and Hughes 2000, QuickCheck (ICFP); Commission Delegated Regulation (EU) 2017/589 (RTS 6): testing of algorithms and conformance testing (articles 5-7); a major exchange's certification requirements before production access (dated); Beyer et al., Site Reliability Engineering (canarying releases).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Claessen and Hughes, QuickCheck: a lightweight tool for random testing of Haskell programs, Proceedings of the fifth ACM SIGPLAN International Conference on Functional Programming (ICFP), 2000, pp. 268-279 | Crossref record | https://api.crossref.org/works/10.1145/351240.351266 | 2026-09-26 | title, proceedings, pages, date | section 1 |
| F2 | RTS 6: methodologies to develop and test algorithmic trading systems before deployment or substantial update (art. 5(1)); conformance testing with the trading venue's system when becoming a member, first sponsored access, material change of the venue's systems, and before deploying or materially updating the algorithm (art. 6(1)); it verifies interaction with the venue's matching logic and processing of its data flows (art. 6(2)); testing in an environment separated from production (art. 7(1)) | Commission Delegated Regulation (EU) 2017/589, EUR-Lex | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0589 | 2026-09-26 | "Prior to the deployment or substantial update of an algorithmic trading system, trading algorithm or algorithmic trading strategy, an investment firm shall establish clearly delineated methodologies to develop and test such systems"; "interacts with the trading venue's matching logic as intended"; "an environment that is separated from its production environment" | section 3; dat:ll:testing-and-deploying-low-latency-systems:cert |
| F3 | CME Group requires all client systems transacting on CME Globex through iLink order routing or processing its market data to be certified by AutoCert+, an automated testing tool for validating client system functionality | CME Group Client Systems Wiki, Client Application Testing and Certification | https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457315236/Client+Application+Testing+and+Certification | 2026-09-26 | "CME Group requires that all client systems transacting on CME Globex via iLink order routing or processing CME Group market data are certified by AutoCert+"; "an automated testing tool for validating client system functionality" | section 3; dat:ll:testing-and-deploying-low-latency-systems:cert |

## EXCLUDED

- Beyer et al., Site Reliability Engineering (brief): not needed; canary deployment and staged rollout are defined and sourced in Book 7, chapter 21, and this chapter points there.


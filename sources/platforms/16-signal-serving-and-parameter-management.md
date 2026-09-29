# 16. Signal Serving and Parameter Management — brief and source ledger

## Brief

- **Hook.** A risk parameter entered as 50 meant fifty basis points to the person who typed it and fifty percent to the strategy that read it; nothing checked the unit, the change went to every strategy at once, and the first sign was the fill rate.
- **Sections.** From research signal to production input; The signal service; Configuration as data; Schemas, approvals and history; Rolling out a change.
- **Defines.** signal service, parameter store, configuration as data, configuration schema, feature flag, configuration drift.
- **Uses (defined earlier).** parameter change control (B11.28), canary deployment (B7.21), staged rollout (B7.21), audit trail (B12.25), model registry (B12.25), handoff specification (B12.28), shadow deployment (B12.27), feature freshness (B12.24), feature store (B12.24), four-eyes principle (B16.12), valid time (B7.3), knowledge time (B7.3), reproducible result (B7.29).
- **Tutorial.** Publish a research signal through a signal service with a version, a freshness bound and a fallback; store every strategy parameter in a parameter store with a typed schema (units, bounds), effective-dated and hash-chained history, and two approvals for changes above a threshold; replay the units error, caught by the schema; roll out a legitimate change behind a feature flag to one strategy, then all; answer what was live at 10:31 last Tuesday. End state: the timeline of the change with the exposure accrued under each rollout policy.
- **Build.** `firm.paramstore`: typed parameter schemas (unit, bounds, allowed change per step), versioned values with effective and recorded times, approvals, a hash-chained audit trail (on firm.exptrack), feature flags by strategy, drift detection between declared and running configuration, and `SignalService` (versioned values, freshness, fallback); Python.
- **Weekend problem.** Fifty of what? -- named result: the exposure accrued before detection by an unchecked units error under an all-at-once change, a staged rollout and a schema check, and the minutes to detection in each case.
- **Facts to verify.** a public incident caused by a configuration or parameter error at a trading firm or venue (regulator or court record, dated); Beyer et al. 2016, Site Reliability Engineering (O'Reilly): configuration management and progressive rollout chapters; Tang et al. 2015, Holistic configuration management at Facebook (SOSP).
- **Data.** firm.exchsim sessions with a planted parameter change; synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Knight Capital, 1 August 2012: a flag formerly used to activate Power Peg was repurposed for the new RLP code; the new code was not deployed to one of eight SMARS servers; orders with the repurposed flag triggered Power Peg there; about 45 minutes; loss of more than $460 million | US SEC, In the Matter of Knight Capital Americas LLC, Release No. 34-70694 (2013) | https://www.sec.gov/litigation/admin/2013/34-70694.pdf | 2026-09-28 | "The new RLP code also repurposed a flag that was formerly used to activate the Power Peg code"; "one of the eight SMARS computer servers"; "orders sent with the repurposed flag to the eighth server triggered the defective Power Peg code"; "approximately forty-five minutes on August 1 and, ultimately, Knight lost more than $460 million" | section Rolling out a change; dat:pl:signal-serving-and-parameter-management:scale; omsources |
| F2 | Facebook's configuration management handles thousands of online configuration changes and trillions of configuration checks; used for product rollouts, A/B experiments, load balancing, ML model deployment | Tang et al., Holistic Configuration Management at Facebook, SOSP 2015 (publication page abstract) | https://research.facebook.com/publications/holistic-configuration-management-at-facebook/ | 2026-09-28 | "thousands of online configuration changes"; "trillions of configuration checks"; use cases listed | dat:pl:signal-serving-and-parameter-management:scale; omsources |

## EXCLUDED

- Beyer et al. 2016, Site Reliability Engineering (brief): not fetched; canary and staged rollout are taken from Book 7 chapter 21.
- Facebook paper's claims about configuration errors causing incidents: not in the abstract fetched; not claimed.


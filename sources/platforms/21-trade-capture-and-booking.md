# 21. Trade Capture and Booking — brief and source ledger

## Brief

- **Hook.** A swap was amended three times in a week -- a notional change, a counterparty novation, a partial termination -- and the risk system, the confirmation system and the settlement system each held a different version of it on Friday, because each had copied the trade instead of following its events.
- **Sections.** What a trade is, as data; Capture: from execution to booked trade; Booking models and books; The lifecycle as events; Allocations and straight-through processing.
- **Defines.** trade capture, booking, booking model, canonical trade model, trade lifecycle event, trade amendment, unique transaction identifier, block allocation, straight-through processing.
- **Uses (defined earlier).** novation (B1.5), clearing (B1.5), give-up (B1.30), ISDA master agreement (B2.28), legal entity identifier (B2.28), interest-rate swap (B2.9), trade reporting (B2.22), execution report (B10.26), order management system (B10.20), trading book (B6.23), fictitious trade (B6.28), event sourcing (ch24), system of record (ch1).
- **Tutorial.** Capture fills from firm.exchsim and two OTC tickets into a canonical trade model (a header with identifiers, parties, book and dates, and the instrument as firm.pricing's JSON); allocate a block fill to three funds with a fair rounding rule; apply a lifecycle of amendments, a novation, a partial termination and an exercise as events, and rebuild any version of the trade as of any time; check that risk, confirmation and settlement views read the same event stream. End state: the trade's versions through the week and the allocation's residuals.
- **Build.** `firm.tradecap`: canonical trade model (JSON schema, validation), capture adapters (exchange execution reports, OTC tickets), block allocation with average price and a deterministic residual rule, lifecycle events (new, amend, cancel, novate, partially terminate, exercise, allocate) applied by event sourcing with versioned state and `as_of(time)`, booking model (book tree, booking rules by instrument and desk), and a unique-transaction-identifier generator; Python.
- **Weekend problem.** Three versions on Friday -- named result: the number of downstream disagreements after a week of lifecycle events under copy-based and event-based distribution, and the allocation residuals of a block split among three funds under three rounding rules.
- **Facts to verify.** ISDA Common Domain Model (CDM) documentation: trade lifecycle events; FpML specification (trade representation); CPMI-IOSCO Technical guidance on the harmonisation of the Unique Transaction Identifier (2017); SEC or FINRA rules on block allocation for investment advisers (pointer only if sourced, dated).
- **Data.** firm.exchsim fills and synthetic OTC tickets.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CPMI-IOSCO UTI technical guidance (28 February 2017): new UTIs = the LEI of the generating entity concatenated with a unique value created by that entity; max 52 characters; only A-Z and 0-9; no check digit | CPMI and IOSCO, Harmonisation of the Unique Transaction Identifier: Technical Guidance (CPMI Papers 158) | https://www.bis.org/publications/harmonisation-unique-transaction-identifier-technical-guidance.pdf | 2026-09-28 | "structured as a concatenated combination of the LEI of the generating entity at the point of generation and a unique value created by that entity"; "a maximum of 52 characters"; "constructed solely from the upper-case alphabetic characters A-Z or the digits 0-9"; "no need to ... include a check digit" | def UTI; dat:pl:trade-capture-and-booking:standards; omsources |
| F2 | ISDA CDM event model: "A lifecycle event describes a state transition"; primitive instructions include execution, quantity change, terms change, party change, exercise, contract formation, reset, transfer, split | FINOS/ISDA Common Domain Model documentation, Event Model | https://cdm.finos.org/docs/event-model | 2026-09-28 | "A lifecycle event describes a state transition. There must be different before/after trade states based on that lifecycle event."; list of primitive instructions | section The lifecycle as events; dat box; omsources |

## EXCLUDED

- FpML specification: mentioned by name only.
- SEC/FINRA block-allocation rules for advisers (brief): not searched; no regulatory claim made.


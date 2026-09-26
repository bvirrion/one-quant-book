# 21. Order Gateway and Order Management — brief and source ledger

## Brief

- **Hook.** A strategy cancelled an order and, a few microseconds later, sent its replacement; the cancel crossed a fill on the way, the exchange rejected it as too late, and for a moment the firm held twice the position it believed it held.
- **Sections.** The order state machine; Acknowledgements, in-flight orders and races; Throttles and message budgets; Sessions: login, sequence numbers, cancel on disconnect; Drop copies and reconciliation.
- **Defines.** order gateway, order state machine, in-flight order, cancel--fill race, token bucket, drop copy.
- **Uses (defined earlier).** exchange simulator (B10.26), matching engine (B10.1), order lifecycle (B7.17), partial fill (B7.17), rate limit (B3.15), execution report (B10.26), order-entry protocol (B10.26), order-entry session (B10.26), cancel on disconnect (B10.26), self-trade prevention (B10.26), order management system (B10.20), message throttle (B11.10), position (B1.7).
- **Tutorial.** Connect the C++ gateway to the simulator's order-entry session: a table-driven state machine, conservative position accounting for in-flight orders, a token-bucket throttle; inject cancel-fill races through the simulator's latency model; reconcile the gateway's view against the drop-copy session. End state: a race-frequency chart against cancel latency, and a reconciliation report with zero breaks.
- **Build.** `firm.ordergw`: order-entry session (login, sequencing, heartbeats, replay on reconnect), order state machine with pending states, worst-case position accounting on Book 1's firm.pnl (its C++20 and Rust twins), token-bucket throttle, drop-copy reconciler; C++20 and Rust with a Python reference; acceptance: property tests over random interleavings (filled never exceeds ordered, no negative leaves, exposure bound respected) and conformance against the simulator.
- **Weekend problem.** The cancel that crossed a fill -- named result: the probability of a cancel-fill race per cancel as a function of the cancel's latency and the fill intensity, and the worst over-position without in-flight accounting.
- **Data.** Book 10 simulator's order-entry and drop-copy sessions.
- **Facts to verify.** FIX OrdStatus and ExecType values (FIX specification); Nasdaq OUCH 5.0 order states and cancel reasons; exchange cancel-on-disconnect functionality (for example CME iLink, dated); drop-copy services of a major exchange (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CME Cancel On Disconnect: monitors iLink for involuntary lost connections and cancels all resting futures and options orders of the disconnected COD-enabled session (not GTC/GTD); enabled by default for new sessions, mandatory except iLink CGW sessions for listed derivatives; the user must re-enter the orders | CME Group Client Systems Wiki, Cancel on Disconnect | https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457216487 | 2026-09-25 | "If a lost connection is detected, COD cancels all resting futures and options orders for the disconnected COD-enabled iLink session"; "All newly created iLink sessions are created with Cancel on Disconnect (COD) enabled by default" | section 4; dat:ll:order-gateway-and-order-management:cme |
| F2 | CME Drop Copy: real-time copies of the Execution Reports and Acknowledgments sent over iLink order-entry sessions, on a separate dedicated path; execution reports give the filled position, acknowledgments the open-order position; certification mandatory | CME Group Client Systems Wiki, Drop Copy 4.0 Service for iLink | https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/665190402 | 2026-09-25 | "The Drop Copy service allows customers to receive real-time copies of CME Globex Execution Report and Acknowledgment messages as they are sent over iLink order entry system sessions on a separate, dedicated path" | section 5; dat:ll:order-gateway-and-order-management:cme |
| F3 | FIX OrdStatus code set (New 0, PartiallyFilled 1, Filled 2, Canceled 4, PendingCancel 6, Rejected 8, PendingNew A, PendingReplace E) | FIX Latest (EP312) code-set dictionary, OrdStatusCodeSet | https://orchimate.org/fixtrading/fix-latest/codeSets/OrdStatusCodeSet | 2026-09-25 | "PendingCancel 6 Pending Cancel (i.e. result of Order Cancel Request)"; "PendingNew A"; "PendingReplace E Pending Replace (i.e. result of Order Cancel/Replace Request)" | section 1 |

## EXCLUDED

- Nasdaq OUCH 5.0 (brief): not used; the chapter works against the simulator's order-entry protocol (Book 10, PROTOCOL.md), whose states and cancel reasons are stated there.

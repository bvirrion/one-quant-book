# 19. Simulation versus Live — brief and source ledger

## Brief

- **Hook.** A strategy's first live month makes forty per cent of what the simulator says it would have made on the same days, with the same signals.
- **Sections.** Reconciling fills; Reconciling P&L; Locating the divergence; Keeping the simulator honest.
- **Defines.** sim-to-live reconciliation, shadow trading, implementation shortfall, arrival price, divergence decomposition, replay parity test, simulator calibration.
- **Uses (defined earlier).** mark-out (B2.15), P\&L attribution (B1.7), fill model (ch17), queue-position model (ch18), latency model (ch18), market impact (ch18), order-book replay (ch18).
- **Tutorial.** Trade a strategy against a firm.tape market that reacts to its orders (the stand-in for live) and replay the same session in firm.lobreplay; match the fills and decompose the P&L gap into latency, queue, impact and fees; then recalibrate the fill model on the live fills.
- **Build.** `firm.simlive`: fill matcher (live orders to simulated orders), P&L gap decomposition, replay parity test, and fill-probability recalibration from live fills; Python.
- **Weekend problem.** The forty-per-cent month — named result: the decomposition of the gap between live and simulated P&L into latency, queue position, impact and fees.
- **Facts to verify.** Perold 1988, The implementation shortfall: paper versus reality (JPM).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. F. Perold, "The implementation shortfall", J. Portfolio Management 14(3) (1988) 4-9 (reprinted as "The implementation shortfall: paper versus reality"): the term, the difference between a paper portfolio and the real one | Crossref records of the article and of its reprint (Streetwise, 1998); no abstract | https://doi.org/10.3905/jpm.1988.409150 | 2026-09-25 | bibliographic records; the reprint's title "The Implementation Shortfall: Paper versus Reality" | def. implementation shortfall; iq 2; omsources |

## EXCLUDED

- No firm's live results are reported: the "live" market is firm.tape with the strategy as an agent (the chapter says so); every fill, P&L, parity share and calibration result is computed and tested.
- The decomposition of implementation shortfall into delay, execution, opportunity and fees is the chapter's own presentation; only the term is attributed to Perold.

# 20. The Risk Grid — brief and source ledger

## Brief

- **Hook.** The nightly risk batch -- every trade, every historical scenario, every bump -- finished at 06:10 against a 06:00 deadline, for the third night running. Doubling the machines did not help, because the last hour was one task waiting for the one trade that would not price.
- **Sections.** Nightly revaluation at scale; Fanning out scenarios; Task granularity, failure and retry; Adjoint sensitivities in production; Intraday risk and incremental revaluation.
- **Defines.** risk grid, batch window, scenario fan-out, task granularity, incremental revaluation.
- **Uses (defined earlier).** risk engine (B6.29), risk factor (B6.21), risk hierarchy (B6.29), risk limit (B6.29), pricing engine (B5.28), market-data snapshot (B5.28), bump-and-reprice (B5.4), Greeks (B5.4), full revaluation (B6.29), revaluation grid (B6.29), historical simulation (B6.21), expected shortfall (B6.21), algorithmic differentiation (B4.28), adjoint mode (B4.28), checkpointing (B4.28), task graph (ch13), straggler (ch13), makespan (ch13), job scheduler (ch13), end-of-day batch (ch1).
- **Tutorial.** Build a book of a few thousand trades from Book 5's and Book 6's instruments, generate historical scenarios with Book 6's risk engine, and fan the (trade batch, scenario batch) tasks out through chapter 13's scheduler on its simulated cluster, the pricing calls themselves run for real on a sample; vary the task granularity and measure makespan against overhead; plant one slow and one failing trade; compute sensitivities by bumping and by the adjoint of Book 4's tape and count pricing calls; rerun intraday for the trades that changed only. End state: makespan against task granularity, with the batch window marked, and pricing calls by method.
- **Build.** `firm.riskgrid`: task planning (trade and scenario batching by cost estimate), submission through firm.jobgraph, per-task results into the results store, retry and quarantine of failing trades with a report, adjoint sensitivities through firm.aad where the engine supports them with bump fallback, incremental intraday revaluation keyed by trade and market-data version, aggregation through firm.riskengine; Python.
- **Weekend problem.** 06:10 against 06:00 -- named result: the batch's makespan as a function of task granularity and cluster size, the granularity that meets the window, and the pricing calls saved by adjoint sensitivities and by incremental intraday revaluation.
- **Facts to verify.** Capriotti and Giles 2010, Fast correlation Greeks by adjoint algorithmic differentiation (Risk); Giles and Glasserman 2006, Smoking adjoints (Risk); BCBS FRTB (d457) requirement of daily ES computation (pointer B6.23); a public account of a bank's risk-grid scale (talk or paper, dated).
- **Data.** Book 5 and Book 6 instruments; synthetic scenarios from firm.riskengine; simulated cluster.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|

## EXCLUDED

- FRTB daily ES requirement (brief): the Basel Framework MAR page fetched did not show the paragraph text; the dated box was removed.
- Giles and Glasserman 2006, Capriotti and Giles 2010 (Risk magazine): not indexed on Crossref; adjoints are pointed to Book 4 chapter 28.
- A public account of a bank's risk-grid scale: not searched.


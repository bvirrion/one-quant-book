# 17. Discretionary Macro — brief and source ledger

## Brief

- **Hook.** A macro manager with a view that rates will fall has a dozen ways to express it; the view is the easy part, and the instrument, the size and the stop decide whether being right pays.
- **Sections.** From view to trade; Instrument choice and convexity; Sizing and stops; Keeping score.
- **Defines.** trade expression, convexity budget, stop discipline.
- **Uses (defined earlier).** risk reversal (B2.19), straddle (B5.4), drawdown limit (B8.28).
- **Tutorial.** Simulate a manager with a noisy view on a synthetic rate path and compare expressions (futures, options, spreads) and stop rules on the view's expected payoff and the probability of being stopped out before being right.
- **Build.** `firm.macrobook`: view-to-trade mapping, expression payoffs under a view distribution, stop rules and their cost; Python.
- **Weekend problem.** Right and still losing — named result: the expected payoff of each expression of the same view and the share of correct views stopped out early.
- **Facts to verify.** no firm named without a public source; public descriptions of macro process (dated) if any.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | K. M. Kaminski, A. W. Lo, "When do stop-loss rules stop losses?", Journal of Financial Markets 18 (2014) 234-254: a simple analytical framework for the value added or subtracted by stop-loss rules (policies that reduce exposure after a threshold of cumulative losses) on a strategy's expected return and volatility; with daily futures data on index buy-and-hold strategies, at longer sampling frequencies certain stop-loss policies can increase expected return while substantially reducing volatility | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.finmar.2013.07.001 | 2026-09-25 | "At longer sampling frequencies, certain stop-loss policies can increase expected return while substantially reducing volatility" | section 3; omsources |

## EXCLUDED

- Named discretionary macro managers and their trades: none; the brief allowed a firm only with a public source, and no process description was needed for the chapter's argument.
- The view's parameters (50 bp fall, 50 bp dispersion, 90 bp volatility, 10% implied-vol premium) and the risk-budget definitions are the chapter's own choices.


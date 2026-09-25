# 9. Capital-Structure Arbitrage — brief and source ledger

## Brief

- **Hook.** The same company's shares and its credit default swaps price its default risk; when they disagree, a trader buys one and sells the other and waits for the disagreement to close, or for the model to be wrong.
- **Sections.** From equity to credit spread; The trade and its hedge ratio; Evidence and losses; Model risk.
- **Defines.** equity-implied spread, cross-asset hedge ratio.
- **Uses (defined earlier).** capital-structure arbitrage (B6.14), Merton model (B6.14), credit spread (B2.21), credit default swap (B2.23), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** equity-implied spread convergence; long CDS short equity on weak equity; debt-equity dislocation after events.
- **Tutorial.** Simulate firms whose equity and CDS both reflect a structural default model with planted noise and occasional regime changes; compute equity-implied spreads, trade convergence, and measure losses when the model's parameters shift.
- **Build.** `firm.capstruct`: equity-implied spreads from a structural model, hedge ratios, convergence trades and a parameter-shift stress; Python.
- **Weekend problem.** Same default, two prices — named result: the convergence trade's Sharpe ratio and the losses when leverage shifts.
- **Facts to verify.** Yu 2006 how profitable is capital structure arbitrage? (FAJ); Duarte, Longstaff, Yu 2007 risk and return in fixed-income arbitrage (RFS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | F. Yu, "How profitable is capital structure arbitrage?", Financial Analysts Journal 62(5) (2006) 47-62: exploits mispricing between a company's CDS spread and its equity price, using the CreditGrades benchmark model, a convergence-type strategy and 135,759 daily CDS spreads on 261 North American obligors; individual trades can lose substantially because of the low correlation between CDS spreads and equity prices; an equally weighted portfolio of all trades had Sharpe ratios similar to other fixed-income arbitrage strategies and hedge fund benchmarks | Crossref metadata; OpenAlex abstract | https://doi.org/10.2469/faj.v62.n5.4282 | 2026-09-25 | abstract: "At the level of individual trades, substantial losses can occur as a result of the low correlation between the CDS spread and the equity price"; "An equally weighted portfolio of all trades, however, produced Sharpe ratios similar to those for other fixed-income arbitrage strategies" | hook; section 1; section 3; strat:s2:capital-structure-arbitrage:convergence; omsources |
| F2 | J. Duarte, F. A. Longstaff, F. Yu, "Risk and return in fixed-income arbitrage: nickels in front of a steamroller?", Review of Financial Studies 20(3) (2007) 769-811: strategies requiring more "intellectual capital" tend to produce significant alphas after controlling for bond and equity market factors, remaining significant after typical hedge fund fees; many fixed-income arbitrage strategies produce positively skewed returns | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhl026 | 2026-09-25 | abstract: "the strategies requiring more 'intellectual capital' to implement tend to produce significant alphas"; "many of the fixed-income arbitrage strategies produce positively skewed returns" | section 3; omsources |

## EXCLUDED

- Real CDS and equity data: no free source; the chapter's trades are synthetic and Yu's results are quoted from his abstract.
- CreditGrades' exact formula and parameters (barrier uncertainty): not fetched; the chapter's model is described as "in the spirit of" it, a first-passage model with a recovered-debt barrier.
- Named leveraged buyouts and their effect on CDS: none quoted; the chapter's shifts are planted.
- The mispricing (sd 10% in logs), barrier dispersion (25%) and trade thresholds are the chapter's own choices.


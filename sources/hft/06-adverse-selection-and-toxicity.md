# 6. Adverse Selection and Toxicity — brief and source ledger

## Brief

- **Hook.** A market maker's fills from one counterparty class lose half a tick five seconds later on average, and from another they gain; the quotes are the same for both until the desk decides they should not be.
- **Sections.** Mark-outs by counterparty, venue and order type; Detecting informed flow; Toxicity scores; Responses: widen, fade, skew, refuse; Toxicity is not permanent.
- **Defines.** toxicity score, quote fading, defensive widening.
- **Uses (defined earlier).** flow toxicity (B7.9), VPIN (B7.9), mark-out (B2.15), client tiering (B9.24), order-flow imbalance (B7.8), trade sign (B7.9), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30), mark-out curve (B7.23), spread capture (B7.23), adverse-selection cost (B7.23), inventory P\&L (B7.23), fill rate (B7.23).
- **Tutorial.** Run a quoter in firm.mmharness against firm_tape flow with informed and noise traders, compute mark-out curves by counterparty class, venue-like order type and time of day, build a toxicity score and test widening and fading against a flat policy on common random numbers.
- **Build.** `firm.toxicity`: grouped mark-outs with standard errors, a sequential toxicity score (Bayesian update of the informed share), fade and widen responses as Quoter wrappers; Python, on firm.markout.
- **Weekend problem.** Who is on the other side — named result: the change in capture and in adverse-selection cost when quotes are faded on a high toxicity score, and the fills given up.
- **Facts to verify.** Easley, Lopez de Prado, O'Hara 2012 Flow toxicity and liquidity in a high-frequency world (RFS); Battalio, Corwin, Jennings 2016 Can brokers have it all? (JF); O'Hara 2015 High frequency market microstructure (JFE); Andersen and Bondarenko 2014 VPIN and the flash crash (JFM).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Easley, Lopez de Prado and O'Hara (2012): order flow is toxic when it adversely selects market makers, who may be unaware they are providing liquidity at a loss; VPIN estimates toxicity from volume imbalance and trade intensity in volume time, with bulk volume classification; a useful indicator of short-term, toxicity-induced volatility | D. Easley, M. Lopez de Prado and M. O'Hara, "Flow toxicity and liquidity in a high-frequency world", Review of Financial Studies 25(5), 2012, 1457-1493 | https://doi.org/10.1093/rfs/hhs053 | 2026-09-25 | OpenAlex abstract: "Order flow is toxic when it adversely selects market makers, who may be unaware they are providing liquidity at a loss" | §2 |
| F2 | Andersen and Bondarenko: VPIN is a poor volatility predictor, reached its all-time high only after the flash crash, and its predictive content stems from a mechanical relation with trading intensity; caution against adopting a market stress metric before thorough comparison with benchmarks | T. G. Andersen and O. Bondarenko, "VPIN and the flash crash", Journal of Financial Markets 17, 2014, 1-46 (CREATES working paper 2011-50 abstract) | https://ideas.repec.org/p/aah/create/2011-50.html | 2026-09-25 | "we find that VPIN is a poor volatility predictor, that it only reached an all-time high following the flash crash, and that its predictive content stems from a mechanical relation with trading intensity"; Crossref doi 10.1016/j.finmar.2013.05.005 | §2 |
| F3 | Battalio, Corwin and Jennings (2016): retail brokers that seemingly route to maximise order-flow payments send limit orders to venues paying large rebates; negative relation between limit order execution quality and the rebate/fee level, in proprietary limit order data and TAQ | R. Battalio, S. A. Corwin and R. Jennings, "Can brokers have it all? On the relation between make-take fees and limit order execution quality", Journal of Finance 71(5), 2016, 2193-2238 | https://doi.org/10.1111/jofi.12422 | 2026-09-25 | Crossref abstract: "we document a negative relation between several measures of limit order execution quality and rebate/fee level" | §1 |

## EXCLUDED

- O'Hara (2015) "High frequency market microstructure": not verified in this session; not cited.
- Mark-outs by named venue or counterparty: no public data; the chapter's classes are the simulator's truth (informed or not).


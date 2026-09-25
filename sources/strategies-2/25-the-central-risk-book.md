# 25. The Central Risk Book — brief and source ledger

## Brief

- **Hook.** Ten desks each hedging their own risk pay ten spreads for trades that would net to little; a central risk book collects the risk first and hedges only what is left.
- **Sections.** Pooling and netting; Internal crossing; Optimised hedging; Governance.
- **Defines.** central risk book, residual risk hedge, risk pooling.
- **Uses (defined earlier).** internal crossing (B7.27), fundamental factor model (B7.24), transaction cost analysis (B7.23).
- **Strategy files.** central netting across desks; factor-hedged residual risk; patient hedging of pooled risk.
- **Tutorial.** Simulate trades arriving at several desks, pool them in a central book, hedge the net with a factor model and a cost model, and compare costs and residual risk with desk-by-desk hedging.
- **Build.** `firm.crbook`: risk pooling across desks, netting, factor hedges optimised against costs and residual-risk limits; Python.
- **Weekend problem.** Hedge what is left — named result: the hedging cost saved by pooling and the residual risk accepted.
- **Facts to verify.** public descriptions of central risk books (dated), no firm named without a source.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | N. Garleanu, L. H. Pedersen, "Dynamic trading with predictable returns and transaction costs", Journal of Finance 68(6) (2013) 2309-2340: with costly trading the optimal policy aims in front of the target and trades partially toward the current aim (as in Book 7, ch. 26) | Crossref metadata; OpenAlex abstract (Book 7 ledger) | https://doi.org/10.1111/jofi.12080 | 2026-09-25 | "The optimal strategy is characterized by two principles: (1) aim in front of the target, and (2) trade partially toward the current aim" | section 3; strat:s2:the-central-risk-book:patient; exercise 5; solutions; omsources |
| F2 | R. Almgren, C. Thum, E. Hauptmann, H. Li, "Direct estimation of equity market impact" (Risk, 2005): almost 700,000 US stock orders executed by Citigroup equity trading desks, December 2001 to June 2003; impact coefficients depend on volatility, daily volume and turnover; temporary impact follows a 3/5 power law of the trade rate rather than a square root | Paper PDF, pdftotext (Book 7 ledger) | https://www.cis.upenn.edu/~mkearns/finread/costestim.pdf | 2026-09-25 | "We reject the common square-root model for temporary impact as function of trade rate, in favor of a 3/5 power law across the range of order sizes considered" | section 1; solutions; omsources |
| F3 | M. Butz, R. Oomen, "Internalisation by electronic FX spot dealers", Quantitative Finance 19(1) (2019): internalisation (warehousing a client's risk in anticipation of offsetting flow) against externalisation (hedging at once); costs of internalisation lower for dealers willing to hold more risk (as in chapter 24) | Crossref metadata; OpenAlex abstract | https://doi.org/10.1080/14697688.2018.1504167 | 2026-09-25 | "They may internalise a customer's trade by warehousing the risk in anticipation of future offsetting flow, or they can externalise the trade by hedging it out in the open market" | section 1; strat:s2:the-central-risk-book:netting; omsources |

## EXCLUDED

- Public descriptions of central risk books at named banks: the sources found were vendor blog posts, a paywalled industry report and an arXiv paper whose title and abstract are redacted; none is citable under the series rule, so no bank is named and no dated box is printed.
- Sizes of banks' internal crossing or hedging costs: not public; the desks and flows are synthetic (planted: five desks, $0.5m flow sd per name a day, 10% common variance).

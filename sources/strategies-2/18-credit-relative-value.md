# 18. Credit Relative Value — brief and source ledger

## Brief

- **Hook.** A company's bond and its credit default swap insure the same default; the gap between them, the basis, went deeply negative in 2008 when the trade that should close it needed funding nobody had.
- **Sections.** The bond-CDS basis; Index against constituents; Credit curve trades; Funding and the negative basis.
- **Defines.** negative basis trade, credit index arbitrage, credit curve trade.
- **Uses (defined earlier).** credit default swap (B2.23), credit spread (B2.21), z-spread (B2.21), credit event (B2.23), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** negative basis trade; index versus single-name arbitrage; credit curve flattener; senior versus subordinated; cross-currency credit.
- **Tutorial.** Simulate bonds and CDS on synthetic issuers with a funding cost that drives the basis, trade the basis, index-constituent gaps and curve shapes, and stress funding.
- **Build.** `firm.creditrv`: bond-CDS basis, index intrinsic value and skew, curve trades and funding stress; Python.
- **Weekend problem.** Same default, two prices again — named result: the negative-basis trade's carry and its mark-to-market loss when funding costs jump.
- **Facts to verify.** Bai and Collin-Dufresne 2019 the CDS-bond basis (Financial Management); Mitchell and Pulvino 2012 arbitrage crashes and the speed of capital (JFE).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. Bai, P. Collin-Dufresne, "The CDS-bond basis", Financial Management 48(2) (2019) 417-439: the arbitrage relation between cash bond and CDS says the basis should be zero in normal conditions; cross-sectional deviations are consistent with limits to arbitrage, larger for bonds with higher frictions (trading liquidity, funding cost, counterparty risk, collateral quality); the basis is more negative when the bond lending fee is higher | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/fima.12252 | 2026-09-25 | abstract: "deviations are larger for bonds with higher frictions as measured by trading liquidity, funding cost, counterparty risk, and collateral quality" | hook; section 1; section 4; strat:s2:credit-relative-value:negbasis; omsources |
| F2 | M. Mitchell, T. Pulvino (2012), as in chapter 8: in 2008 the imminent failure of prime brokers suddenly cut the leverage available to hedge funds; long-term debt capital became short-term; arbitrageurs could not keep similar prices of similar assets | Crossref metadata; RePEc abstract | https://doi.org/10.1016/j.jfineco.2011.09.002 | 2026-09-25 | as chapter 8 ledger F2 | section 4; omsources |

## EXCLUDED

- Measured bond-CDS bases in 2008 (sizes by rating): not in the fetched abstracts; the chapter's crisis is planted and labelled as such.
- CDS index skew and curve data: licensed; synthetic only.
- Named funds' negative-basis losses: none quoted.


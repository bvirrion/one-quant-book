# 7. Limits and Capital Allocation — brief and source ledger

## Brief

- **Hook.** A firm with 500 million dollars of risk capital runs six strategies. Allocated by each strategy's own value at risk, they use all of it; allocated by what each contributes to the firm's tail, two of them turn out to earn less than the capital they consume costs, and one that looked expensive is the cheapest in the firm.
- **Sections.** What a limit framework is for; Measures and levels: notional, sensitivities, VaR, stress, loss; Utilisation, breaches and temporary increases; Allocating risk capital; Charging for capital.
- **Defines.** limit framework, hard limit, soft limit, limit utilisation, limit breach, concentration limit, economic capital, risk-adjusted return on capital, capital charge.
- **Uses (defined earlier).** risk limit (B6.29), risk hierarchy (B6.29), value at risk (B6.21), expected shortfall (B6.21), stress test (B6.22), Euler allocation (B6.20), risk budgeting (B7.26), hurdle rate (B6.19), loss limit (B11.27), position limit (B1.27), drawdown limit (B8.28), pre-trade risk check (B11.27), risk appetite (ch6), risk appetite statement (ch6).
- **Tutorial.** Six strategies with P&L histories from the synthetic firm: compute standalone and Euler contributions to the firm's expected shortfall, allocate its economic capital by each, charge it at a hurdle, and rank the strategies by risk-adjusted return on capital; then choose the allocation that maximises the firm's risk-adjusted return subject to its limits. End state: a bar chart of allocated capital and risk-adjusted return by strategy under the three allocation rules.
- **Build.** `firm.limitalloc`: a limit framework as data (a tree of levels, each with measures and hard and soft thresholds), utilisation and breach classification from positions and risk, temporary increases with expiry, economic-capital allocation (standalone, Euler, incremental) and the capital charge, and the optimal allocation under limits; exports its pre-trade part to firm.riskctl's limits schema; Python.
- **Weekend problem.** Who pays for the tail -- named result: the capital-charge rate at which a given strategy's risk-adjusted return falls below the hurdle under Euler allocation but not under standalone allocation (the diversification credit it earns or loses).
- **Facts to verify.** BCBS, Range of practices and issues in economic capital frameworks (2009); Tasche 2008 on Euler allocation (pointer to Book 6 ch. 20); Zaik, Walter, Kelling and James 1996, RAROC at Bank of America (Journal of Applied Corporate Finance); a bank's public disclosure of economic capital or RAROC in its annual report or Pillar 3 (dated).
- **Data.** Synthetic (firm.multistrat pods).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|

## EXCLUDED


# 14. The Almgren--Chriss Framework — brief and source ledger

## Brief

- **Hook.** A trader must sell a million shares by the close. Selling them all now pays the impact; selling them evenly carries the price risk all day. Between the two lies a curve of schedules, and choosing a point on it is choosing a risk aversion.
- **Sections.** Parent orders, child orders and a trajectory; Costs: impact and risk; The optimal trajectory in closed form; The efficient trading frontier; Calibration and limits.
- **Defines.** parent order, child order, trading trajectory, Almgren--Chriss model, execution risk, efficient trading frontier, urgency.
- **Uses (defined earlier).** market impact (B7.18), temporary impact (B7.27), permanent impact (B7.27), square-root impact law (B7.27), metaorder (B7.9), percentage of volume (B7.27), implementation shortfall (B7.19), arrival price (B7.19), transaction cost analysis (B7.23), mean--variance optimisation (B7.25), risk-aversion parameter (B7.25), certainty equivalent (B4.9), Hamilton--Jacobi--Bellman equation (B4.9), value function (B4.9), dynamic programming (B4.9), volume-weighted average price (B7.2), impact prefactor (ch11).
- **Tutorial.** Implement the discrete and continuous Almgren-Chriss solutions; draw trajectories for several risk aversions and the efficient trading frontier; execute the schedules in firm.exchsim with an execution agent and compare the realised mean and variance of the shortfall with the model's. Data: simulated.
- **Build.** `firm.acexec`: discrete and continuous Almgren-Chriss trajectories, cost and variance, frontier, calibration of the impact parameters from firm.impactfit, and the common scheduler interface (target holdings per interval) that chapters 15, 16 and 28 plug their schedules into; Python.
- **Weekend problem.** Liquidating a block by the close -- named result: the optimal trading horizon, expected cost and standard deviation for a given risk aversion, and the extra cost of a schedule that is twice too patient or twice too hurried.
- **Facts to verify.** Almgren and Chriss 2000 optimal execution of portfolio transactions (J. Risk); Bertsimas and Lo 1998 optimal control of execution costs (JFM); Almgren 2003 optimal execution with nonlinear impact functions and trading-enhanced risk (Applied Mathematical Finance); Kissell and Glantz 2003 Optimal Trading Strategies.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Almgren and N. Chriss, "Optimal execution of portfolio transactions", Journal of Risk 3(2) (2001) 5-39 | Crossref record | https://doi.org/10.21314/jor.2001.041 | 2026-09-25 | bibliographic record | §2-4, omsources |
| F2 | D. Bertsimas and A. W. Lo, "Optimal control of execution costs", Journal of Financial Markets 1(1) (1998) 1-50 | Crossref record | https://doi.org/10.1016/s1386-4181(97)00012-8 | 2026-09-25 | bibliographic record | §1, omsources |
| F3 | R. Almgren, "Optimal execution with nonlinear impact functions and trading-enhanced risk", Applied Mathematical Finance 10(1) (2003) 1-18 | Crossref record | https://doi.org/10.1080/135048602100056 | 2026-09-25 | bibliographic record | §5, omsources |

## EXCLUDED

- The block (1,000,000 shares of a 50-dollar stock trading 10 million a day at 2% volatility) is an illustration with parameters chosen by the chapter; the prefactor 0.8 is chapter 11's simulated truth, not a published value.
- Kissell and Glantz (2003, Optimal Trading Strategies): not needed; not cited.
- All numbers are computed by firm.acexec and on firm.agentmkt and tested.

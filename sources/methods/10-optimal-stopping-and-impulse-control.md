# 10. Optimal Stopping and Impulse Control — brief and source ledger

## Brief

- **Hook.** A treasury desk carries a currency exposure that drifts with client flows; each hedge ticket costs a fixed fee plus the spread. Hedging every flow wastes fees, never hedging wastes risk, and the answer is a band: do nothing inside it, trade back to target when it is hit.
- **Sections.** Optimal stopping in discrete time: the Snell envelope; Free boundaries and variational inequalities; When to act: exiting a mean-reverting position; Impulse control and no-trade regions; Singular control and reflection.
- **Defines.** optimal stopping problem, Snell envelope, continuation region, stopping region, free-boundary problem, smooth pasting, variational inequality, impulse control, quasi-variational inequality, no-trade region, singular control, reflected Brownian motion.
- **Uses (defined earlier).** American exercise, stopping time, supermartingale, value function, dynamic programming, Hamilton--Jacobi--Bellman equation, Ornstein--Uhlenbeck process, half-life, bid--ask spread.
- **Results (named theorems, not terms).** the Snell envelope is the smallest supermartingale dominating the reward; the first entry into the stopping region is optimal; smooth pasting for a perpetual problem (derived); fixed-cost band half-width scales as the fourth root of the cost; proportional-cost band as the cube root (asymptotics, stated with sources).
- **Tutorial.** Find the optimal take-profit level of a mean-reverting spread trade with a round-trip cost two ways: by solving the free-boundary ODE with smooth pasting, and by backward induction on a grid with `firm.dpsolve`; plot the value function and the boundary.
- **Build.** `firm.impulse`: optimal stopping by backward induction on top of `firm.dpsolve`, and a band-policy optimiser for impulse control (evaluate and optimise (d, D, U, u) bands for a diffusing exposure with fixed and proportional costs); Python.
- **Weekend problem.** The hedging band — named result: the optimal band half-width for the desk's exposure, its fourth-root dependence on the ticket fee, and the saving against hedging at every flow.
- **Facts to verify.** Snell 1952 (Trans. AMS); Constantinides and Richard 1978 (Operations Research) impulse control cash management; Harrison and Taksar 1983 instantaneous control of Brownian motion; Davis and Norman 1990 (Math. of Operations Research) portfolio selection with transaction costs; Whalley and Wilmott 1997 (Mathematical Finance) asymptotic hedging bands; Rogers 2004 on the O(eps^{2/3}) effect of proportional costs; Leung and Li 2015 (IJTAF) optimal mean-reversion trading with transaction costs.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | J. L. Snell, "Applications of martingale system theorems", Transactions of the AMS 73 (1952), 293-312 (the Snell envelope) | AMS journal PDF | https://www.ams.org/journals/tran/1952-073-02/S0002-9947-1952-0050209-9/S0002-9947-1952-0050209-9.pdf | 2026-09-24 | Trans. AMS 73, 293-312 | def Snell envelope; omsources |
| F2 | G. M. Constantinides and S. F. Richard, "Existence of optimal simple policies for discounted-cost inventory and cash management in continuous time", Operations Research 26 (1978), 620-636 | search summary of citing literature | https://www.aporc.org/LNOR/10/ISORA2009F40.pdf | 2026-09-24 | Operations Research 26 (1978) 620-636 | §3 (impulse control); omsources |
| F3 | M. H. A. Davis and A. R. Norman, "Portfolio selection with transaction costs", Mathematics of Operations Research 15(4) (1990), 676-713: proportional costs give a wedge-shaped no-trade region with local-time trading at its boundaries | INFORMS record, doi 10.1287/moor.15.4.676 | https://pubsonline.informs.org/doi/10.1287/moor.15.4.676 | 2026-09-24 | "optimal buying and selling policies are the local times ... at the boundaries of a wedge-shaped region" | §4; omsources |
| F4 | A. E. Whalley and P. Wilmott, "An asymptotic analysis of an optimal hedging model for option pricing with transaction costs", Mathematical Finance 7(3) (1997), 307-324 | Wiley Online Library record | https://onlinelibrary.wiley.com/doi/abs/10.1111/1467-9965.00034 | 2026-09-24 | Math. Finance 7: 307-324 | omsources |
| F5 | G. Peskir and A. Shiryaev, Optimal Stopping and Free-Boundary Problems, Birkhäuser (Lectures in Mathematics ETH Zürich), 2006 | Springer book record | https://link.springer.com/book/10.1007/978-3-7643-7390-0 | 2026-09-24 | 1st edition 2006, ISBN 978-3-7643-2419-3 | omsources |

## EXCLUDED

- Harrison-Taksar 1983, Rogers 2004, Leung-Li 2015 (planned): not cited in the text.
- The desk's parameters (sigma 20m per sqrt day, gamma 0.5, K = USD 300, c = USD 25 per million) are illustrative, not market facts.


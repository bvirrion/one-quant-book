# 2. The Binomial Model — brief and source ledger

## Brief

- **Hook.** A three-step tree on a whiteboard, eight end nodes, and a question: the price of a call, with no volatility number, no formula, only the two moves and the rate.
- **Sections.** One period: replication and the risk-neutral probability; Many periods: the recombining tree; Calibrating the tree to a volatility; Convergence and its oscillations; American exercise on a tree.
- **Defines.** binomial model, recombining tree, Cox--Ross--Rubinstein tree, Jarrow--Rudd tree, Leisen--Reimer tree.
- **Uses (defined earlier).** replicating portfolio, self-financing strategy, risk-neutral measure (Book 4 ch. 5), American exercise (Book 1 ch. 23), dynamic programming (Book 4 ch. 9), central limit theorem (Book 4 ch. 1).
- **Tutorial.** Price a European and an American put on CRR, JR and Leisen-Reimer trees from 10 to 1,000 steps and plot the error against the number of steps.
- **Build.** `firm.binomial`: recombining-tree pricer (CRR, JR, LR; European and American; the discrete-dividend hook is filled in chapter 5).
- **Weekend problem.** The whiteboard tree — named result: the early-exercise premium of the American put on the three-step tree, and the number of CRR steps after which the price stays within one cent of its limit.
- **Facts to verify.** Cox, Ross, Rubinstein 1979 JFE; Rendleman-Bartter 1979 JF; Jarrow-Rudd 1983 book; Leisen-Reimer 1996 Applied Mathematical Finance.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Cox, Ross, Rubinstein, "Option pricing: a simplified approach", JFE 7(3) (1979) 229-263: binomial model, Black-Scholes as a limit | IDEAS/RePEc record | https://ideas.repec.org/a/eee/jfinec/v7y1979i3p229-263.html | 2026-09-24 | "contains as a special limiting case the celebrated Black-Scholes model" | §1-3; omsources |
| F2 | Rendleman and Bartter, "Two-state option pricing", JF 34(5) (1979) 1093-1110 | Wiley record | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1979.tb00058.x | 2026-09-24 | bibliographic record | omsources |
| F3 | Jarrow and Rudd, Option Pricing, Irwin, Homewood IL, 1983 | IDEAS/RePEc (JBF review) | https://ideas.repec.org/a/eee/jbfina/v10y1986i1p157-161.html | 2026-09-24 | "(Irwin, Homewood, IL, 1983) pp. xxii + 235" | def JR tree; omsources |
| F4 | Leisen and Reimer, Applied Mathematical Finance 3(4) (1996) 319-346: order-one convergence of CRR, order-two trees | EconPapers / T&F record | https://econpapers.repec.org/article/tafapmtfi/v_3a3_3ay_3a1996_3ai_3a4_3ap_3a319-346.htm | 2026-09-24 | "converge smoothly to the Black-Scholes solution with order of convergence two" (search summary) | def LR tree; omsources |

## EXCLUDED

- None: every number in the chapter is computed by its code.

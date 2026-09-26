# 4. Why There Is a Spread — brief and source ledger

## Brief

- **Hook.** A market maker quotes 100.00 bid, 100.02 offered. If nobody knew more than she did, the two cents would pay for her time and for the risk of the inventory she carries. A buyer who has read the news first makes the spread pay for something else, and the three explanations lead to different spreads.
- **Sections.** Order-processing costs; Inventory; Information: the sequential-trade model; Information: the strategic trader; Measuring informed trading.
- **Defines.** order-processing cost, inventory-holding cost, informed trader, noise trader, sequential-trade model, Glosten--Milgrom model, Kyle model, probability of informed trading.
- **Uses (defined earlier).** adverse selection (B1.1), market maker (B1.1), bid--ask spread (B1.1), inventory (B2.30), Bayesian update (B2.30), winner's curse (B2.30), Kyle's lambda (B7.9), VPIN (B7.9), flow toxicity (B7.9), Roll's estimator (B4.21), bid--ask bounce (B4.21), Nash equilibrium (B4.29), maximum likelihood estimator (B4.11), limit order book (ch1).
- **Tutorial.** Simulate the Glosten-Milgrom dealer and watch its quotes converge to the value; solve Kyle's one-period and N-period models and recover lambda from simulated trades; fit the probability of informed trading by maximum likelihood (scipy) on simulated buy and sell counts, and on firm.tape whose informed flow is known. Data: simulated.
- **Build.** `firm.spreadmodels`: Glosten-Milgrom quotes and dynamics, Kyle one-period and N-period (backward recursion), Ho-Stoll inventory quotes, the PIN likelihood (numerically stable form) and its fit, all deterministic; Python (scipy).
- **Weekend problem.** The specialist's two cents -- named result: the share of a Glosten-Milgrom spread that is adverse selection, against the informed share, and the bias of the PIN estimate when arrival rates move during the day.
- **Facts to verify.** Roll 1984 a simple implicit measure of the effective bid-ask spread (JF); Garman 1976 market microstructure (JFE); Stoll 1978 the supply of dealer services (JF); Ho and Stoll 1981 optimal dealer pricing (JFE); Glosten and Milgrom 1985 (JFE); Kyle 1985 continuous auctions and insider trading (Econometrica); Easley, Kiefer, O'Hara, Paperman 1996 liquidity, information and infrequently traded stocks (JF); Duarte and Young 2009 why is PIN priced? (JFE).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | R. Roll, "A simple implicit measure of the effective bid-ask spread in an efficient market", Journal of Finance 39(4) (1984) 1127-1139 | Crossref record | https://doi.org/10.2307/2327617 | 2026-09-25 | bibliographic record | §1, omsources |
| F2 | M. B. Garman, "Market microstructure", Journal of Financial Economics 3(3) (1976) 257-275 | Crossref record | https://doi.org/10.1016/0304-405X(76)90006-4 | 2026-09-25 | bibliographic record | §2 |
| F3 | H. R. Stoll, "The supply of dealer services in securities markets", Journal of Finance 33(4) (1978) 1133-1151 | Crossref record | https://doi.org/10.1111/j.1540-6261.1978.tb02053.x | 2026-09-25 | bibliographic record | §2 |
| F4 | T. Ho and H. R. Stoll, "Optimal dealer pricing under transactions and return uncertainty", Journal of Financial Economics 9(1) (1981) 47-73 | Crossref record | https://doi.org/10.1016/0304-405X(81)90020-9 | 2026-09-25 | bibliographic record | §2 |
| F5 | L. R. Glosten and P. R. Milgrom, "Bid, ask and transaction prices in a specialist market with heterogeneously informed traders", Journal of Financial Economics 14(1) (1985) 71-100 | Crossref record | https://doi.org/10.1016/0304-405X(85)90044-3 | 2026-09-25 | bibliographic record | §3 |
| F6 | A. S. Kyle, "Continuous auctions and insider trading", Econometrica 53(6) (1985) 1315-1335 | Crossref record | https://doi.org/10.2307/1913210 | 2026-09-25 | bibliographic record | §4 |
| F7 | D. Easley, N. M. Kiefer, M. O'Hara, J. B. Paperman, "Liquidity, information, and infrequently traded stocks", Journal of Finance 51(4) (1996) 1405-1436 | Crossref record | https://doi.org/10.1111/j.1540-6261.1996.tb04074.x | 2026-09-25 | bibliographic record | §5 |
| F8 | J. Duarte and L. Young, "Why is PIN priced?", Journal of Financial Economics 91(2) (2009) 119-138: decompose PIN into an asymmetric-information component and an illiquidity component; the information component is not priced, the illiquidity component is | RePEc abstract | https://ideas.repec.org/a/eee/jfinec/v91y2009i2p119-138.html | 2026-09-25 | "the PIN component related to asymmetric information is not priced, while the PIN component related to illiquidity is priced" | §5 |

## EXCLUDED

- All model quantities (quotes, lambda, PIN fits and biases, Roll on the tape) are derived or simulated and tested.

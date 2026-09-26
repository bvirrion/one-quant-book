# 3. Inventory Models — brief and source ledger

## Brief

- **Hook.** A market maker who has just bought three times in a row owns stock nobody has yet asked for; lowering both quotes a little makes the next trade more likely to be a sale, and the question is by how much.
- **Sections.** The market maker's control problem; The Avellaneda--Stoikov model; Reservation price and optimal spread; Closed forms, their limits, and a numerical solution; Simulating the policy.
- **Defines.** Avellaneda--Stoikov model, reservation price, fill intensity, inventory penalty.
- **Uses (defined earlier).** Hamilton--Jacobi--Bellman equation (B4.9), value function (B4.9), stochastic control problem (B4.9), CRRA utility (B4.9), certainty equivalent (B4.9), Poisson process (B4.6), quote skewing (B2.15), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30), mark-out curve (B7.23), spread capture (B7.23), adverse-selection cost (B7.23), inventory P\&L (B7.23), fill rate (B7.23).
- **Tutorial.** Solve the Avellaneda--Stoikov control problem on a grid with firm.dpsolve, compare it with the closed-form approximations, then run the policy as a Quoter in firm.mmharness on firm_tape and measure inventory, capture and P&L against a symmetric quoter.
- **Build.** `firm.invmm`: the Avellaneda--Stoikov and Cartea--Jaimungal quoting policies (closed form and numerical HJB), fill-intensity estimation from a quoter's own fills, a Poisson-fill simulator for fast policy studies; Python.
- **Weekend problem.** Three buys in a row — named result: the P&L and inventory variance of the optimal quoter against the symmetric one, and the risk aversion at which they diverge.
- **Facts to verify.** Avellaneda and Stoikov 2008 High-frequency trading in a limit order book (QF); Ho and Stoll 1981 Optimal dealer pricing under transactions and return uncertainty (JFE); Cartea, Jaimungal, Ricci 2014 Buy low, sell high (SIAM JFM); Gueant 2016 The Financial Mathematics of Market Liquidity (CRC).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Avellaneda and Stoikov (2008): mid a Brownian motion, market orders hit quotes at distance delta with intensity A exp(-k delta), exponential utility; approximate solution: reservation price r = s - q gamma sigma^2 (T - t), spread gamma sigma^2 (T - t) + (2/gamma) ln(1 + gamma/k); simulation parameters s = 100, T = 1, sigma = 2, dt = 0.005, q = 0, gamma = 0.1, k = 1.5, A = 140, mid updated by +/- sigma sqrt(dt); Table 1 (gamma 0.1, 1,000 simulations): inventory strategy average spread 1.49, profit 65.0, std 6.6, final q 0.08, std 2.9; symmetric 1.49, 68.4, 12.7, 0.26, 8.4; Table 2 (gamma 0.01): 1.35, 68.6, 8.7, 0.12, 5.1 / 1.35, 68.8, 12.8, 0.09, 8.7; Table 3 (gamma 1): 3.02, 31.4, 5.0, 0.02, 1.7 / 3.02, 44.0, 11.0, 0.00, 5.1 | M. Avellaneda and S. Stoikov, "High-frequency trading in a limit order book", Quantitative Finance 8(3), 2008, 217-224 (author's copy) | https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf | 2026-09-25 | pdftotext: "we chose the following parameters: s = 100, T = 1, sigma = 2, dt = 0.005, q = 0, gamma = 0.1, k = 1.5 and A = 140"; "Table 1. 1000 simulations with gamma = 0.1. ... Inventory 1.49 65.0 6.6 0.08 2.9 Symmetric 1.49 68.4 12.7 0.26 8.4" | §2-3, tutorial table |
| F2 | Ho and Stoll (1981): optimal dealer pricing under transactions and return uncertainty, the dealer's prices depend on inventory | T. Ho and H. R. Stoll, Journal of Financial Economics 9(1), 1981, 47-73 | https://doi.org/10.1016/0304-405X(81)90020-9 | 2026-09-25 | Crossref metadata (title, journal, volume, pages) | §1 |
| F3 | Cartea, Jaimungal and Penalva, Algorithmic and High-Frequency Trading, Cambridge University Press, 2015 (ISBN 9781107091146): market making with running inventory penalties among its models | Oxford University Research Archive record | https://ora.ox.ac.uk/objects/uuid:cae8e4f6-7068-49d4-beac-ee06837a4282 | 2026-09-25 | book record; publisher CUP, 2015 | §3 |

## EXCLUDED

- The chapter's own exact solution of the running-penalty model is derived in the text (the substitution h = ln(omega)/k); no claim about which paper first wrote it in that form is made.


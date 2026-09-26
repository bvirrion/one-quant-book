# 4. Extensions of the Inventory Framework — brief and source ledger

## Brief

- **Hook.** The closed form tells a quoter to quote a negative spread when it is long enough; real market makers stop buying instead, hold several correlated books at once, and know that the next trade is more likely to come from someone who knows more than they do.
- **Sections.** Inventory bounds and the asymptotic solution; Many assets and correlated inventory; Signals and drift inside the control problem; Adverse selection inside the fill intensity.
- **Defines.** inventory bound, multi-asset market making, drift-adjusted quoting.
- **Uses (defined earlier).** Avellaneda--Stoikov model (ch3), reservation price (ch3), fill intensity (ch3), covariance matrix (B4.22), Hamilton--Jacobi--Bellman equation (B4.9), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Tutorial.** Implement the Gueant--Lehalle--Fernandez-Tapia asymptotic quotes with an inventory bound, extend to two correlated assets, add a drift signal, and compare all policies on common random numbers in firm.invmm's fast simulator and in firm.mmharness.
- **Build.** `firm.multimm`: bounded-inventory asymptotic quotes, the multi-asset reservation price and quotes, drift-adjusted and adverse-selection-adjusted policies; Python.
- **Weekend problem.** Two books, one risk — named result: the reduction in inventory risk from quoting two correlated assets jointly, at equal expected capture.
- **Facts to verify.** Gueant, Lehalle, Fernandez-Tapia 2013 Dealing with the inventory risk (MFE); Gueant 2017 Optimal market making (Applied Mathematical Finance); Cartea and Wang 2020 Market making with alpha signals (IJTAF); Cartea, Donnelly, Jaimungal 2017 Algorithmic trading with model uncertainty (SIAM JFM).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Gueant, Lehalle and Fernandez-Tapia: a change of variables turns the market-making control problem with inventory limits into a system of linear ODEs; asymptotic quotes characterised by an eigenvalue problem and approximated in closed form: delta_b(q) ~ (1/gamma) ln(1 + gamma/k) + (2q + 1)/2 sqrt(sigma^2 gamma/(2kA) (1 + gamma/k)^(1 + k/gamma)), delta_a(q) with -(2q - 1)/2; with a drift mu an extra -mu/(gamma sigma^2) inside the bracket (bid) and +mu/(gamma sigma^2) (ask); with market impact xi each quote gains xi/2 and the square root is multiplied by e^(k xi/4) | O. Gueant, C.-A. Lehalle, J. Fernandez-Tapia, "Dealing with the inventory risk: a solution to the market making problem", Mathematics and Financial Economics 7(4), 2013, 477-507 (arXiv 1105.3115v5) | https://arxiv.org/pdf/1105.3115 | 2026-09-25 | pdftotext of the arXiv v5 PDF: "we use results from spectral analysis to provide an approximation of the optimal quotes in closed-form"; the approximations in sections 4 and 5.1-5.2 as quoted in the claim; Crossref: doi 10.1007/s11579-012-0087-0 | §1, §3, §4 |
| F2 | Gueant (2017), "Optimal market making", Applied Mathematical Finance 24(2), 112-154: general intensities and multi-asset market making | Crossref metadata | https://doi.org/10.1080/1350486X.2017.1342552 | 2026-09-25 | Crossref: title, journal, volume 24, issue 2, pages 112-154 | §2 |
| F3 | Cartea and Wang (2020), "Market making with alpha signals", International Journal of Theoretical and Applied Finance 23(3), 2050016: signals of the mid's drift inside the market maker's control problem | Crossref metadata | https://doi.org/10.1142/S0219024920500168 | 2026-09-25 | Crossref: title, journal, volume 23, issue 3, article 2050016 | §3 |

## EXCLUDED

- Cartea, Donnelly and Jaimungal (2017) on model uncertainty: not used by any claim; dropped from the brief.
- The penalty-model closed form, the multi-asset exact grid solution and the half-move result are derived in the chapter; no priority claim is made.


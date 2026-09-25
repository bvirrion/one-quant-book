# 25. Portfolio Construction I — brief and source ledger

## Brief

- **Hook.** An unconstrained mean--variance optimiser puts forty-five per cent of a long--short book into two stocks: the two with the largest alphas and the smallest estimated specific risks.
- **Sections.** Mean--variance with an alpha and a risk model; The error maximiser; Realistic constraints; Turnover control; Solving at scale.
- **Defines.** mean--variance optimisation, risk-aversion parameter, efficient frontier, error maximisation, dollar neutrality, beta neutrality, factor-neutrality constraint, name limit, liquidity constraint, turnover penalty, 130/30 portfolio.
- **Uses (defined earlier).** quadratic programme (B4.23), Karush--Kuhn--Tucker conditions (B4.23), shadow price (B4.23), second-order cone programme (B4.23), interior-point method (B4.23), minimum-variance portfolio (B4.22), no-trade region (B4.10), gross exposure (B1.7), short sale (B1.6), tracking error (B1.3), market beta (ch22), risk model (ch24), transfer coefficient (ch15).
- **Tutorial.** Optimise a long--short book on firm.synthmkt from chapter 15's forecasts and chapter 24's risk model, adding the constraints one at a time and recording the information ratio, turnover, transfer coefficient and each constraint's shadow price.
- **Build.** `firm.portcons`: portfolio-construction layer over firm.portopt (objective from alpha, risk model and costs; constraint builders for budget, neutralities, name, liquidity, gross and turnover limits; diagnostics of binding constraints and shadow prices; trade list); Python.
- **Weekend problem.** The forty-five-per-cent portfolio — named result: the information ratio each constraint costs or earns, from the shadow-price decomposition.
- **Facts to verify.** Markowitz 1952 (JF); Michaud 1989, the Markowitz optimization enigma (FAJ); Jagannathan and Ma 2003, risk reduction by imposing the wrong constraints (JF); Jacobs, Levy, Starer 1998 long-short portfolio management (FAJ); Clarke, de Silva, Thorley 2002 (FAJ).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | H. Markowitz, "Portfolio Selection", Journal of Finance 7(1) (1952) 77-91 | Crossref record | https://doi.org/10.1111/j.1540-6261.1952.tb01525.x | 2026-09-25 | vol 7(1), pp 77-91 | section 1; omsources |
| F2 | R. O. Michaud, "The Markowitz Optimization Enigma: Is 'Optimized' Optimal?", Financial Analysts Journal 45(1) (1989) 31-42: mean-variance optimisers as "estimation-error maximizers"; they overweight assets with large estimation errors in large estimated returns, small variances and negative correlations, often with poor ex-post performance | Crossref metadata for the article; the authors' own patent US 6,928,418 B2 (Michaud and Michaud, 2005), which states and cites the claim (Google Patents text) | https://patents.google.com/patent/US6928418B2/en | 2026-09-25 | "These deficiencies are known to arise due to the propensity of MV optimization as 'estimation-error maximizers,' as discussed in R. Michaud, 'The Markowitz Optimization Enigma: Is Optimized Optimal?' Financial Analysts Journal (1989)"; "MV optimization tends to overweight those assets having large statistical estimation errors associated with large estimated returns, small variances, and negative correlations, often resulting in poor ex-post performance" | section 2; def. error maximisation; iq 1; omsources |
| F3 | R. Jagannathan, T. Ma, "Risk Reduction in Large Portfolios: Why Imposing the Wrong Constraints Helps", Journal of Finance 58(4) (2003) 1651-1683: constraining weights to be nonnegative can reduce the risk of estimated optimal portfolios even when the constraints are wrong; with no-short-sale constraints the sample covariance matrix performs as well as factor, shrinkage and daily-data estimates | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.1111/1540-6261.00580 | 2026-09-25 | "constraining portfolio weights to be nonnegative can reduce the risk in estimated optimal portfolios even when the constraints are wrong" | section 3; exo 8; omsources |
| F4 | B. I. Jacobs, K. N. Levy, D. Starer, "On the Optimality of Long-Short Strategies", Financial Analysts Journal 54(2) (1998) 40-51: the common practice of constraining long-short portfolios to zero net holdings or zero beta is generally suboptimal; optimal portfolios demand integrated optimisation | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.2469/faj.v54.n2.2164 | 2026-09-25 | "following the common practice of constraining long-short portfolios to have zero net holdings or zero betas is generally suboptimal"; "optimal portfolios demand the use of integrated optimizations" | section 3; omsources |
| F5 | R. Clarke, H. de Silva, S. Thorley, "Portfolio Constraints and the Fundamental Law of Active Management", Financial Analysts Journal 58(5) (2002) 48-66: constraints on short positions and turnover are common and materially restrictive; a generalised fundamental law with ex-ante and ex-post correlation relationships (the transfer coefficient) | Crossref metadata; OpenAlex record with abstract | https://doi.org/10.2469/faj.v58.n5.2468 | 2026-09-25 | "Constraints on short positions and turnover, for example, are fairly common and materially restrictive"; "The ex ante relationship is a generalized version of a previously developed 'fundamental law of active management'" | sections 3-4; omsources |

## EXCLUDED

- Michaud (1989), the article's text: behind the publisher's paywall; the claim is taken from the authors' own patent
  text, which states and cites it.
- The decomposition of the unconstrained ex-ante IR^2 by constraint (shadow-price vectors from the KKT conditions) is
  the chapter's own construction.
- Every information ratio, turnover, shadow price and decomposition share is computed on firm.synthmkt and tested.


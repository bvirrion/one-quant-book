# 9. Managing Researchers, Traders and Engineers — brief and source ledger

## Brief

- **Hook.** Three researchers' signals went into one combined forecast that made thirty million dollars. Asked what each had contributed, the desk measured what the forecast lost without each signal in turn: the three answers added up to less than half the profit. How the rest is split decides who stays.
- **Sections.** Choosing projects: a research portfolio; Review without theatre; Who made the money: attributing credit; Keeping research honest; Traders and engineers: different work, different feedback.
- **Defines.** research portfolio, project scorecard, leave-one-out contribution, credit attribution.
- **Uses (defined earlier).** research log (B7.1), research review (B7.1), stage gate (B7.1), kill criterion (B7.1), pre-registration (B7.1), trial count (B7.1), deflated Sharpe ratio (B4.12), Shapley value (B12.6), signal combination (B7.14), handoff specification (B12.28), model owner (B12.28), strategy lifecycle (B11.28), canary deployment (B7.21).
- **Tutorial.** Three contributors' signals overlap: combine them with firm.combine, and split the combined P&L by leave-one-out, by order of arrival and by Shapley value; then run a year of a research portfolio -- twelve projects with costs, success probabilities and payoffs, chosen by a budget-constrained ranking against at random -- and deflate the survivors' Sharpe ratios by the trial count in the research log. End state: a table of credit shares under the three rules, and a chart of the portfolio's realised value.
- **Build.** `firm.projsel`: a research-project portfolio (cost, probability of success, payoff distribution, correlation with the book), budget-constrained selection (by expected value per unit cost with a diversification penalty), and credit attribution of a combined P&L among contributors (leave-one-out, order-dependent, Shapley exactly for few contributors and by sampling for many); Python; uses firm.combine and firm.multitest.
- **Weekend problem.** Who made the money -- named result: the Shapley shares of three contributors whose signals overlap, against their leave-one-out shares, and the bonus-pool split each rule implies.
- **Facts to verify.** Shapley 1953, A value for n-person games; Lipovetsky and Conklin 2001, Analysis of regression in game theory approach; Harvey, Liu and Zhu 2016 (RFS) and Bailey and Lopez de Prado 2014 (pointers to Book 4 ch. 12); published descriptions of research governance by quantitative managers (papers or firm publications; only as cited) (optional).
- **Data.** Synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Shapley, A value for n-person games, in Contributions to the Theory of Games II (Annals of Mathematics Studies 28), 307-318, 1953 | Crossref | https://api.crossref.org/works/10.1515/9781400881970-018 | 2026-09-28 | title, volume, pages | prop Shapley; omsources |
| F2 | Lipovetsky and Conklin, Analysis of regression in game theory approach, Applied Stochastic Models in Business and Industry 17(4), 319-330, 2001 (Shapley decomposition of a regression's fit) | Crossref | https://api.crossref.org/works/10.1002/asmb.446 | 2026-09-28 | title, journal, volume, pages | section 3; omsources |
| F3 | Bailey and Lopez de Prado, The deflated Sharpe ratio, Journal of Portfolio Management 40(5), 94-107, 2014 | Crossref | https://api.crossref.org/works/10.3905/jpm.2014.40.5.094 | 2026-09-28 | title, journal, volume, pages | section 4; omsources |
| F4 | Harvey, Liu and Zhu, ... and the cross-section of expected returns, Review of Financial Studies 29(1), 5-68, 2016 | Crossref | https://api.crossref.org/works/10.1093/rfs/hhv059 | 2026-09-28 | title, journal, volume, pages | section 4; omsources |

## EXCLUDED


# 4. Greeks and the Hedging P\&L — brief and source ledger

## Brief

- **Hook.** An options trader is short one-month at-the-money straddles at 20 volatility; the share realises 25; at the end of the month the hedged book has lost almost exactly what the gamma-theta identity predicted on the first morning.
- **Sections.** The Greeks and their shapes; The gamma-theta identity and the hedging P&L; Discrete hedging error; Break-even volatility; Which volatility to hedge at.
- **Defines.** Greeks, vega, theta, rho, vanna, volga, cash gamma, straddle, hedging P\&L, discrete hedging error, break-even volatility, bump-and-reprice.
- **Uses (defined earlier).** delta, delta hedging, gamma (Book 1 ch. 26), realised volatility, implied volatility (Book 1 ch. 25), P\&L attribution (Book 1 ch. 7), delta-neutral straddle (Book 2 ch. 19), Itô's formula (Book 4 ch. 3), quadratic variation (Book 4 ch. 2), finite differences (Book 4 ch. 27), Black--Scholes formula (ch. 3).
- **Tutorial.** Simulate delta hedging of a short call sold at 20% implied when realised is 25%, daily and hourly, hedged at the implied and at the realised volatility; plot the distribution of the hedging P&L and the path of cumulative gamma P&L.
- **Build.** `firm.greeks`: Greek calculator: analytic Greeks from `firm.bs`, central bump-and-reprice for any pricer, Greeks in money units (cash gamma, theta per day, vega per point), and the next-day P&L predictor.
- **Weekend problem.** The short-straddle month — named result: the hedged P&L of a short one-month straddle when realised volatility exceeds implied by five points: its expectation from the gamma-theta identity and its standard deviation under daily hedging.
- **Facts to verify.** Boyle-Emanuel 1980 discrete hedging error; Leland 1985 transaction costs; Ahmad-Wilmott 2005 'Which free lunch would you like today, sir?' (hedging at implied versus realised); Carr's and Bergomi's P&L-of-hedging derivations (book references).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Standard deviation of discrete-hedging P&L of an option hedged N times approx sqrt(pi/4) * vega * sigma / sqrt(N); prefactor 0.886; quadrupling the hedges halves the error; example S=100, T=1/12, vega 0.115 per vol point | Derman and Kamal, "When you cannot hedge continuously: the corrections of Black-Scholes", Goldman Sachs research note (published in Risk, 1999), PDF via pdftotext | https://raw.githubusercontent.com/s0ap/gs-quantitative-strategies-research-notes/master/When%20You%20Cannot%20Hedge%20Continuously%20-%20The%20Corrections%20of%20Black-Scholes.pdf | 2026-09-24 | "The numerical prefactor, sqrt(pi/4) is slightly less than one: 0.886"; "If you rebalance four times as frequently, you halve the typical size of the hedging error" | prop dk; ex 6; omsources |
| F2 | Derman-Kamal note: replication error proportional to vega times volatility uncertainty; published 1999 | author's page | https://emanuelderman.com/when-you-cannot-hedge-continuously-the-corrections-of-black-scholes/ | 2026-09-24 | "the typical error in the replication value is proportional to the vega of the option" | prop dk |
| F3 | Boyle and Emanuel, "Discretely adjusted option hedges", JFE 8(3) (1980) 259-282 | IDEAS/RePEc record | https://ideas.repec.org/a/eee/jfinec/v8y1980i3p259-282.html | 2026-09-24 | bibliographic record | omsources |
| F4 | Ahmad and Wilmott, "Which free lunch would you like today, Sir?", Wilmott, November 2005, 64-79: hedging with implied versus forecast volatility | Wilmott.com article page | https://www.wilmott.com/which-free-lunch-would-you-like-today-sir-delta-hedging-volatility-arbitrage-and-optimal-portfolios-riaz-ahmad-and-paul-wilmott/ | 2026-09-24 | bibliographic record (search summary: "November 2005, pages 64-79") | §5; omsources |
| F5 | Leland, "Option pricing and replication with transactions costs", JF 40 (1985) 1283-1301 | Wiley record | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1985.tb02383.x | 2026-09-24 | bibliographic record | ex 5; omsources |

## EXCLUDED

- None. The desk of the hook is illustrative; all its numbers are computed.

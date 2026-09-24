# 9. Local Volatility — brief and source ledger

## Brief

- **Hook.** Two desks price the same one-year cliquet with two models that both fit every listed vanilla to the tick; their prices differ by a third.
- **Sections.** Dupire's formula; Local volatility from implied volatility; Calibration in practice; What local volatility predicts: dynamics and the forward smile.
- **Defines.** local volatility, local volatility model, Dupire formula, Markovian projection, forward smile.
- **Uses (defined earlier).** volatility surface, total implied variance, log-moneyness, sticky strike (ch. 7), SVI parametrisation, surface SVI (ch. 8), Kolmogorov forward equation (Book 4 ch. 4), Monte Carlo (Book 4 ch. 26).
- **Tutorial.** Compute local volatility from an SSVI surface with the total-variance form of Dupire's formula, reprice vanillas by Monte Carlo under it to check the fit, then compute the forward smile it implies and compare it with today's smile.
- **Build.** `firm.localvol`: Dupire local-volatility surface from a `volsurface` (total-variance formula, guarded derivatives) and a local-volatility path generator.
- **Weekend problem.** The flattening forward smile — named result: the at-the-money skew of the six-month smile six months forward under local volatility, as a fraction of today's six-month skew.
- **Facts to verify.** Dupire 1994 Risk 'Pricing with a smile'; Derman-Kani 1994; Gyöngy 1986 mimicking theorem; Hagan et al. 2002 on local volatility's smile dynamics.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Dupire, "Pricing with a smile", Risk 7(1), January 1994, 18-20: local volatility consistent with the surface of option prices | Semantic Scholar record (search summary) | https://www.semanticscholar.org/paper/Pricing-with-a-Smile-Dupire/03798655e555ca39ed845e4399f745b3d0d11681 | 2026-09-24 | "published in January 1994 in Risk, volume 7, issue 1 ... pages 18-20" (search summary) | thm Dupire; omsources |
| F2 | Derman and Kani, "Riding on a smile", Risk 7(2) (1994) 32-39: implied binomial trees with a local volatility at each node | Derman's Goldman Sachs note "The volatility smile and its implied tree" (PDF) | https://www.cmat.edu.uy/~mordecki/hk/derman-kani.pdf | 2026-09-24 | "RISK 7, issue 2, pages 32-39" (search summary) | omsources |
| F3 | Gyongy (1986), Probability Theory and Related Fields 71, 501-516: an SDE with non-random coefficients has the same one-dimensional marginals as a given Ito process; coefficients are conditional expectations of the original volatility and drift | Springer record | https://link.springer.com/article/10.1007/BF00699039 | 2026-09-24 | "coefficients have a simple interpretation involving conditional expectations of the volatility and drift" (search summary) | def Markovian projection; omsources |
| F4 | Local volatility models predict that when the underlying falls the smile shifts to higher prices, the opposite of observed market behaviour (rates), making their hedges unstable; SABR proposed instead; Wilmott, January 2002 | Hagan, Kumar, Lesniewski, Woodward, "Managing smile risk" (deriscope PDF / ResearchGate record) | https://www.deriscope.com/docs/Hagan_2002.pdf | 2026-09-24 | "when the price of the underlying decreases, local vol models predict that the smile shifts to higher prices" (search summary) | §4; omsources |
| F5 | Under local volatility the at-the-money volatility moves "twice as fast" as the skew (short maturity, weak skew): d sigma_{K=S}/d ln S = 2 d sigma/d ln K; forward smiles in local volatility depend substantially on the forward date and spot; Risk, September 2004 | L. Bergomi, "Smile dynamics", Risk, September 2004 (PDF via pdftotext) | https://www.maths.univ-evry.fr/pages_perso/crepey/Finance/0904_tech_bergomi.pdf | 2026-09-24 | "showing that sigma_{K=S} moves 'twice as fast' as the skew"; "forward smiles depend substantially on the forward date and the spot value at the forward date" | prop dynamics; §4; omsources |

## EXCLUDED

- The market's own forward skews (whether they flatten) are not measured: the chapter compares models only.

# 23. Monte Carlo Pricers in Practice — brief and source ledger

## Brief

- **Hook.** A Bermudan option on a basket of five shares has no grid that fits in memory; a Monte Carlo engine prices it in a second and gets the exercise decision wrong by design, which is why its answer is a lower bound.
- **Sections.** Simulating the models; Early exercise by regression; Greeks: pathwise, likelihood ratio, adjoint; Bridges and quasi-random numbers; Engineering a Monte Carlo pricer.
- **Defines.** Longstaff--Schwartz method, dual upper bound, pathwise Greek, likelihood-ratio Greek, quadratic-exponential scheme.
- **Uses (defined earlier).** Monte Carlo, variance reduction, control variate, antithetic variates, low-discrepancy sequence, Euler scheme, multilevel Monte Carlo (Book 4 ch. 26), Brownian bridge (Book 4 ch. 2 or 26), algorithmic differentiation, adjoint mode (Book 4 ch. 28), Bermudan exercise (ch. 6), Heston model (ch. 10), digital option (ch. 15), worst-of option (ch. 17).
- **Tutorial.** Price a Bermudan put by Longstaff-Schwartz and bound it above by the Andersen-Broadie dual; compute the delta and vega of a digital pathwise, by likelihood ratio and by adjoint differentiation, and compare their variances.
- **Build.** `firm.mcpricer`: Monte Carlo engine (path generators for Black-Scholes, local volatility and Heston-QE; payoffs from `pathdep` and `autocall`; Longstaff-Schwartz; pathwise and likelihood-ratio Greeks; common random numbers across bumps).
- **Weekend problem.** The Bermudan bounds — named result: the gap between the Longstaff-Schwartz lower bound and the dual upper bound for a three-asset Bermudan max-call, and its sensitivity to the regression basis.
- **Facts to verify.** Longstaff-Schwartz 2001 RFS; Andersen-Broadie 2004 Management Science; Andersen 2008 J. Computational Finance, QE scheme; Broadie-Glasserman 1996 Management Science, Greeks; Giles-Glasserman 2006 Risk 'Smoking adjoints'; Glasserman 2003 book.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Longstaff and Schwartz, "Valuing American options by simulation: a simple least-squares approach", Review of Financial Studies 14(1) (2001) 113-147 | Crossref record 10.1093/rfs/14.1.113 | https://api.crossref.org/works/10.1093/rfs/14.1.113 | 2026-09-24 | Crossref metadata | def Longstaff-Schwartz, omsources |
| F2 | Andersen and Broadie, "Primal-dual simulation algorithm for pricing multidimensional American options", Management Science 50(9) (2004) 1222-1234: lower bounds from any primal algorithm, upper bounds by Monte Carlo from the duality representation of Haugh and Kogan (2004) and Rogers (2002); valid confidence intervals | Crossref record with abstract, 10.1287/mnsc.1040.0258 | https://api.crossref.org/works/10.1287/mnsc.1040.0258 | 2026-09-24 | abstract in Crossref | def dual upper bound, omsources |
| F3 | Andersen, "Simple and efficient simulation of the Heston stochastic volatility model", Journal of Computational Finance 11(3) (2008) 1-42 | Crossref record 10.21314/JCF.2008.189 | https://api.crossref.org/works/10.21314/JCF.2008.189 | 2026-09-24 | Crossref metadata | def QE scheme, omsources |
| F4 | Broadie and Glasserman, "Estimating security price derivatives using simulation", Management Science 42(2) (1996) 269-285: pathwise and likelihood-ratio methods; one simulation estimates several derivatives; unbiased, unlike resimulation | Crossref record with abstract, 10.1287/mnsc.42.2.269 | https://api.crossref.org/works/10.1287/mnsc.42.2.269 | 2026-09-24 | abstract in Crossref | sec. Greeks, omsources |
| F5 | Glasserman, Monte Carlo Methods in Financial Engineering (Springer, 2003) | Crossref record 10.1007/978-0-387-21617-1 | https://api.crossref.org/works/10.1007/978-0-387-21617-1 | 2026-09-24 | Crossref metadata | omsources |
| F6 | Giles and Glasserman, "Smoking adjoints": an adjoint method for Monte Carlo Greeks; along each path the forward and adjoint implementations produce the same values, the adjoint rearranges the calculation; it outperforms a forward implementation for few outputs and many inputs (e.g. points of a volatility surface); published as "Smoking adjoints: fast Monte Carlo Greeks", Risk 19 (2006) 88-92 | Oxford University Computing Laboratory report NA-05-15 (August 2005), abstract; Risk.net article page | https://people.maths.ox.ac.uk/~gilesm/files/NA-05-15.pdf | 2026-09-24 | report abstract (pdftotext); venue from https://www.risk.net/derivatives/interest-rate-derivatives/1500261/smoking-adjoints-fast-monte-carlo-greeks and search excerpt | sec. Greeks, omsources |

## EXCLUDED

- Published reference values for the three-asset Bermudan max-call: not re-verified; the chapter reports its own bounds only.

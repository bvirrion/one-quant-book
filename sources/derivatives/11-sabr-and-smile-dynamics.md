# 11. SABR and Smile Dynamics — brief and source ledger

## Brief

- **Hook.** In 2002 four authors showed that the model many desks used to fit smiles predicted the smile would move the wrong way when the forward moved, so that its hedges were worse than none.
- **Sections.** The SABR model; The asymptotic formula; Backbone and smile dynamics; Hedging under a smile model; Limits: wings and long expiries.
- **Defines.** SABR model, Hagan formula, backbone, minimum-variance delta.
- **Uses (defined earlier).** stochastic volatility model, volatility of volatility, spot--volatility correlation (ch. 10), local volatility (ch. 9), sticky strike, sticky delta (ch. 7), Black model (ch. 3), vanna, volga (ch. 4), Bachelier model, normal volatility (Book 2 ch. 13).
- **Tutorial.** Implement Hagan's lognormal and normal formulas, fit SABR at one expiry, plot the backbone for beta 0, one half and 1, and compare the Black delta, the minimum-variance delta and the realised hedge ratio on simulated paths.
- **Build.** `firm.sabr`: Hagan implied-volatility formulas (lognormal and normal), calibration with fixed beta, minimum-variance delta (Book 6 ch. 5 builds the cube and shifted SABR on it).
- **Weekend problem.** Which delta — named result: the reduction in the variance of the hedging error from the minimum-variance delta over the Black delta on simulated SABR paths.
- **Facts to verify.** Hagan, Kumar, Lesniewski, Woodward 2002 Wilmott 'Managing smile risk'; Bartlett 2006 Wilmott 'Hedging under SABR model'; Obłój 2008 correction; Hagan et al. 2014 arbitrage-free SABR (negative density in the wings).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Hagan et al. (2002): SABR implied volatility formula (2.17a-c) and ATM formula (2.18); backbone traced by sigma_B(f, f); local vol predicts the smile moves opposite to the forward, contrary to the market, and its hedges can be unstable; SABR as the remedy; Wilmott, January 2002 | P. S. Hagan, D. Kumar, A. S. Lesniewski, D. E. Woodward, "Managing smile risk" (deriscope PDF via pdftotext) | https://www.deriscope.com/docs/Hagan_2002.pdf | 2026-09-24 | "x(z) = log( (sqrt(1 - 2 rho z + z^2) + z - rho) / (1 - rho) )" (2.17c); "is known as the backbone" | def Hagan; def backbone; hook; omsources |
| F2 | Bartlett, "Hedging under SABR model", Wilmott, July/August 2006, 2-4: delta accounting for the volatility move induced by the forward's move | Wilmott.com page; search summary | https://wilmott.com/hedging-under-sabr-model-wilmott-magazine-article-bruce-bartlett/ | 2026-09-24 | "an alternative formula for delta in the SABR model that accounts for a forward swap rate change induced jump in instantaneous volatility" (search summary) | def MV delta; omsources |
| F3 | Oblój, "Fine-tune your smile: correction to Hagan et al.", Wilmott, May 2008, 102-109: corrected zero-order term | arXiv 0708.0998 | https://arxiv.org/abs/0708.0998 | 2026-09-24 | "derive explicitly the correct zero order term in the expansion of the implied volatility" (abstract via search) | §5; omsources |
| F4 | Hagan et al., "Arbitrage-free SABR", Wilmott 2014 (69), 60-75: the explicit formulas can lead to arbitrage for low strikes; an effective one-dimensional forward equation for the density gives arbitrage-free prices | Wiley record | https://onlinelibrary.wiley.com/doi/abs/10.1002/wilm.10290 | 2026-09-24 | "which can lead to arbitrage for low strike options" (abstract via search) | §5; omsources |

## EXCLUDED

- The claim that SABR is "the market standard for interest-rate options" is stated from the 2002 paper's own framing and the chapter's use in Book 6; no market survey was found. The hook states it as common use, not as a measured share.

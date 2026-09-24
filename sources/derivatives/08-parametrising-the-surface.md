# 8. Parametrising the Surface — brief and source ledger

## Brief

- **Hook.** A market maker's screen refreshes 400 strikes on 20 expiries several times a second; the model behind it has five numbers per expiry.
- **Sections.** Why parametrise; SVI and its surface version; Splines and non-parametric fits; Fitting to bid and ask; Events, and business time against calendar time.
- **Defines.** SVI parametrisation, surface SVI, Lee moment formula, event variance, business time.
- **Uses (defined earlier).** total implied variance, log-moneyness, butterfly arbitrage, calendar arbitrage (ch. 7), vega (ch. 4), least squares, Levenberg--Marquardt (Book 4 ch. 16, 24), spline (Book 4 ch. 28), bid--ask spread (Book 1 ch. 1).
- **Tutorial.** Fit raw SVI slice by slice to bid and ask quotes of a synthetic chain with vega weights, check it is free of butterfly arbitrage, fit SSVI to the whole surface and compare the errors; strip an earnings event out of the term structure.
- **Build.** `firm.svi`: SVI/SSVI fitter (quasi-explicit slice fit, bid-ask-aware objective, arbitrage checks) plugged into `volsurface`.
- **Weekend problem.** Earnings week — named result: the implied move of an earnings announcement from the jump in total variance between the expiries before and after it.
- **Facts to verify.** Gatheral 2004 SVI presentation (Merrill Lynch origin, 1999); Gatheral-Jacquier 2014 Quant. Finance, arbitrage-free SVI; Lee 2004 Math. Finance moment formula; Zeliade 2009 quasi-explicit SVI calibration white paper; Dubinsky-Johannes 2006 earnings announcements and option prices.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | SVI devised at Merrill Lynch in 1999 and publicly disseminated later (Gatheral 2004); SVI total variance linear in k in the wings, consistent with Lee's moment formula | Gatheral and Jacquier, arXiv 1204.0646 (PDF via pdftotext), introduction | https://arxiv.org/abs/1204.0646 | 2026-09-24 | "was originally devised at Merrill Lynch in 1999 and subsequently publicly disseminated" | §2; omsources |
| F2 | SSVI definition w(k, theta) = theta/2 (1 + rho phi k + sqrt((phi k + rho)^2 + 1 - rho^2)); Theorem 4.1 calendar conditions (theta increasing; 0 <= d(theta phi)/dtheta <= (1 + sqrt(1 - rho^2)) phi / rho^2); power law phi = eta theta^(-gamma) with 0 < gamma < 1 satisfies it; with gamma = 1/2 the ATM skew is rho eta / (2 sqrt t); Theorem 4.2 butterfly conditions theta phi (1+|rho|) < 4 and theta phi^2 (1+|rho|) <= 4, the first necessary (Lemma 4.2); QF 14(1) (2014) 59-71 | same PDF, section 4 | https://arxiv.org/abs/1204.0646 | 2026-09-24 | "The SSVI volatility surface (4.1) is free of butterfly arbitrage if ... theta phi(theta)(1 + |rho|) < 4; theta phi(theta)^2 (1 + |rho|) <= 4" | def SSVI; thm; ex 5 |
| F3 | Lee's moment formula: beta_R = limsup I^2(x)/(|x|/T) in [0,2], beta_R = 2 - 4(sqrt(p^2 + p) - p) with p = sup{p: E S^(1+p) < inf}; left wing with q = sup{q: E S^(-q) < inf}; Mathematical Finance 14(3) (2004) 469-480 | R. W. Lee, "The moment formula for implied volatility at extreme strikes" (author's PDF via pdftotext) | http://math.uchicago.edu/~rogerlee/moment.pdf | 2026-09-24 | "Theorem 3.2 (The Moment Formula, part 1) ... Then beta_R in [0, 2] and ... beta_R = 2 - 4(sqrt(p^2 + p) - p)" | thm Lee; ex 2 |
| F4 | Quasi-explicit calibration of SVI by dimension reduction (Zeliade white paper ZWP-0005, C. Martini and S. De Marco, June 2009, revised February 2012) | Zeliade | https://www.zeliade.com/wp-content/uploads/whitepapers/zwp-0005-SVICalibration.pdf | 2026-09-24 | "a procedure based on dimension reduction in parameters space providing a quasi-explicit calibration" (search summary) | method; omsources |
| F5 | Implied volatility of individual equity options rises before earnings announcements and drops sharply after | Dubinsky and Johannes, "Earnings announcements and equity options", Columbia working paper (2006) | https://business.columbia.edu/sites/default/files-efs/pubfiles/6051/DJ_2006.pdf | 2026-09-24 | "Implied volatility increases prior to earnings announcements and then drops off sharply immediately thereafter" (search summary) | §5; omsources |

## EXCLUDED

- Gatheral's 2004 Global Derivatives presentation is cited from the Gatheral-Jacquier reference list, not fetched.

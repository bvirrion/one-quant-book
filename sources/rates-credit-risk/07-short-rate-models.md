# 7. Short-Rate Models — brief and source ledger

## Brief

- **Hook.** Every night a bank must value ten thousand callable bonds and mortgage pools; a one-factor tree does it in minutes, and its weaknesses are known by name.
- **Sections.** The short rate and affine bond prices; Vasicek and Hull--White; Calibration to the curve and to swaptions; Trees; Two factors, and what one factor cannot do.
- **Defines.** short-rate model, affine term-structure model, Vasicek model, Hull--White model, Black--Karasinski model, Jamshidian decomposition, two-factor Gaussian model.
- **Uses (defined earlier).** Ornstein--Uhlenbeck process (B4.4), square-root process (B4.4), Feynman--Kac formula (B4.4), numeraire (B4.5), forward measure (B4.5), Monte Carlo (B4.26), finite-difference method (B4.27), recombining tree (B5.2), trinomial tree (B5.22), zero-coupon rate (B2.3), swaption (B2.13), normal volatility (B2.13), instantaneous forward rate (ch1), curve calibration (ch1).
- **Tutorial.** Fit Hull--White to the curve, calibrate its mean reversion and volatility to co-terminal swaptions through the Jamshidian decomposition, build the trinomial tree and check that it reprices bonds and swaptions.
- **Build.** `firm.shortrate`: Hull--White closed forms, trinomial tree and calibration; two-factor Gaussian bond prices.
- **Weekend problem.** One sigma is not enough — named result: the co-terminal swaption pricing errors with a constant volatility and with a piecewise-constant one, and the calibrated volatility term structure.
- **Facts to verify.** Vasicek 1977, Hull-White 1990, Black-Karasinski 1991, Jamshidian 1989 (papers); Brigo and Mercurio 2006 (textbook).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Vasicek (1977): a diffusion model of the short rate and the resulting term structure | O. Vasicek, "An equilibrium characterization of the term structure", Journal of Financial Economics 5(2), 177-188, 1977 | https://ideas.repec.org/a/eee/jfinec/v5y1977i2p177-188.html | 2026-09-24 | bibliographic record | def:rc:short-rate-models:vasicek, omsources |
| F2 | Hull and White (1990) extended the Vasicek and CIR models to fit the current term structure (and volatilities); the extended Vasicek model is analytically tractable | J. Hull and A. White, "Pricing interest-rate-derivative securities", Review of Financial Studies 3(4), 573-592, 1990 | https://academic.oup.com/rfs/article-abstract/3/4/573/1585938 | 2026-09-24 | abstract | def:rc:short-rate-models:hw, omsources |
| F3 | Jamshidian (1989) derived an exact formula for European options on discount bonds in a Gaussian mean-reverting model and extended it to options on portfolios of discount bonds | F. Jamshidian, "An exact bond option formula", Journal of Finance 44, 205-209, 1989 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1989.tb02413.x | 2026-09-24 | abstract | def:rc:short-rate-models:jamshidian, omsources |
| F4 | Black and Karasinski (1991): a one-factor model in which the short rate is lognormal, with deterministic time-dependent target rate, mean reversion and volatility | F. Black and P. Karasinski, "Bond and option pricing when short rates are lognormal", Financial Analysts Journal 47(4), 1991 | https://rpc.cfainstitute.org/research/financial-analysts-journal/1991/bond-and-option-pricing-when-short-rates-are-lognormal | 2026-09-24 | abstract: "the distribution of possible short rates is lognormal" | def:rc:short-rate-models:bk, omsources |

## EXCLUDED

- The Hull-White (1994) tree paper: the construction is derived in the text; no factual claim beyond attribution. The co-terminal volatilities come from chapter 5's synthetic cube (illustrative); G2++ parameters are illustrative, set to match the Treasury 2y/10y correlation of chapter 6. Re-checked 2026-09-24: no factual claim to restore.


# 21. Convertibles and the Credit--Equity Link — brief and source ledger

## Brief

- **Hook.** With the share at 30 and the conversion price at 40 a convertible trades like a bond; with the share at 60, like the share; a convertible desk lives in the region between, hedged with the share and a credit default swap.
- **Sections.** The instrument; Bond floor, conversion value and the convex region; Equity-to-credit models; What a convertible desk hedges; Convertible arbitrage and its crises.
- **Defines.** convertible bond, conversion ratio, conversion price, conversion value, conversion premium, bond floor, soft call, equity-to-credit model, convertible arbitrage.
- **Uses (defined earlier).** credit spread, recovery rate (Book 2 ch. 21), hazard rate, credit default swap (Book 2 ch. 23), contingent convertible bond (Book 2 ch. 26), callable bond (Book 2 ch. 13), exercise boundary (ch. 6), Black--Scholes equation (ch. 3), finite differences (Book 4 ch. 27), jump-to-default risk (Book 6 ch. 13), structural model (Book 6 ch. 14).
- **Tutorial.** Price a convertible on a one-dimensional grid with a hazard rate that rises as the share falls, compare it with the constant-hazard model, and compute the delta, the credit sensitivity and the hedge a convertible-arbitrage book holds.
- **Build.** `firm.convertible`: convertible-bond pricer (Crank-Nicolson grid, issuer calls with soft-call trigger, investor puts, equity-to-credit hazard) with delta, gamma and credit sensitivities.
- **Weekend problem.** The spring of 2005 — named result: the loss of a delta-hedged convertible-arbitrage position when the issuer's credit spread widens by 300 bp while its share falls 20%.
- **Facts to verify.** Tsiveriotis-Fernandes 1998 J. Fixed Income; Ayache, Forsyth, Vetzal 2003; Andersen-Buffum 2003 equity-to-credit; 2005 convertible-arbitrage drawdown (Mitchell, Pedersen, Pulvino 2007); 2008 convertible-arbitrage crisis (Mitchell-Pulvino 2012 JFE); global convertible issuance (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Tsiveriotis and Fernandes, "Valuing convertible bonds with credit risk", Journal of Fixed Income 8(2) (1998) 95-102 | Crossref record 10.3905/jfi.1998.408243 | https://api.crossref.org/works/10.3905/jfi.1998.408243 | 2026-09-24 | Crossref metadata | sec. equity-to-credit models, omsources |
| F2 | Ayache, Forsyth and Vetzal, "Valuation of convertible bonds with credit risk", Journal of Derivatives 11(1) (2003) 9-29 | Crossref record 10.3905/jod.2003.319208 | https://api.crossref.org/works/10.3905/jod.2003.319208 | 2026-09-24 | Crossref metadata | sec. equity-to-credit models, omsources |
| F3 | Andersen and Buffum, "Calibration and implementation of convertible bond models", Journal of Computational Finance 7 (2003) 1-34: naive calibration can lead to highly significant pricing biases; joint calibration to debt and option markets through the Fokker-Planck equation; finite differences rather than the trees that dominated the literature | Crossref records 10.21314/JCF.2003.124 and SSRN 355308 (abstract) | https://api.crossref.org/works/10.2139/ssrn.355308 | 2026-09-24 | abstract in Crossref | sec. equity-to-credit models, omsources |
| F4 | Mitchell, Pedersen and Pulvino, "Slow moving capital", American Economic Review 97(2) (2007) 215-220 | Crossref record 10.1257/aer.97.2.215 | https://api.crossref.org/works/10.1257/aer.97.2.215 | 2026-09-24 | Crossref metadata (title) | sec. crises, omsources |
| F5 | Mitchell and Pulvino, "Arbitrage crashes and the speed of capital", Journal of Financial Economics 104(3) (2012) 469-490: the imminent failure of large prime brokers in 2008 sharply cut the leverage afforded to hedge funds; long-term financing became short-term; relative-value funds could not keep substantially similar assets at similar prices | Crossref records 10.1016/j.jfineco.2011.09.002 and SSRN 1628261 (abstract) | https://api.crossref.org/works/10.2139/ssrn.1628261 | 2026-09-24 | abstract in Crossref | sec. crises |
| F6 | Convertible arbitrage and other hedge funds account for up to 75% of the convertible market; in early 2005 large institutional investors began to withdraw capital from convertible-arbitrage funds; according to the Barclay Group more than 20% of capital was redeemed in the first quarter of 2005; the redemptions led to massive bond sales and reduced convertible prices relative to fundamental values | Mitchell, Pedersen and Pulvino, "Slow moving capital" (AER 2007), author PDF | https://pages.stern.nyu.edu/~lpederse/papers/SlowMovingCapital.pdf | 2026-09-24 | pdftotext, section I (quoted) | sec. convertible arbitrage |

## EXCLUDED

- Fund-level drawdowns of 2005: not stated; the redemption share (F6, restored in Phase C from the authors' PDF) is the only number used.
- Global convertible issuance and the size of the convertible-arbitrage industry: not fetched; not stated.

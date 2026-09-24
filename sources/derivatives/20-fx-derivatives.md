# 20. FX Derivatives — brief and source ledger

## Brief

- **Hook.** In August 2015 the renminbi's central fixing moved by nearly 2% in one day, and companies across Asia holding target-redemption forwards on the dollar-renminbi rate found the sign of their exposure had turned.
- **Sections.** Pricing conventions revisited; The vanna-volga method; Barriers and target-redemption forwards; Stochastic-local volatility; An FX exotic book.
- **Defines.** Garman--Kohlhagen model, vanna--volga method, target redemption forward, accumulator, stochastic-local volatility model, leverage function.
- **Uses (defined earlier).** spot delta, forward delta, premium-adjusted delta, delta-neutral straddle, risk reversal, butterfly, barrier option (Book 2 ch. 19), currency pair, base currency, quote currency (Book 2 ch. 14), one-touch option, barrier shift (ch. 15), local volatility, Markovian projection (ch. 9), Heston model (ch. 10), vanna, volga (ch. 4).
- **Tutorial.** Price a one-touch and a double-no-touch by vanna-volga from ATM, RR and BF quotes (building on Book 2's `firm.fxsmile`), then a target-redemption forward by Monte Carlo under local volatility and under SLV with a calibrated leverage function.
- **Build.** `firm.fxvol`: vanna-volga pricer, target-redemption-forward Monte Carlo, SLV leverage function calibrated by the particle method.
- **Weekend problem.** The TARF — named result: the expected number of fixings before redemption and the client's expected loss per million when spot moves 10% against it in the first quarter.
- **Facts to verify.** PBoC 11 August 2015 fixing change (PBoC statement); CNH TRF losses 2015-16 (HKMA / SFC / quality press); 2008 accumulator losses (HK regulators); Castagna-Mercurio 2007 Risk, vanna-volga; Guyon, Henry-Labordère 2011 particle method; Garman-Kohlhagen 1983 JIMF; FX options turnover share (reuse Book 2 ledger).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | On 11 August 2015 the People's Bank of China announced that the renminbi would continue to trade against the US dollar in a +-2% daily band around a central parity now determined by the previous day's closing market rate rather than a preset target; the renminbi slipped 2.8% against the dollar in the two days after the announcement before stabilising when the PBoC intervened; the Malaysian ringgit depreciated by more than 6% after the announcement; from the start of 2015 up to the new fixing method the renminbi had traded consistently towards the weaker end of its band | BIS Quarterly Review, September 2015, "EME vulnerabilities take centre stage" | https://www.bis.org/publ/qtrpdf/r_qt1509a.htm | 2026-09-24 | page text | hook, sec. an FX exotic book |
| F2 | Garman and Kohlhagen, "Foreign currency option values", Journal of International Money and Finance 2(3) (1983) 231-237 | Crossref record 10.1016/S0261-5606(83)80001-1 | https://api.crossref.org/works/10.1016/S0261-5606(83)80001-1 | 2026-09-24 | Crossref metadata | def GK, omsources |
| F3 | Guyon and Henry-Labordere, "The smile calibration problem solved" (SSRN 1885032, 2011): exact calibration of multi-factor local stochastic volatility models to market smiles by McKean's particle method, extending to hybrid models | Crossref record with abstract, 10.2139/ssrn.1885032 | https://api.crossref.org/works/10.2139/ssrn.1885032 | 2026-09-24 | abstract in Crossref | sec. stochastic-local volatility, omsources |
| F4 | Vanna-volga is a popular method for interpolating and extrapolating volatility smiles, widely used in FX markets because it constructs the whole smile from three market quotes | Perederiy, "Vanna-volga method for normal volatilities" (SSRN 3262146, 2018), abstract | https://api.crossref.org/works/10.2139/ssrn.3262146 | 2026-09-24 | abstract in Crossref | sec. vanna-volga |
| F5 | The main assumption of the vanna-volga method is a flat but stochastic implied volatility for pricing vanilla options | Rolloos, "On the flat but stochastic implied volatility assumption in the vanna-volga model" (SSRN 4287718, 2022), abstract | https://api.crossref.org/works/10.2139/ssrn.4287718 | 2026-09-24 | abstract in Crossref | sec. vanna-volga |

## EXCLUDED

- Castagna and Mercurio (2007, Risk) on vanna-volga: no fetchable record; the method is presented from its construction.
- Losses of Asian companies on renminbi target-redemption forwards in 2015-16 and on accumulators in 2008 (HKMA, SFC, press): not fetched; the chapter describes the mechanism on a synthetic pair and states no losses.
- FX options turnover shares: not needed; not stated.

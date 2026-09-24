# 15. Barriers and Digitals — brief and source ledger

## Brief

- **Hook.** A digital pays 10 million if the index closes above 5,000; with the index at 4,999.9 and one minute to the close, its delta is larger than the desk's whole index position.
- **Sections.** Digitals and their hedge; Barriers by reflection; Static hedging; Discrete monitoring and the barrier shift; Gap risk at the barrier.
- **Defines.** digital option, one-touch option, no-touch option, double-barrier option, barrier rebate, call-spread overhedge, static hedging, barrier shift, gap risk.
- **Uses (defined earlier).** barrier option, knock-out option, knock-in option (Book 2 ch. 19), reflection principle (Book 4 ch. 2), Black--Scholes formula (ch. 3), vanna, volga (ch. 4), local volatility (ch. 9).
- **Tutorial.** Price a down-and-out call in closed form, with discrete monitoring by Monte Carlo and with the barrier shift; hedge a digital with a call spread; build a static hedge of a barrier from vanillas.
- **Build.** `firm.barrier`: barrier and digital pricer (closed forms with rebates, the discrete-monitoring shift, double barriers by series) and a static-hedge builder.
- **Weekend problem.** The digital at expiry — named result: the call-spread width that caps the hedger's loss at 50,000 on a 10-million digital, and the overhedge cost it charges the client.
- **Facts to verify.** Reiner-Rubinstein 1991 barrier closed forms; Broadie, Glasserman, Kou 1997 continuity correction (0.5826); Derman, Ergener, Kani 1995 static hedging; Carr, Ellis, Gupta 1998 static hedging; SNB removal of the EURCHF floor, 15 January 2015 (gap).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Discretely monitored barrier options can be priced with the continuous formulas after shifting the barrier away from the underlying by exp(beta sigma sqrt(dt)), beta ~ 0.5826; Broadie, Glasserman and Kou, "A continuity correction for discrete barrier options", Mathematical Finance 7(4) (1997) 325-349 | Crossref record with abstract, 10.1111/1467-9965.00035 | https://api.crossref.org/works/10.1111/1467-9965.00035 | 2026-09-24 | abstract in Crossref ("shifts the barrier away from the underlying by a factor of exp(beta sigma sqrt dt), where beta approx 0.5826") | sec. discrete monitoring, build |
| F2 | Derman, Ergener and Kani, "Static options replication", Journal of Derivatives 2(4) (1995) 78-95 | Crossref record 10.3905/jod.1995.407927 | https://api.crossref.org/works/10.3905/jod.1995.407927 | 2026-09-24 | Crossref metadata | sec. static hedging, omsources |
| F3 | Carr, Ellis and Gupta, "Static hedging of exotic options", Journal of Finance 53(3) (1998) 1165-1190 | Crossref record 10.1111/0022-1082.00048 | https://api.crossref.org/works/10.1111/0022-1082.00048 | 2026-09-24 | Crossref metadata | sec. static hedging, omsources |
| F4 | On 15 January 2015 the Swiss National Bank discontinued the minimum exchange rate of CHF 1.20 per euro and lowered the rate on sight deposits above the exemption threshold to -0.75% | SNB press release, 15 January 2015 (PDF) | https://www.snb.ch/public/asset/en/www-snb-ch/publications/communication/press-releases/2015/pre_20150115/publications0_en/pre_20150115.en.pdf | 2026-09-24 | "The Swiss National Bank (SNB) is discontinuing the minimum exchange rate of CHF 1.20 per euro" | sec. gap risk, dated box |
| F5 | ECB euro reference rate for CHF: 1.2010 on 14 January 2015, 1.0280 on 15 January, 1.0128 on 16 January | ECB euro foreign exchange reference rates, full history (eurofxref-hist.csv) | https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip | 2026-09-24 | CSV rows 2015-01-14, 2015-01-15, 2015-01-16, column CHF | sec. gap risk, dated box |

## EXCLUDED

- Reiner and Rubinstein, "Breaking down the barriers", Risk (1991): no fetchable record (not in Crossref; web search exhausted); the chapter derives the closed forms from the reflection principle and does not attribute them.
- Intraday low of EUR/CHF on 15 January 2015 and losses of named firms: not verified; the chapter uses the ECB reference rates only.

# 13. The Rates Options Market — brief and source ledger

## Brief

- **Hook.** A broker reads out a column of numbers in basis points a day; they are volatilities, and nobody on the line uses a percentage.
- **Sections.** Caps and floors; Swaptions; Normal volatility; The volatility cube and who trades it.
- **Defines.** caplet, cap, floor, callable bond, swaption, payer swaption, receiver swaption, normal volatility, Bachelier model, volatility cube.
- **Uses (defined earlier).** implied volatility, annuity, par swap rate, negative convexity.
- **Tutorial.** Convert between normal and lognormal quotes and price a swaption straddle from a cube slice.
- **Build.** `firm.normalvol`: Bachelier pricer and quote converter.
- **Weekend problem.** The callable issuer — named result: the vega a bank acquires from swapping one callable issue, and the swaption it sells to lay it off.
- **Facts to verify.** market quoting in normal vol (bp/day, bp/year); negative rates made Black unusable (EUR 2015+); callable issuance and structural vega flows (public BIS/ECB).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ECB deposit facility rate: -0.10% from 11 Jun 2014, -0.20% from 10 Sep 2014, -0.30% from 9 Dec 2015, -0.40% from 16 Mar 2016, -0.50% from 18 Sep 2019, 0.00% from 27 Jul 2022 | ECB, Key ECB interest rates | https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html | 2026-09-23 | table rows "11 Jun. -0.10 ... 18 Sep. -0.50 ... 27 Jul. 0.00" | hook; fig |
| F2 | German 10-year government yield (monthly average) negative in 38 months between June 2016 and January 2022, lowest -0.65% in August 2019; Japanese 10-year negative in 24 months between February 2016 and April 2020, lowest -0.28% | OECD MEI via FRED IRLTLT01DEM156N, IRLTLT01JPM156N (data/markets-2/oecd_10y_monthly.csv, ledgered in ch. 7) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRLTLT01DEM156N | 2026-09-23 | computed from the file | hook; fig |
| F3 | In interest-rate derivatives normal (Bachelier) volatilities are the usual convention when forwards, strikes or rates can be near zero or negative; the convention has long been familiar in yen rates; bp vol is the normal vol in basis points per square-root year; in April 2020 CME Clearing switched its options pricing model to Bachelier when WTI futures traded below zero | F. Le Floc'h, "Explicit rational formulae for Bachelier (normal) implied volatility", arXiv 2605.18343 (2026), introduction | https://arxiv.org/html/2605.18343 | 2026-09-23 | "In interest-rate derivatives, normal or Bachelier volatilities are the usual convention when forwards, strikes, or rates can be close to zero or negative." | hook; §3 |
| F4 | Bachelier, "Théorie de la spéculation", Annales scientifiques de l'École Normale Supérieure, 3e série, tome 17 (1900), pp. 21-86 | Numdam | http://www.numdam.org/item/ASENS_1900_3_17__21_0/ | 2026-09-23 | bibliographic record | def Bachelier model |
| F5 | Taiwan, May 2014: lawmakers excluded locally issued foreign-currency bonds from the 45% cap on insurers' overseas investments; all dollar notes sold in Taiwan since then callable by the issuer, maturing in 20 or 30 years, 74% zero coupon; USD 7.3 billion issued in 2014 to September against zero a year earlier | Bloomberg, republished by Insurance Journal, 10 Sep 2014 | https://www.insurancejournal.com/news/international/2014/09/10/340062.htm | 2026-09-23 | "All of the dollar notes sold on the island since May's amendment are callable by the issuer and mature in 20 or 30 years" | §4 |
| F6 | OTC derivatives notional outstanding USD 846 trillion at end-June 2025 (+16% y/y), interest rate derivatives 79% of notional; gross market value USD 21.8 trillion | BIS, OTC derivatives statistics at end-June 2025, 8 Dec 2025 | https://www.bis.org/publ/otc_hy2512.htm | 2026-09-23 | "interest rate derivatives make up 79% of all OTC derivatives' notional amounts" | dat:m2:the-rates-options-market:size |

## EXCLUDED

- Brief hook (a broker reading vols in bp a day): a scene, not a checkable fact; replaced by the negative-rates hook (F1-F3).
- Interest-rate options notional by instrument (BIS table D5): not fetched; only the OTC total and IRD share are used.
- Formosa-bond hedging effects on the swaption expiry curve: only press and broker commentary found (Risk.net, bank strategists); not used. The mechanism is explained from first principles.


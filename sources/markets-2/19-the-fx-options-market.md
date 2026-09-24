# 19. The FX Options Market — brief and source ledger

## Brief

- **Hook.** Asked for the twenty-five delta risk reversal, the broker answers 1.2 puts over; a new trader writes it down without knowing which side pays.
- **Sections.** Delta and at-the-money conventions; Risk reversals, butterflies and the smile; Premium currency and premium-adjusted delta; Broker markets and barrier-driven flows.
- **Defines.** spot delta, forward delta, premium-adjusted delta, delta-neutral straddle, risk reversal, strangle, butterfly, barrier option, knock-out option, knock-in option.
- **Uses (defined earlier).** implied volatility, volatility skew, at-the-money, delta hedging, option cut, forward points.
- **Tutorial.** Recover the 25-delta call and put strikes and vols from ATM, RR and BF quotes with each delta convention.
- **Build.** `firm.fxsmile`: quote-to-smile converter.
- **Weekend problem.** The barrier defence — named result: the notional of spot the option desk must trade at the barrier.
- **Facts to verify.** market conventions (Clark / Wystup) for delta and ATM; OTC FX options turnover (Triennial); USDJPY or EURCHF barrier episodes (public).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | FX delta conventions: spot delta (hedge in spot) and forward delta (hedge in forwards); standard delta in percent of the foreign (base) notional; premium-adjusted delta when the premium is paid in the foreign currency (example: 60% delta and a premium of 73,669 EUR per 1,000,000 EUR gives 52.63%); OECD-only pairs use spot deltas up to and including 1Y, forward deltas beyond; forward deltas for pairs with an emerging-market currency; premium-adjusted delta default when the premium currency is the foreign one; examples (from Clark): EURUSD USD premium regular; USDJPY USD premium premium-adjusted; EURJPY, EURCHF, EURGBP EUR premium premium-adjusted; GBPUSD, AUDUSD regular; USDCAD, USDCHF, USDBRL, USDMXN premium-adjusted | Reiswich and Wystup, "FX Volatility Smile Construction", CPQF Working Paper 20, Frankfurt School (2010), sections 1.3 and Table 2 | https://www.econstor.eu/bitstream/10419/40186/1/613825101.pdf | 2026-09-23 | "We call this type of delta the premium-adjusted delta." | §1; §3; def |
| F2 | ATM definitions: ATM-spot, ATM-forward, ATM-value-neutral (= ATM-forward by put-call parity), ATM-delta-neutral (call delta = - put delta), the last the default for short-dated FX options; FX markets quote ATM, 25-delta risk reversal and strangle volatilities, not smiles | same, section 1.4 and 2 | https://www.econstor.eu/bitstream/10419/40186/1/613825101.pdf | 2026-09-23 | "This ATM convention is considered as the default ATM notion for short-dated FX options." | §1-2 |
| F3 | Simplified formula: sigma25C = sigmaATM + RR/2 + smile strangle, sigma25P = sigmaATM - RR/2 + smile strangle, so sigma25C - sigma25P = RR; the quoted (market) strangle is a different quantity and the simplified formula is only an approximation of the market's construction | same, section 3 (equations 28-30) | https://www.econstor.eu/bitstream/10419/40186/1/613825101.pdf | 2026-09-23 | "Very often, a simplified formula is stated in the literature which allows an easy calculation of the 0.25 delta volatilities given the market quotes." | §2; build |
| F4 | FX options turnover more than doubled from 2022 to 2025, 7% of global FX turnover in April 2025 (4% in 2022) | BIS Triennial Survey 2025 (ch. 14, F1) | https://www.bis.org/statistics/rpfx25_fx.htm | 2026-09-23 | "Average daily turnover of FX options more than doubled from 2022 to 2025, accounting for 7% of global turnover" | hook; dat:m2:the-fx-options-market:size |

## EXCLUDED

- Specific barrier-defence episodes (USDJPY, EURCHF): only press and market commentary; not used. The mechanism is shown on an illustrative trade.
- Broker jargon such as "1.2 puts over": explained as a convention without a source-dependent claim.


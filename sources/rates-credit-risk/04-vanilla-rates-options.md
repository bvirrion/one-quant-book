# 4. Vanilla Rates Options — brief and source ledger

## Brief

- **Hook.** In 2014 euro rates went below zero and the broker screens that had quoted caps and swaptions in lognormal volatility for twenty years began printing blanks.
- **Sections.** Black and Bachelier for rates; Caps, floors and caplet stripping; Swaptions: physical and cash settlement; Vega, the smile at a glance, and the choice of model.
- **Defines.** lognormal volatility, flat volatility, caplet volatility, caplet stripping, cash-settled swaption, cash annuity.
- **Uses (defined earlier).** caplet (B2.13), cap (B2.13), floor (B2.13), swaption (B2.13), payer swaption (B2.13), receiver swaption (B2.13), Bachelier model (B2.13), normal volatility (B2.13), volatility cube (B2.13), annuity (B2.9), implied volatility (B1.25), Black model (B5.3), vega (B5.4), forward measure (B4.5), annuity measure (B4.5), projection curve (ch2), discount curve (ch2).
- **Tutorial.** Strip caplet volatilities from a ladder of flat cap volatilities; price swaptions under Black and Bachelier; compare a cash-settled swaption on the cash annuity with its physical twin.
- **Build.** `firm.capfloor`: cap, floor and swaption pricer on the multi-curve, flat-to-caplet stripping, cash annuity; reuses `firm.normalvol`.
- **Weekend problem.** The treasurer's cap — named result: the premium, vega and break-even rate of a five-year cap bought to protect a floating-rate loan.
- **Facts to verify.** ECB deposit facility rate negative from June 2014 to July 2022 (ECB); the move of rates-option quoting to normal volatility (public); ISDA collateralised cash price settlement for EUR swaptions (2018); rates options market size (BIS OTC statistics, dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | ECB deposit facility rate: -0.10% from 11 June 2014, -0.20% 10 Sep 2014, -0.30% 9 Dec 2015, -0.40% 16 Mar 2016, -0.50% 18 Sep 2019, 0.00% from 27 July 2022 | ECB, Key ECB interest rates | https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html | 2026-09-24 | table of deposit facility rate changes | dat:rc:vanilla-rates-options:negative, hook |
| F2 | The default cash-settlement method for EUR swaptions in the ISDA Settlement Matrix changed from "Par Yield Curve - Unadjusted" to "Collateralized Cash Price" effective 26 November 2018 (Supplement 58 to the 2006 ISDA Definitions, 21 November 2018, links the discount factors to those of a mutually agreed clearing house) | ISDA, "Market Practice Change for Settlement of EUR Swaptions to Collateralized Cash Price", 26 Nov 2018 | https://www.isda.org/2018/11/26/market-practice-change-for-settlement-of-eur-swaptions-to-collateralized-cash-price/ | 2026-09-24 | "Collateralized Cash Price" replaced the prior "Par Yield Curve - Unadjusted"; effective "November 26, 2018" | dat:rc:vanilla-rates-options:negative, sec. 4.3 |
| F3 | With negative rates, Black volatilities cannot represent options with negative strikes or forwards; the market started to quote caps, floors and swaptions also in normal (Bachelier) or shifted Black volatilities | MathWorks, "Work with Negative Interest Rates Using Functions" (secondary, vendor documentation) | https://www.mathworks.com/help/fininst/work-with-negative-interest-rates-using-functions.html | 2026-09-24 | "the market started to quote cap, floor, and swaption prices also in terms of either Normal volatilities or Shifted Black volatilities" | hook, dat:rc:vanilla-rates-options:negative |

## EXCLUDED

- Cap and swaption volatilities of the chapter are illustrative (normal volatilities); the euro curves are chapter 2's illustrative curves. Re-checked 2026-09-24: illustrative by design.
- Rates-options market size (BIS): not needed after the outline brief; the chapter states no market-size figure. Re-checked 2026-09-24: not needed (no claim in the text).


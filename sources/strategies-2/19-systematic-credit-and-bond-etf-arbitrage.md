# 19. Systematic Credit and Bond-ETF Arbitrage — brief and source ledger

## Brief

- **Hook.** A bond ETF trades every second while most of its bonds do not trade for days; when they disagree, authorised participants create or redeem shares, and the discount says how illiquid the bonds really are.
- **Sections.** Factors in credit; Bond ETFs and create-redeem; Portfolio trades; Discounts in stress.
- **Defines.** credit factor, ETF create-redeem arbitrage, ETF discount.
- **Uses (defined earlier).** creation basket (B1.14), creation unit (B1.14), authorised participant (B1.14), portfolio trade (B2.22), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** credit value and momentum; low-risk credit; ETF premium-discount arbitrage; portfolio-trade liquidity provision.
- **Tutorial.** Simulate a bond universe with factor structure and stale prices, a bond ETF with authorised participants, and a stress in which the ETF's discount widens; trade credit factors and the ETF arbitrage.
- **Build.** `firm.syscredit`: credit factor signals on a synthetic bond panel, ETF net asset value with stale prices, create-redeem arbitrage and portfolio-trade pricing; Python.
- **Weekend problem.** Which price is right — named result: the credit factors' Sharpe ratios and the ETF arbitrage's return in the planted stress.
- **Facts to verify.** Houweling and van Zundert 2017 factor investing in the corporate bond market (FAJ); Haddad, Moreira, Muir 2021 when selling becomes viral (RFS); Pan and Zeng 2019 or Koont, Ma, Pastor, Zeng on bond ETF arbitrage.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | P. Houweling, J. van Zundert, "Factor investing in the corporate bond market", Financial Analysts Journal 73(2) (2017) 100-115: size, low-risk, value and momentum factor portfolios generate economically meaningful and statistically significant alphas in corporate bonds; low correlations between single-factor portfolios make a combined portfolio more efficient; robust to transaction costs and to liquid-bond subsamples; adds value beyond equity factors | Crossref metadata; OpenAlex abstract | https://doi.org/10.2469/faj.v73.n2.1 | 2026-09-25 | abstract: "size, low-risk, value, and momentum factor portfolios generate economically meaningful and statistically significant alphas in the corporate bond market" | hook; section 1; strat:s2:systematic-credit-and-bond-etf-arbitrage:factors; strat:s2:systematic-credit-and-bond-etf-arbitrage:lowrisk; solutions; omsources |
| F2 | V. Haddad, A. Moreira, T. Muir, "When selling becomes viral: disruptions in debt markets in the COVID-19 crisis and the Fed's response" (NBER WP 27168, 2020): corporate bonds traded at a large discount to their CDS, the basis widening most for safer bonds; liquid bond ETFs traded at a large discount to NAV, more for Treasuries, municipal bonds and investment-grade corporates than high yield; investors sold safer, more liquid securities to raise cash; the disruptions reversed after the Fed's announcements to buy corporate bonds on 23 March and 9 April 2020 | NBER abstract page | https://www.nber.org/papers/w27168 | 2026-09-25 | "Liquid bond ETFs traded at a large discount to their NAV, more so for Treasuries, municipal bonds, and investment-grade corporate than high-yield corporate" | hook; section 4; strat:s2:systematic-credit-and-bond-etf-arbitrage:etf; exercise 5; solutions; omsources |
| F3 | N. Koont, Y. Ma, L. Pastor, Y. Zeng, "Steering a ship in illiquid waters: active management of passive funds" (NBER WP 30039, 2022): corporate bond ETFs manage their portfolios actively, trading off index tracking against liquidity transformation; they choose creation and redemption baskets with cash and a subset of index bonds, adjust baskets to correct imbalances while facilitating arbitrage; basket inclusion improves bond liquidity in general but worsens it in large creation-redemption imbalances such as the COVID-19 crisis | NBER abstract page | https://www.nber.org/papers/w30039 | 2026-09-25 | "ETFs optimally choose creation and redemption baskets that include cash and only a subset of index assets, especially if those assets are illiquid" | section 2; strat:s2:systematic-credit-and-bond-etf-arbitrage:etf; exercise 6; solutions; omsources |

## EXCLUDED

- Measured ETF discounts in March 2020 (sizes for named funds): not in the fetched abstracts; the chapter's stress is planted.
- Pan and Zeng 2019 on bond ETF arbitrage: not fetched; Koont, Ma, Pastor and Zeng cover the basket mechanism.
- Portfolio-trade pricing data: none; the strategy file states the mechanism only.


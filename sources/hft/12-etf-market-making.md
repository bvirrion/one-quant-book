# 12. ETF Market Making — brief and source ledger

## Brief

- **Hook.** An ETF on emerging-market bonds trades all day in New York while half of its bonds have not traded for a week; the market maker who quotes it is the price, and on a bad day its quote and the fund's net asset value can be several percent apart.
- **Sections.** Pricing an ETF from its basket; The primary market: creation and redemption; Hedging an ETF book; When the underlying is closed or illiquid; Stress: discounts, stale NAVs and who absorbs them.
- **Defines.** pricing basket, custom basket, creation fee.
- **Uses (defined earlier).** exchange-traded fund (B1.14), authorised participant (B1.14), creation unit (B1.14), creation basket (B1.14), indicative NAV (B1.14), net asset value (B1.14), ETF create-redeem arbitrage (B9.19), ETF discount (B9.19), fair price (ch2), market maker (B1.1), bid--ask spread (B1.1), adverse selection (B1.1), mid price (B1.1), inventory (B2.30).
- **Strategy files.** basket-hedged equity ETF quoting; creation-redemption arbitrage; fixed-income ETF quoting on a stale NAV; international ETF quoting while the underlying is closed; futures-hedged ETF quoting.
- **Tutorial.** Price a synthetic ETF from a pricing basket with stale components, quote it with firm.mmharness hedged in the basket or in a future, and run the create-redeem decision at the close; stress with a planted bond-market freeze.
- **Build.** `firm.etfmm`: pricing-basket fair price with staleness and futures proxies, hedge choice, creation-redemption decision with fees and settlement lag; Python, on firm.etfmonitor.
- **Weekend problem.** Quoting a closed market — named result: the ETF market maker's P&L and the premium it quotes through the planted freeze, and how much of the discount was the NAV's staleness.
- **Facts to verify.** SEC Rule 6c-11 (2019) custom baskets and ETF disclosure (dated); Flow Traders annual report: ETF value traded (dated); Petajisto 2017 Inefficiencies in the pricing of exchange-traded funds (FAJ); Pan and Zeng 2019 or Koont et al. on ETF arbitrage under liquidity mismatch; Haddad, Moreira, Muir 2021 When selling becomes viral (RFS): March 2020 bond ETF discounts.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Petajisto (2017): ETF price deviations from NAV typically within a band of about 200 bp, larger for international or illiquid holdings; controlling for stale prices with similar ETFs, the average band is still about 100 bp | A. Petajisto, "Inefficiencies in the pricing of exchange-traded funds", Financial Analysts Journal 73(1), 2017, 24-54 | https://ideas.repec.org/a/taf/ufajxx/v73y2017i1p24-54.html | 2026-09-25 | abstract: "The deviations, typically within a band of about 200 bps, are larger in funds holding international or illiquid securities... The average pricing band remains economically significant at about 100 bps" | §1; strategy files |
| F2 | iShares Trust SAI dated 31 July 2020 (as revised 27 November 2020): iShares Core S&P 500 ETF 50,000 shares per creation unit, approx. value $14,579,000 on 30 April 2020; standard creation transaction fee $1,250, maximum additional charge for creations 3.0%; standard redemption fee $1,250, maximum additional charge 2.0%; iShares Europe ETF standard fee $10,000 | SEC EDGAR, Form 497, iShares Trust (CIK 1100663) | https://www.sec.gov/Archives/edgar/data/1100663/000119312520304520/d47555d497.htm | 2026-09-25 | "Fund Shares Per Creation Unit Approximate Value Per Creation Unit (U.S.$) iShares Core S&P 500 ETF 50,000 $ 14,579,000"; "iShares Core S&P 500 ETF $ 1,250 3.0%"; redemption table "iShares Core S&P 500 ETF $ 1,250 2.0%"; "iShares Europe ETF 10,000" | dat:hf:etf-market-making:fees |
| F3 | SEC Rule 6c-11 (press release 2019-190, 26 September 2019): custom baskets permitted with written policies and procedures; daily portfolio transparency on the website; UITs, leveraged/inverse, share-class and non-transparent ETFs cannot rely on the rule | SEC press release 2019-190 | https://www.sec.gov/newsroom/press-releases/2019-190 | 2026-09-25 | "permitted to use baskets that do not reflect a pro-rata representation of the fund's portfolio or that differ from the initial basket used in transactions on the same business day ('custom baskets') if the ETF adopts written policies and procedures"; "required to provide daily portfolio transparency on its website" | dat:hf:etf-market-making:fees |
| F4 | Flow Traders FY2025 ETP value traded EUR 1,940bn | Flow Traders, "4Q and FY 2025 Results", 12 February 2026 | https://flowtraders.com/media/mdbmvriu/flow-traders-4q-fy-2025-results.pdf | 2026-09-25 | "Full year Flow Traders' ETP Value Traded increased by 26% year-on-year to €1,940b" (as in chapter 1, F4) | dat:hf:etf-market-making:fees |

## EXCLUDED

- Haddad, Moreira and Muir (2021) and Koont, Ma, Pastor and Zeng: already in One Quant Book 9, chapter 19; referred to by pointer, not restated.
- Pan and Zeng (2019): not fetched.

# 20. Mortgage and Structured-Credit Strategies — brief and source ledger

## Brief

- **Hook.** A mortgage holder can repay whenever rates fall, so a mortgage bond is short an option the borrower may not use well; traders who model borrowers better than the market are paid for it.
- **Sections.** Prepayment views; Interest-only and principal-only trades; Tranche relative value.
- **Defines.** prepayment trade, tranche relative value.
- **Uses (defined earlier).** prepayment (B2.12), conditional prepayment rate (B2.12), prepayment model (B6.12), interest-only strip (B6.12), tranche (B2.24), option-adjusted spread (B2.21), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** IO long on slow prepayment view; OAS relative value across coupons; mezzanine tranche relative value.
- **Tutorial.** Simulate a mortgage pool with a planted borrower behaviour that differs from the market's prepayment model, value IO, PO and pass-throughs under both, and trade the difference.
- **Build.** `firm.mbsrv`: prepayment-view trades on firm.prepay and firm.mbsoas, IO/PO valuation and tranche relative value; Python.
- **Weekend problem.** Better than the market's model — named result: the IO trade's return when the view is right and when the burnout assumption is wrong.
- **Facts to verify.** Gabaix, Krishnamurthy, Vigneron 2007 limits of arbitrage: theory and evidence from the mortgage-backed securities market (JF); Boyarchenko, Fuster, Lucca 2019 understanding mortgage spreads (RFS).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | X. Gabaix, A. Krishnamurthy, O. Vigneron, "Limits of arbitrage: theory and evidence from the mortgage-backed securities market", Journal of Finance 62(2) (2007) 557-595: homeowner prepayment risk, a wash in the aggregate, is priced in the MBS market; its covariance with aggregate wealth has the wrong sign to explain the prices; the price of risk is better explained by a kernel based on MBS market-wide risk, consistent with specialised arbitrageurs as marginal investors | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/j.1540-6261.2007.01217.x | 2026-09-25 | abstract: "We show that the risk of homeowner prepayment, which is a wash in the aggregate, is priced in the MBS market" | hook; section 1; strat:s2:mortgage-and-structured-credit-strategies:io; exercise 5; solutions; omsources |
| F2 | N. Boyarchenko, A. Fuster, D. O. Lucca, "Understanding mortgage spreads", Review of Financial Studies 32(10) (2019) 3799-3850: MBS spreads show a pronounced cross-sectional smile in coupon; a pricing model using stripped MBS prices attributes the smile to non-interest-rate prepayment risk, while time-series spread variation is mostly non-prepayment risk factors | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhz004 | 2026-09-25 | abstract: "MBS spreads show a pronounced cross-sectional smile with respect to the securities' coupon rates" | section 2; strat:s2:mortgage-and-structured-credit-strategies:oas; solutions; omsources |
| F3 | J. Coval, J. Jurek, E. Stafford, "The economics of structured finance", Journal of Economic Perspectives 23(1) (2009) 3-25: pooling and tranching makes many tranches far safer than the average pool asset; two features explain the rise and fall of structured finance: the extreme fragility of ratings to modest imprecision in evaluating underlying risks, and exposure to systematic risk; and J. Coval, J. Jurek, E. Stafford, "Economic catastrophe bonds", American Economic Review 99(3) (2009) 628-666: many structured finance instruments resemble bonds that default only in severe economic states but offer far less compensation than alternatives with comparable payoffs | Crossref metadata; OpenAlex abstracts | https://doi.org/10.1257/jep.23.1.3 ; https://doi.org/10.1257/aer.99.3.628 | 2026-09-25 | JEP abstract: "the extreme fragility of their ratings to modest imprecision in evaluating underlying risks, and their exposure to systematic risks"; AER abstract: "offer far less compensation than alternatives with comparable payoff profiles" | section 3; strat:s2:mortgage-and-structured-credit-strategies:mezz; exercise 6; solutions; omsources |

## EXCLUDED

- Real prepayment speeds, OAS or tranche prices by coupon or series: none fetched (agency and dealer data are licensed); the chapter's markets are synthetic, and the planted beliefs (the market's burnout 0.25 against the view's 1.0; a market correlation of 0.30) are the chapter's own choices.
- Freddie Mac PMMS mortgage rates: terms of reuse not verified; not used.
- Named firms' mortgage or tranche trades (for example 2007-08 structured-credit shorts): no citable primary source fetched; no firm named.

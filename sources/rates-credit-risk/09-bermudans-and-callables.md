# 9. Bermudans and Callables — brief and source ledger

## Brief

- **Hook.** A Taiwanese life insurer buys a thirty-year zero-coupon bond the issuer may call every year; the issuing bank's hedge of that call is part of why long-dated dollar volatility falls when such issuance is heavy.
- **Sections.** Bermudan swaptions and their co-terminal Europeans; Exercise by backward induction on a tree; Exercise by regression in Monte Carlo; Upper bounds and the switch option; The callable-bond issuance business.
- **Defines.** Bermudan swaption, co-terminal swaption, switch option, Formosa bond, callable range accrual.
- **Uses (defined earlier).** callable bond (B2.13), swaption (B2.13), option-adjusted spread (B2.21), exercise boundary (B5.6), Bermudan exercise (B5.6), Longstaff--Schwartz method (B5.23), dual upper bound (B5.23), trinomial tree (B5.22), Hull--White model (ch7), LIBOR market model (ch8).
- **Tutorial.** Price a ten-year-non-call-one Bermudan receiver on the Hull--White tree and by least-squares regression on the same model; compare with the most expensive co-terminal European and bound it from above.
- **Build.** `firm.bermudan`: tree and regression pricers for Bermudan swaptions and callable bonds on `firm.shortrate`.
- **Weekend problem.** The Formosa hedge — named result: the Bermudan premium over the most expensive European and the vega the issuing bank's hedge sells into the market.
- **Facts to verify.** Formosa bond market size and history (TPEx/BIS); BIS or central-bank analysis of callable issuance and long-dated volatility; Longstaff and Schwartz 2001; Andersen and Broadie 2004 (papers).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | In May 2014 Taiwan's lawmakers excluded locally issued foreign-currency bonds from the 45% cap on insurers' overseas investments, unlocking USD 586 billion of insurers' funds; all dollar notes sold since were callable by the issuer with 20- or 30-year maturities and 74% paid zero coupon (Bloomberg data) | Insurance Journal (Bloomberg News), "Goldman Leads Wall Street Tapping Taiwan Cash Pile", 10 September 2014 (secondary, press) | https://www.insurancejournal.com/news/international/2014/09/10/340062.htm | 2026-09-24 | "lawmakers in May excluded locally issued foreign-currency bonds from a 45 percent cap"; "unlocked $586 billion"; "callable by the issuer and mature in 20 or 30 years, while 74 percent pay zero coupon" | dat:rc:bermudans-and-callables:formosa, def:rc:bermudans-and-callables:formosa |
| F2 | Risk.net reported that the callable bonds bought by Taiwan's life insurers help supply the US swaptions market, holding down US rates volatility | Risk.net, "Formosas, the Fed, and the billion-dollar Bermudan trade" (paywalled; the claim is from the article's public summary as returned by search) | https://www.risk.net/derivatives/5287696/formosas-the-fed-and-the-billion-dollar-bermudan-trade | 2026-09-24 | summary: "callable bonds ... are helping power the US swaptions market, holding down US rates volatility" | sec. 9.5, dat:rc:bermudans-and-callables:formosa |
| F3 | Longstaff and Schwartz (2001): least squares estimates the continuation value in simulation, illustrated on an American swaption in a multi-factor term-structure model | F. Longstaff and E. Schwartz, "Valuing American options by simulation: a simple least-squares approach", Review of Financial Studies 14(1), 113-147, 2001 | https://academic.oup.com/rfs/article-abstract/14/1/113/1587472 | 2026-09-24 | abstract | sec. 9.3, omsources |

## EXCLUDED

- Formosa market size today (TPEx statistics) and the estimated profit figure in the Risk.net article: not used. Andersen-Broadie duality: attributed in prose only, as Book 5's term (dual upper bound). Curves and volatilities are the book's illustrative ones. Re-checked 2026-09-24: not needed (no claim in the text).


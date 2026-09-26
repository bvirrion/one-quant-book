# 22. Portfolio Trades and Risk Bids — brief and source ledger

## Brief

- **Hook.** A pension fund asks three brokers for a price at which they will take on a basket of five hundred stocks at tonight's close, knowing only its size, its sectors and its liquidity. The broker who wins learns the names afterwards, and learns whether it bid too much.
- **Sections.** Agency and principal portfolio trades; The cost of liquidating a basket; Pricing a risk bid; Blind bids and the winner's curse; Transitions.
- **Defines.** agency portfolio trade, risk bid, blind risk bid, basket liquidity profile.
- **Uses (defined earlier).** portfolio trade (B2.22), transition management (B8.29), central risk book (B9.25), risk pooling (B9.25), internal crossing (B7.27), principal (B1.1), winner's curse (B2.30), factor model (B4.22), Almgren--Chriss model (ch14), cross-impact matrix (ch13), square-root impact law (B7.27), closing price (B1.13).
- **Tutorial.** Price a risk bid on a synthetic basket: its expected liquidation cost (multi-asset Almgren-Chriss with cross-impact and Book 7's firm.riskmodel), the price of the risk carried, and the winner's-curse adjustment against competing brokers; compare a disclosed and a blind bid. Data: simulated (firm.synthmkt names).
- **Build.** `firm.riskbid`: basket liquidity profile, multi-asset liquidation cost and risk, bid pricing with competition and information (winner's curse), a transition plan with internal crossing; Python.
- **Weekend problem.** Pricing the basket blind -- named result: the bid in basis points for the disclosed and the blind basket, and the winner's-curse adjustment against three competitors.
- **Facts to verify.** Kavajecz and Keim 2005 packaging liquidity: blind auctions and transaction efficiencies (JFQA); Almgren and Chriss 2000 (multi-asset section); public descriptions of principal portfolio trading in equities or bonds (dated, only if citable); Bernstein / other transition-management references only if citable.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | K. A. Kavajecz and D. B. Keim, "Packaging liquidity: blind auctions and transaction efficiencies", Journal of Financial and Quantitative Analysis 40(3) (2005) 465-492: blind package auctions give the liquidity demander a transaction-cost saving relative to more traditional mechanisms and liquidity suppliers an efficient way to obtain order flow | Crossref record with abstract | https://doi.org/10.1017/S0022109000001836 | 2026-09-26 | "A critical feature of the auction is that the identities of the securities in the package are not revealed to the bidder. We demonstrate that this mechanism provides a transactions cost savings relative to more traditional trading mechanisms for the liquidity demander as well as an efficient way for liquidity suppliers to obtain order flow." | §1, omsources |
| F2 | R. Almgren and N. Chriss, "Optimal execution of portfolio transactions", Journal of Risk 3(2) (2001) 5-39 (multi-asset section) | Crossref record | https://doi.org/10.21314/jor.2001.041 | 2026-09-25 | bibliographic record (see chapter 14, F1) | §3, omsources |

## EXCLUDED

- Public descriptions of principal portfolio trading and transition-management references (brief, "only if citable"): none used; no firm is named.
- Cross-impact between the basket's names (chapter 13's firm.crossimpact) is not in the pricing: the chapter prices own impact and covariance risk
  and lists cross-impact as the tutorial's next step.
- The half-spread rule (1 bp + 3e4 / sqrt(ADV in USD), in bp), the 20% participation cap, the one-standard-deviation risk charge, the 15% estimation
  error and the 2 bp margin are assumptions stated in the text.
- All numbers are computed by mx_riskbid and firm.riskbid and tested.


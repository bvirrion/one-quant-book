# 13. Supply Trades — brief and source ledger

## Brief

- **Hook.** Treasuries cheapen in the days before a large auction and recover after; dealers must absorb the supply, and they are paid for it.
- **Sections.** Auction concessions; New-issue and on-the-run premia; Corporate supply; Trading around the calendar.
- **Defines.** auction concession, on-the-run premium, supply trade.
- **Uses (defined earlier).** new-issue concession (B2.21), on-the-run (B2.4), when-issued trading (B2.4), auction tail (B2.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** pre-auction short, post-auction long; on-the-run roll; corporate new-issue concession; month-end index extension.
- **Tutorial.** Simulate an auction calendar with planted concessions proportional to size and dealer inventory, and trade the pre- and post-auction pattern and the on-the-run roll.
- **Build.** `firm.supplytrade`: auction calendar, concession model, supply trades around auctions and on-the-run rolls; Python.
- **Weekend problem.** Paid to absorb — named result: the auction trade's return per auction and its dependence on auction size.
- **Facts to verify.** Lou, Yan, Zhang 2013 anticipated and repeated shocks in liquid markets (RFS); Fleming and Rosenberg 2008 how do Treasury dealers manage their positions? (FRBNY staff report); TreasuryDirect auction results (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. Lou, H. Yan, J. Zhang, "Anticipated and repeated shocks in liquid markets", Review of Financial Studies 26(8) (2013) 1891-1912: Treasury prices in the secondary market fall significantly in the few days before auctions and recover shortly after, although auction times and amounts are announced in advance; linked to dealers' limited risk-bearing capacity and end-investors' imperfect capital mobility; a hidden issuance cost to the Treasury estimated at 9 to 18 bp of the auction size, over half a billion dollars for 2007 issuance | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hht034 | 2026-09-25 | abstract: "Treasury security prices in the secondary market decrease significantly in the few days before Treasury auctions and recover shortly thereafter"; "estimated to be 9 to 18 bps of the auction size" | hook; section 1; strat:s2:supply-trades:auction; omsources |
| F2 | M. Fleming, G. Nguyen, J. Rosenberg, "How do Treasury dealers manage their positions?", Federal Reserve Bank of New York Staff Report 299 (August 2007, revised March 2024): with 1990-2020 dealer position data, issuance is the main driver of dealers' weekly inventory changes, only partly offset in adjacent weeks and not significantly hedged with futures; dealers are compensated for inventory risk by subsequent price appreciation; with higher post-crisis balance-sheet costs dealers take smaller positions and lay off inventory faster; more investment-fund participation in auctions has reduced the compensation | NY Fed staff report PDF (pdftotext) | https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr299.pdf | 2026-09-25 | abstract: "Treasury issuance is the main driver of dealers' weekly inventory changes"; "Dealers are compensated for inventory risk by means of subsequent price appreciation of their holdings"; "the increased participation of non-dealers (investment funds) in the primary market contributes to diminishing compensation" | section 1; section 4; omsources |
| F3 | TreasuryDirect auction query service (notes and bonds auctioned 2010-2026: auction date, term, offering amount) and FRED constant-maturity yields DGS2, DGS5, DGS7, DGS10, DGS30, used only through derived statistics | TreasuryDirect TA_WS securities search; FRED | https://www.treasurydirect.gov/TA_WS/securities/search?format=json&securityType=Note ; https://fred.stlouisfed.org/series/DGS10 | 2026-09-25 | queried; statistics recomputed by s2_fetch_auctions.py | section 1 |

## EXCLUDED

- On-the-run premium sizes and corporate new-issue concession magnitudes: no source fetched; strategy files state no figure.
- Index extension at month-end (duration of index changes): mechanism stated without a number.
- End-of-day H.15 yields around an auction held at 1 p.m. mix pre- and post-auction prices on the auction day: stated in the chapter as a limitation.


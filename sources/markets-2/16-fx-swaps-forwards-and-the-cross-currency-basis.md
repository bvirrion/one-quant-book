# 16. FX Swaps, Forwards and the Cross-Currency Basis — brief and source ledger

## Brief

- **Hook.** A Japanese insurer buys US Treasuries and hedges the dollars back to yen; the hedge costs more than the extra yield.
- **Sections.** Outright forwards and forward points; FX swaps and short-dated rolls; Covered interest parity; The cross-currency basis; Dollar funding stress.
- **Defines.** outright forward, forward points, FX swap, tom-next, covered interest parity, cross-currency basis swap, cross-currency basis.
- **Uses (defined earlier).** currency pair, spot value date, interest-rate swap, overnight benchmark rate.
- **Tutorial.** Compute forward points from two curves, then back out the implied basis from market points.
- **Build.** `firm.fxfwd`: forward-points and basis calculator.
- **Weekend problem.** The hedged yield — named result: the currency-hedged yield of a ten-year Treasury for a yen investor.
- **Facts to verify.** BIS on CIP deviations post-2008 (Borio et al.); FX swaps as most traded instrument (Triennial); Fed central-bank swap lines (2008, 2020); quarter-end basis spikes.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CIP "is the closest thing to a physical law in international finance" yet systematically violated since the GFC; since 2007 the basis for lending USD against most currencies, notably EUR and JPY, negative (borrowing USD via FX swaps dearer than in the cash market), positive for some such as AUD; post-2014 violations explained by hedging demand plus limits to arbitrage (risk management, bank balance-sheet constraints); since 2014 quarter-end spikes with repo rates, with greater importance of quarter-end reporting after regulatory reforms; in a cross-currency basis swap notionals are exchanged back at the initial spot and floating payments exchanged, with the basis b on one leg; FX swap quoted in forward points F-S | Borio, McCauley, McGuire and Sushko, "Covered interest parity lost: understanding the cross-currency basis", BIS Quarterly Review, September 2016 | https://www.bis.org/publ/qtrpdf/r_qt1609e.htm | 2026-09-23 | "Since 2007, the basis for lending US dollars against most currencies, notably the euro and yen, has been negative" | §3-5; def |
| F2 | FX swaps are the most traded FX instrument, USD 4 trillion a day in April 2025, 42% of turnover, mostly up to seven days, used to manage funding liquidity and hedge | BIS Triennial Survey 2025 (ch. 14, F1) | https://www.bis.org/statistics/rpfx25_fx.htm | 2026-09-23 | "FX swaps remained the most traded instrument, with average daily turnover rising to $4 trillion" | §2 |
| F3 | Fed swap lines: 12 Dec 2007 with the ECB (up to USD 20bn) and SNB (USD 4bn); 13 Oct 2008 lines with the BoE, ECB and SNB increased to accommodate whatever quantity of dollar funding is demanded | Federal Reserve press releases 12 Dec 2007 and 13 Oct 2008 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20081013a.htm | 2026-09-23 | "increased to accommodate whatever quantity of U.S. dollar funding is demanded" | §5 |
| F4 | 15 Mar 2020: BoC, BoE, BoJ, ECB, Fed, SNB lower standing swap-line pricing by 25 bp to USD OIS + 25 bp and add 84-day operations; 19 Mar 2020: temporary lines with nine more central banks (USD 60bn each: Australia, Brazil, Korea, Mexico, Singapore, Sweden; USD 30bn: Denmark, Norway, New Zealand) for at least six months | Federal Reserve press releases 15 and 19 Mar 2020 | https://www.federalreserve.gov/newsevents/pressreleases/monetary20200319b.htm | 2026-09-23 | "the U.S. dollar overnight index swap (OIS) rate plus 25 basis points" | §5 |
| F5 | Central bank liquidity swaps on the Fed balance sheet: peak USD 583.1bn on 17 Dec 2008, USD 448.9bn on 27 May 2020; USD 45 million on 18 Mar 2020 and USD 206.1bn on 25 Mar 2020 | FRED SWPT (H.4.1), data/markets-2/fed_swaplines_monthly.csv | https://fred.stlouisfed.org/graph/fredgraph.csv?id=SWPT | 2026-09-23 | downloaded series | fig; §5 |
| F6 | Hedged-yield inputs: 10-year Treasury 4.75% (31 Aug 2026), SOFR 3.68% (31 Aug 2026), Japanese call-money rate 0.977% (Aug 2026 average), 10-year JGB 2.94% (Aug 2026 average); USDJPY 156.87 (H.10, 18 Sep 2026) | FRED DGS10, SOFR, IRSTCI01JPM156N, IRLTLT01JPM156N; Federal Reserve H.10 | https://fred.stlouisfed.org/graph/fredgraph.csv?id=IRSTCI01JPM156N | 2026-09-23 | data/markets-2/hedged_ust_jpy.csv | hook; ex; problem; fig; dat:m2:fx-swaps-forwards-and-the-cross-currency-basis:inputs |

## EXCLUDED

- Current levels of the USDJPY and EURUSD cross-currency basis: no free official series found; the text uses illustrative levels (0, -25, -50 bp) and says so.
- Market convention of forward-point quoting per pair and exact day counts per currency: only the ACT/360 USD and ACT/365 JPY money-market conventions are used, as assumptions stated in the build.


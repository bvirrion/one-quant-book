# Rates and FX: ledger

Every level is invented for the arithmetic. Mathematics (bootstrapping, Vasicek, Ho-Lee, Hull-White, Jamshidian, Garman-Kohlhagen, Margrabe-style change of numeraire, vanna-volga) is named as mathematics and tested.

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | USD SOFR fixed-float OIS: annual payments on both legs, actual/360; floating leg pays compounded SOFR in arrears with a payment delay of two US Government Securities business days; legs start accruing two business days after trade (T+2 spot) | Clarus Financial Technology, "SOFR Swap Nuances" (secondary; market-data vendor) (row reused from markets-2) | https://www.clarusft.com/sofr-swap-nuances/ | 2026-09-23 | search excerpt: "trades with annual payments on each side, calculated using an Act/360 DCC" | Q34 dated box |
| F2 | CIP "is the closest thing to a physical law in international finance" yet systematically violated since the GFC; since 2007 the basis for lending USD against most currencies, notably EUR and JPY, negative (borrowing USD via FX swaps dearer than in the cash market), positive for some such as AUD; post-2014 violations explained by hedging demand plus limits to arbitrage (risk management, bank balance-sheet constraints); since 2014 quarter-end spikes with repo rates, with greater importance of quarter-end reporting after regulatory reforms; in a cross-currency basis swap notionals are exchanged back at the initial spot and floating payments exchanged, with the basis b on one leg; FX swap quoted in forward points F-S | Borio, McCauley, McGuire and Sushko, "Covered interest parity lost: understanding the cross-currency basis", BIS Quarterly Review, September 2016 (row reused from markets-2) | https://www.bis.org/publ/qtrpdf/r_qt1609e.htm | 2026-09-23 | "Since 2007, the basis for lending US dollars against most currencies, notably the euro and yen, has been negative" | Q29 |

## Unverified

That forwards are poor forecasts of spot (Q9), that basis trades have blown out when financing tightened (Q47), and that pairs with foreign premium use the premium-adjusted delta (Q44) are commonplaces, stated as such; no source read in this chapter. The one-third accrual rule (Q34) is checked only as the variance of a Brownian average.

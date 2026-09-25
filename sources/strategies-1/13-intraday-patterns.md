# 13. Intraday Patterns — brief and source ledger

## Brief

- **Hook.** Since 1993 most of the US market's return has come overnight: from the close to the open, while the exchanges are closed.
- **Sections.** Overnight versus intraday returns; The volume smile and the auctions; End-of-day hedging flows; Close imbalances.
- **Defines.** overnight return, intraday return, volume smile, end-of-day hedging flow.
- **Uses (defined earlier).** call auction (B1.13), order imbalance (B1.13), closing price (B1.13), gamma (B1.26), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** overnight drift; last-half-hour momentum; close imbalance reversal; hedging-flow timing; open-auction reversal.
- **Tutorial.** Measure overnight and intraday returns in firm.tape sessions and in derived statistics of public index data, simulate end-of-day hedging flow from a short-gamma dealer book and its footprint on the last half hour.
- **Build.** `firm.intraday`: intraday return decomposition, volume curves, close-imbalance signals and a dealer-hedging flow model; Python.
- **Weekend problem.** The market makes its money at night — named result: the share of the cumulative return earned overnight and the last-half-hour predictability with and without hedging flow.
- **Facts to verify.** Cliff, Cooper, Gulen 2008 return differences between trading and non-trading hours (working paper); Lou, Polk, Skouras 2019, A tug of war: overnight versus intraday expected returns (JFE); Baltussen, Da, Lammers, Martens 2021 hedging demand and market intraday momentum (JFE); Nasdaq closing cross documentation (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | O. Bondarenko, D. Muravyev, "Market return around the clock: a puzzle", Journal of Financial and Quantitative Analysis 58(3) (online 2022; issue 2023) 939-967: in E-mini S&P 500 futures traded around the clock, four hours around the European open account for the entire average market return, with a Sharpe ratio of 1.6 that remains high after costs; average returns are a noisy zero in the other twenty hours; VIX futures prices rise overnight and fall around the European open | Crossref metadata; OpenAlex abstract | https://doi.org/10.1017/s0022109022000783 | 2026-09-25 | abstract: "4 hours around European open account for the entire average market return"; "Average returns are a noisy zero during the remaining 20 hours" | hook; section 1; strat:s1:intraday-patterns:overnight; omsources |
| F2 | D. Lou, C. Polk, S. Skouras (2019): as chapter 2, F6 (overnight and intraday continuation with cross-period reversal; reversal and momentum profits earned overnight) | as chapter 2 | https://doi.org/10.1016/j.jfineco.2019.03.011 | 2026-09-25 | as chapter 2 | section 1; strat:s1:intraday-patterns:openreversal; omsources |
| F3 | G. Baltussen, Z. Da, S. Lammers, M. Martens, "Hedging demand and market intraday momentum", Journal of Financial Economics 142(1) (2021) 377-403: hedging short gamma exposure means trading in the direction of price moves, creating momentum; in intraday returns on over 60 futures (equities, bonds, commodities, currencies), 1974-2020, the last 30 minutes' return is positively predicted by the return from the previous close to the last 30 minutes; highly significant; reverts over the next days; linked to gamma hedging by options market makers and leveraged ETFs | the authors' PDF of the published article (abstract) | https://doi.org/10.1016/j.jfineco.2021.04.029 ; https://www3.nd.edu/~zda/intramom.pdf | 2026-09-25 | abstract: "The return during the last 30 minutes before the market close is positively predicted by the return during the rest of the day"; "reverts over the next days"; "links market intraday momentum to the gamma hedging demand from market participants such as market makers of options and leveraged ETFs" | section 3; strat:s1:intraday-patterns:lasthalf; strat:s1:intraday-patterns:hedging; omsources |
| F4 | Nasdaq, "Nasdaq Closing Cross" FAQ (2019 edition): MOC, LOC and imbalance-only orders accepted before 3:50 p.m. ET; from 3:50 p.m. early dissemination of closing information (the Net Order Imbalance Indicator every 10 seconds until 3:55), and on-close orders may no longer be cancelled or modified; at 3:55 p.m. MOC entry stops and the NOII is disseminated every second; LOC orders accepted until 3:58 p.m.; imbalance-only orders until 4:00 p.m.; the closing process begins at 4:00 p.m. | Nasdaq Trader FAQ (PDF) | https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf | 2026-09-25 | "3:50 p.m. ET Early dissemination of closing information begins"; "3:55 p.m. ET ... Nasdaq stops accepting MOC orders"; "3:58 p.m. ET Nasdaq stops accepting entry of LOC orders" | dat:s1:intraday-patterns:nasdaq; section 4 |
| F5 | M. J. Cooper, M. T. Cliff, H. Gulen, "Return differences between trading and non-trading hours: like night and day", SSRN working paper 1004081 (2008) | Crossref metadata | https://doi.org/10.2139/ssrn.1004081 | 2026-09-25 | Crossref: authors, title, year | section 1; omsources |

## EXCLUDED

- Cooper, Cliff and Gulen (2008), content: the SSRN abstract could not be retrieved directly (only through a search summary); cited without quoting results.
- Public daily open and close index data (for a real overnight/intraday split): no licensed free source used; the chapter relies on Bondarenko and Muravyev's published result.
- The current (2026) Nasdaq closing cross timeline: the FAQ fetched is the 2019 edition; the dated box says so.


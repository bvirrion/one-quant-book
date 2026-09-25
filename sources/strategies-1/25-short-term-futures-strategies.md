# 25. Short-Term Futures Strategies — brief and source ledger

## Brief

- **Hook.** On days with a scheduled macro announcement, the S&P futures drift upward in the hours before it; the drift was documented, then partly traded away.
- **Sections.** Intraday mean reversion and momentum; Opening ranges; The pre-announcement drift; Execution at short horizons.
- **Defines.** opening range breakout, pre-announcement drift, intraday mean reversion.
- **Uses (defined earlier).** market impact (B7.18), mark-out curve (B7.23), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** opening range breakout; intraday futures mean reversion; pre-FOMC drift; post-announcement momentum; overnight gap fade.
- **Tutorial.** Simulate futures sessions with firm.tape (a scheduled announcement with a planted pre-drift, opening volatility) and test opening-range, mean-reversion and announcement strategies with the level-2 backtester.
- **Build.** `firm.futintraday`: intraday futures strategy toolkit (opening ranges, gap statistics, announcement windows) on firm.tape and firm.evbt; Python.
- **Weekend problem.** Before the announcement — named result: the pre-announcement drift's Sharpe ratio before and after the planted crowding.
- **Facts to verify.** Lucca and Moench 2015, The pre-FOMC announcement drift (JF); Crabb, Holt, Kirkpatrick 2014 opening range breakout (J. of Trading); Federal Reserve FOMC calendar (dated).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | D. O. Lucca, E. Moench, "The pre-FOMC announcement drift", Journal of Finance 70(1) (2015) 329-371: large average excess returns on US equities in anticipation of monetary policy decisions at scheduled FOMC meetings over the past few decades; the pre-FOMC returns increased over time and account for sizable fractions of total annual realised stock returns; similar in other major international equity indices; no such effect in Treasury securities and money market futures; other major US macroeconomic announcements do not give rise to pre-announcement excess equity returns | Crossref metadata; OpenAlex abstract | https://doi.org/10.1111/jofi.12196 | 2026-09-25 | abstract: "We document large average excess returns on U.S. equities in anticipation of monetary policy decisions made at scheduled meetings of the Federal Open Market Committee"; "Other major U.S. macroeconomic news announcements also do not give rise to preannouncement excess equity returns" | hook; section 3; strat:s1:short-term-futures-strategies:prefomc; omsources |
| F2 | 2026 FOMC meetings: January 27-28, March 17-18*, April 28-29, June 16-17*, July 28-29, September 15-16*, October 27-28, December 8-9* (* with a Summary of Economic Projections) | Board of Governors of the Federal Reserve System, FOMC calendars | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm | 2026-09-25 | the page lists the eight 2026 meetings; the asterisk marks a Summary of Economic Projections meeting | dat:s1:short-term-futures-strategies:fomc; section 3 |

## EXCLUDED

- Crabb, Holt and Kirkpatrick (2014) on the opening range breakout (brief): not found in Crossref under that description; no performance figure for the opening range breakout is cited.
- An SSRN study (2026) reporting that opening-range breakouts do not survive costs: SSRN blocks scripted fetching; not cited.
- The time of day at which FOMC statements are released: the calendar page does not state it; the chapter does not.
- The session model, the planted trend, bounce and pre-announcement drift, and the crowding date are the chapter's own choices.

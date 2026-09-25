# 4. Gamma Scalping and Event Volatility — brief and source ledger

## Brief

- **Hook.** Before earnings a stock's options price a move; the stock then moves more or less. Owning the straddle and hedging it pays the difference between the move priced and the move delivered, less the hedging's cost.
- **Sections.** Gamma scalping as a bet on realised against implied; Implied moves around events; The volatility crush after events; Hedging frequency and path.
- **Defines.** implied move, event straddle, volatility crush.
- **Uses (defined earlier).** gamma scalping (B5.25), event variance (B5.8), cash gamma (B5.4), theta (B5.4), implied volatility (B1.25), realised volatility (B1.25), delta hedging (B1.26), vega (B5.4), backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28).
- **Strategy files.** earnings event straddle; post-event volatility sale; gamma scalping with hedge bands; macro-event variance.
- **Tutorial.** Plant earnings jumps in firm.synthvol's single stocks with an implied event variance that mis-prices them by a controlled amount; trade event straddles and delta-hedged gamma at several hedging frequencies.
- **Build.** `firm.eventvol`: event-variance extraction from term structures, implied moves, event straddles and discrete delta-hedging P&L with bands; Python.
- **Weekend problem.** The move priced and the move delivered — named result: the event straddle's return per event against the implied move's error, and the hedging frequency that maximises it after costs.
- **Facts to verify.** Dubinsky, Johannes, Kaeck, Seeger 2019 option pricing of earnings announcement risks (RFS); Gao, Xing, Zhang 2018 anticipating uncertainty: straddles around earnings announcements (JFQA).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | A. Dubinsky, M. Johannes, A. Kaeck, N. J. Seeger, "Option pricing of earnings announcement risks", Review of Financial Studies 32(2) (2019) 646-687: reduced-form models and estimators separate price uncertainty about earnings announcements from normal day-to-day volatility using option prices; the anticipated price uncertainty is quantitatively large, varies across time and is informative about future return volatility | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/hhy060 | 2026-09-25 | abstract: "separate price uncertainty about earnings announcements from normal day-to-day volatility"; "the anticipated price uncertainty is quantitatively large, varies across time, and is informative about the future return volatility" | section 2; strat:s2:gamma-scalping-and-event-volatility:earnings; omsources |
| F2 | C. Gao, Y. Xing, X. Zhang, "Anticipating uncertainty: straddles around earnings announcements", Journal of Financial and Quantitative Analysis 53(6) (2018) 2587-2617: straddles on individual stocks generally earn negative and significant returns, but average at-the-money straddles from 3 days before an earnings announcement to the announcement date yield a highly significant 3.34% return; returns are larger for smaller firms, higher volatility and kurtosis, more volatile past surprises and less trading volume or higher transaction costs; read as investors underestimating uncertainty around announcements | Crossref metadata; OpenAlex abstract | https://doi.org/10.1017/s0022109018000285 | 2026-09-25 | abstract: "average at-the-money straddles from 3 days before an earnings announcement to the announcement date yield a highly significant 3.34% return" | hook; section 2; strat:s2:gamma-scalping-and-event-volatility:earnings; omsources |
| F3 | Federal Reserve, FOMC meeting calendars: scheduled meetings 2011-2026 with their dates, distinct from unscheduled meetings, cancelled meetings and notation votes | Federal Reserve web pages | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm ; https://www.federalreserve.gov/monetarypolicy/fomchistorical2011.htm (to 2020) | 2026-09-25 | parsed by s2_fetch_fomc.py: 125 scheduled statement days from 26 January 2011 to 16 September 2026 | section 3 |
| F4 | Cboe SPX, VIX and VIX9D daily histories (VIX9D from January 2011) to 22 September 2026, used only through derived statistics | Cboe daily price files | https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv ; VIX_History.csv ; VIX9D_History.csv | 2026-09-25 | files downloaded; statistics recomputed by s2_fetch_fomc.py | section 3 |

## EXCLUDED

- Single-stock option data around earnings: none free; the chapter's event trades are synthetic, and GXZ's 3.34% is quoted as their result, not reproduced.
- Hedging and option costs (2 bps on stock, 2% of premium on options): the chapter's own assumptions.
- Performance of any event-volatility fund or desk: none quoted.


# 23. Seasonality and Calendar Effects — brief and source ledger

## Brief

- **Hook.** Hundreds of calendar effects have been published; a handful survive out of sample, and they are the ones with a reason.
- **Sections.** Commodity seasonality with a physical reason; Turn-of-the-month and holiday effects; Same-month seasonality in stock returns; What survives out of sample.
- **Defines.** calendar effect, turn-of-the-month effect, return seasonality.
- **Uses (defined earlier).** multiple testing (B4.12), deflated Sharpe ratio (B4.12), backtest (B7.16), vectorised backtest (B7.16), information coefficient (B7.6), transaction cost analysis (B7.23), capacity curve (B7.28), fundamental factor model (B7.24).
- **Strategy files.** natural-gas seasonal spread; turn-of-the-month; same-calendar-month seasonality; pre-holiday effect.
- **Tutorial.** Test a hundred calendar rules on firm.synthfut and firm.synthmkt, of which a few are planted with a mechanism, and show which the multiple-testing corrections keep; measure seasonal patterns in the EIA natural-gas and WTI series.
- **Build.** `firm.seasonal`: calendar-rule generator and tester with multiple-testing control, seasonal decomposition of futures curves; Python.
- **Weekend problem.** A handful survive — named result: the planted effects found and the false discoveries at each correction.
- **Facts to verify.** Heston and Sadka 2008, Seasonality in the cross-section of stock returns (JFE); Lakonishok and Smidt 1988 (RFS); Ariel 1987 monthly effect (JFE); Sullivan, Timmermann, White 2001 dangers of data mining: calendar effects (J. Econometrics); EIA natural gas data (as B3).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | S. L. Heston, R. Sadka, "Seasonality in the cross-section of stock returns", Journal of Financial Economics 87(2) (2008) 418-445: stocks with relatively high (low) returns tend to have high (low) returns every year in the same calendar month; the annual pattern at lags of 12, 24 and 36 months is part of a pattern lasting up to 20 annual lags; it explains an economically and statistically significant share of cross-sectional variation in average returns; independent of size, industry, earnings announcements, dividends and fiscal year | Crossref metadata; authors' seminar version (NYU Stern, pdftotext) | https://doi.org/10.1016/j.jfineco.2007.02.003 ; https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/063f-sadka.pdf | 2026-09-25 | abstract: "Stocks with relatively high (low) returns tend to have high (low) returns every year in the same calendar month"; "a general pattern that lasts up to 20 annual lags" | section 3; strat:s1:seasonality-and-calendar-effects:samemonth; omsources |
| F2 | J. Lakonishok, S. Smidt, "Are seasonal anomalies real? A ninety-year perspective", Review of Financial Studies 1(4) (1988) 403-425: 90 years of daily Dow Jones Industrial Average data; evidence of persistently anomalous returns around the turn of the week, the turn of the month, the turn of the year and holidays | Crossref metadata; OpenAlex abstract | https://doi.org/10.1093/rfs/1.4.403 | 2026-09-25 | abstract: "We find evidence of persistently anomalous returns around the turn of the week, around the turn of the month, around the turn of the year, and around holidays" | hook; section 2; strat:s1:seasonality-and-calendar-effects:tom; strat:s1:seasonality-and-calendar-effects:holiday; omsources |
| F3 | R. Sullivan, A. Timmermann, H. White, "Dangers of data mining: the case of calendar effects in stock returns", Journal of Econometrics 105(1) (2001) 249-286: bibliographic record only (title, venue) | Crossref metadata | https://doi.org/10.1016/s0304-4076(01)00077-x | 2026-09-25 | title and venue only | section 4; omsources |
| F4 | Henry Hub natural gas spot price, monthly average, January 2000 to July 2026 (data/markets-3/gas_monthly.csv, column hh) | FRED series MHHNGSP (source: EIA) | https://fred.stlouisfed.org/series/MHHNGSP | 2026-09-24 | data file and its LICENSES.md row (EIA: public domain) | section 1; strat:s1:seasonality-and-calendar-effects:gas |
| F5 | NYMEX WTI crude oil futures daily settlements, contracts 1 and 2 (EIA), 1986-2024, as in chapters 19-21 | US Energy Information Administration, series RCLC1D-RCLC2D | https://www.eia.gov/dnav/pet/hist/RCLC1D.htm | 2026-09-24 | data file and its LICENSES.md row (EIA: public domain) | section 1 |

## EXCLUDED

- R. A. Ariel, "A monthly effect in stock returns", Journal of Financial Economics 18(1) (1987) 161-174 (doi 10.1016/0304-405x(87)90066-3): no abstract fetched (Crossref, OpenAlex and RePEc carry none), so the chapter states nothing from it.
- Sullivan, Timmermann and White's findings (the size of their rule universe, their bootstrap results): no abstract fetched; the chapter cites the paper by its title only.
- Named calendar-effect funds or products: none.
- The planted effects (8 and 15 basis points), the stylised calendar and the seasonal cross-sectional returns are the chapter's own choices.
